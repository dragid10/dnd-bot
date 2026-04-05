import logging
from asyncio import TimeoutError
from datetime import datetime
from subprocess import check_output

import discord
from discord import Embed, ScheduledEvent
from discord.ext import commands, tasks
from discord.ext.commands import Context
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from app import constants, helpers
from app.constants import Emojis, db_config
from app.db.mongo_odm import MongoEngine
from app.db_client import Tracker
from app.helpers import adjacent_days, plist
from app.tasks import BotTasks

logging.basicConfig(level=logging.DEBUG)

# Initialize the bot with hybrid command support (both prefix and slash commands).
# hybrid_command/hybrid_group decorators register commands for both !prefix and /slash usage.
# The command tree is synced in on_ready() so Discord knows about the slash commands.
bot = commands.Bot(
    command_prefix=constants.discord_config.bot_prefix,
    description=constants.discord_config.bot_desc,
    intents=constants.discord_config.bot_intents,
)

# Connect to mongo and create a DB client wrapper
db_client = Tracker(MongoEngine())
start_time = helpers.current_time()


# Events
@bot.event
async def on_ready():
    logging.debug(f"[{start_time}] - Logged in as {bot.user.name} - {bot.user.id}")

    # Sync the command tree with Discord so slash commands are registered/updated
    await bot.tree.sync()

    # Kick off the hourly alert loop that reminds players to RSVP
    await alert_dispatcher.start()


# ======================== Commands ========================
# All commands use @bot.hybrid_command so they work as both
# prefix commands (!status) and slash commands (/status).


@bot.hybrid_command(name="status", description="Status of the bot")
async def status_command(ctx: Context):
    """Reports uptime, git version, current time, and database connectivity."""
    try:
        # Quick ping to verify database connectivity
        MongoClient(db_config.connection_str)["admin"].command("ping")
    except ConnectionFailure as ce:
        db_status = "offline"
        logging.exception(ce)
    else:
        db_status = "online"

    # Include the git short hash so we know what version is deployed
    git = check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()
    now = helpers.current_time()
    await ctx.message.channel.send(
        f"Up for **{now - start_time}** on `{git}`. Time is {datetime.now(constants.eastern_tz).strftime('%T')} eastern. Database is **{db_status}**."
    )


@bot.hybrid_command(name="config", description="Settings for the bot")
async def config_command(ctx: Context):
    """Walks the DM through an interactive setup for the bot. Prompts for the session
    day, first alert day, second alert day (via emoji reactions), and session time (via text).
    """
    # Each question maps a config key to a prompt shown to the user
    questions: list[tuple] = [
        ("session-day", "What day of the week is the session typically had?"),
        ("first-alert", "When would you like to send the first alert?"),
        ("second-alert", "When would you like to send the second alert?"),
    ]

    # Collect day-of-week answers via emoji reactions
    answers = [await ask_for_day(ctx, q) for q in questions]

    # Look up the voice channel ID by name so we can store it in config
    session_vc_id = discord.utils.get(ctx.guild.voice_channels, name=constants.discord_config.voice_channel)
    session_vc_id = session_vc_id.id

    # Convert emoji reactions to their corresponding day-of-week integer values
    mapped_answers = [helpers.emoji_to_day(a) for a in answers]
    bot_config = {questions[i][0]: mapped_answers[i] for i in range(len(mapped_answers))}

    # Collect the session time as a text response (24h HH:MM format)
    bot_config["session-time"] = await ask_for_time(ctx)

    # Persist the full config to the database
    db_client.create_server_config(
        server_id=ctx.guild.id,
        voice_channel_id=session_vc_id,
        dm_username=ctx.author.name,
        dm_id=ctx.author.id,
        session_day=bot_config["session-day"],
        session_time=bot_config["session-time"],
        meeting_room=ctx.message.channel.id,
        first_alert=bot_config["first-alert"],
        second_alert=bot_config["second-alert"],
    )
    await ctx.message.channel.send("Config saved!")


# ======================== Config Helpers ========================
# These helpers are used by the config command to interactively
# collect session day and time from the DM via reactions and text.


async def ask_for_time(ctx: Context):
    """Prompts the user for a session time in 24h HH:MM format via text input."""
    my_message = await ctx.message.channel.send("Configure Session time ET (24h HH:MM):")

    # Only accept a response from the user who invoked the command
    def check(m):
        return ctx.author == m.author

    to_return = None
    try:
        response = await bot.wait_for("message", timeout=90.0, check=check)
    except TimeoutError:
        await ctx.message.channel.send("Please respond faster")
        to_return = None
    else:
        to_return = response.content.strip()
    finally:
        # Clean up the prompt message regardless of outcome
        await my_message.delete()
        return to_return


async def ask_for_day(ctx, ask: tuple):
    """Prompts the user to select a day of the week by reacting with
    a day-of-week emoji (M/T/W/R/F/S/U). Returns the emoji string.
    """
    my_message = await ctx.message.channel.send(f"Configure: {ask[1]}")

    # Add all day-of-week emoji options as reactions
    for emoji in Emojis:
        await my_message.add_reaction(emoji.value)

    # Only accept a valid day emoji from the command invoker
    def check(user_reaction, user):
        return user == ctx.author and any(e.value == str(user_reaction) for e in Emojis)

    to_return = None
    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=120.0, check=check)
    except TimeoutError:
        await ctx.message.channel.send("Fail! React faster!")
        to_return = None
    else:
        to_return = str(reaction)
    finally:
        # Clean up the prompt message regardless of outcome
        await my_message.delete()
        return to_return


# ======================== Server Config Commands ========================


@bot.hybrid_command(name="unconfig", description="Remove bot settings")
async def unconfig_command(ctx: Context):
    """Removes all bot configuration for this server."""
    db_client.rm_server_config(ctx.guild.id)
    await ctx.message.add_reaction("👋")


# ======================== Player Registration Commands ========================


@bot.hybrid_command(name="register", description="Register yourself as a player")
async def register_command(ctx: Context):
    """Adds the calling user to this server's player roster."""
    db_client.register_player(server_id=ctx.guild.id, player_username=ctx.author.name, player_id=ctx.author.id)
    await ctx.message.add_reaction("✅")


@bot.hybrid_command(name="unregister", description="Unregister yourself as a player")
async def unregister_command(ctx: Context):
    """Removes the calling user from this server's player roster."""
    # Verify the player is actually registered before attempting removal
    if not db_client.is_registered_player(ctx.guild.id, ctx.author):
        await ctx.message.reply("You are not currently registered as a player in this campaign.")
        return

    db_client.unregister_player(server_id=ctx.guild.id, player=ctx.author)
    await ctx.message.add_reaction("👋")


@bot.hybrid_command(name="players", description="List of registered players for this session")
async def players_command(ctx: Context):
    """Displays an embed listing all registered players and their Discord IDs."""
    players: list = db_client.get_players(ctx.guild.id)
    if not players:
        await ctx.message.channel.send("No players registered!")
    else:
        player_response = {
            "title": "Registered Players",
            "fields": [{"name": player["name"], "value": f"ID: {player['id']}"} for player in players],
        }
        await ctx.message.channel.send(embed=Embed().from_dict(player_response))


# ======================== Session Management Commands ========================


@bot.hybrid_command(name="cmds", description="List of available commands for the bot")
async def cmds_command(ctx: Context):
    """Lists all registered bot commands."""
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "title": "Available Commands",
                "fields": [{"name": cmd.name, "value": f"`{cmd.name}`"} for cmd in bot.commands],
            }
        )
    )


@bot.hybrid_command(name="reset", description="Reset the RSVP and voting lists")
async def reset_command(ctx: Context):
    """Clears the RSVP (accepted/declined) and cancellation vote lists for this server."""
    db_client.reset(ctx.guild.id)
    await ctx.message.add_reaction("✅")


@bot.hybrid_command(name="alert", description="Force the bot to send an alert")
async def alert_command(ctx: Context):
    """Manually triggers the alert dispatcher, bypassing the hourly schedule."""
    await alert_dispatcher(force=True)


@bot.hybrid_command(
    name="list",
    description="List of players that have accepted, declined, or voted to cancel",
)
async def list_command(ctx: Context):
    """Displays current RSVP status: who accepted, declined, and voted to cancel."""
    accept, decline, cancel = db_client.get_all(ctx.guild.id)
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "title": "Lists",
                "fields": [
                    {"name": "Accepted", "value": plist(accept)},
                    {"name": "Declined", "value": plist(decline)},
                    {"name": "Voted to Cancel", "value": plist(cancel)},
                ],
            }
        )
    )


@bot.hybrid_command(name="cancel", description="Cancel the upcoming session")
async def cancel_command(ctx: Context):
    """Cancels the upcoming session. Only the DM (game master) can run this."""
    server_id = ctx.guild.id
    player_id = ctx.author.id

    # Only the DM (game master) is allowed to cancel sessions
    if not db_client.is_player_dm(server_id, player_id):
        await ctx.message.reply("Sorry this is a DM-only command. Have the DM run this instead")
        return

    was_cancelled = db_client.cancel_session(server_id)
    if was_cancelled:
        await ctx.message.channel.send("The upcoming session has been cancelled!")
    else:
        await ctx.message.reply("Ran into an error cancelling the session. Please try again")


# ======================== RSVP Commands ========================
# hybrid_group creates a command group that supports subcommands
# for both prefix (!rsvp accept) and slash (/rsvp accept) usage.


@bot.hybrid_group(name="rsvp", description="Accept or decline the upcoming session")
async def rsvp_command(ctx: Context):
    """Parent group for RSVP subcommands. Shows usage hint if no subcommand given."""
    if ctx.invoked_subcommand is None:
        await ctx.message.reply(
            f"Please use either `{constants.discord_config.bot_prefix}rsvp accept` or `{constants.discord_config.bot_prefix}rsvp decline`."
        )


@rsvp_command.command(name="accept", description="Accept the upcoming session")
async def _accept(ctx: Context):
    """Marks the player as attending. If all registered players have
    accepted, automatically creates a Discord scheduled event.
    """
    server_id = ctx.guild.id

    # Don't allow RSVPs if the session was already cancelled
    if db_client.is_session_cancelled(server_id):
        await ctx.message.reply("The upcoming session has been cancelled, so no need to RSVP")
        return

    # Only registered players can RSVP
    if not db_client.is_registered_player(server_id, ctx.author):
        await ctx.message.reply("You are not a registered player in this campaign, so you can not rsvp")
        return

    # Record acceptance and remove from decliners if they previously declined
    db_client.add_attendee(server_id, ctx.author)
    db_client.rm_decliner(server_id, ctx.author)

    await ctx.message.reply(
        embed=Embed().from_dict(
            {
                "fields": [
                    {
                        "name": "Accepted",
                        "value": "Thanks for confirming!",
                    },
                    {
                        "name": "Attendees",
                        "value": plist(db_client.get_attendees(server_id)),
                    },
                ]
            }
        )
    )

    # When every registered player has accepted, auto-create a Discord event
    if db_client.is_full_group(server_id):
        sess_event = await _create_session_event(ctx)
        await ctx.message.channel.send(
            f"All players have confirmed attendance, so I've automatically created an event: {sess_event.url}"
        )


@rsvp_command.command(name="decline", description="Decline the upcoming session")
async def _decline(ctx: Context):
    """Marks the player as not attending and removes them from the accepted list."""
    server_id = ctx.guild.id

    # Don't allow RSVPs if the session was already cancelled
    if db_client.is_session_cancelled(server_id):
        await ctx.message.reply("The upcoming session has been cancelled, so no need to RSVP")
        return

    # Only registered players can RSVP
    if not db_client.is_registered_player(server_id, ctx.author):
        await ctx.message.reply("You are not a registered player in this campaign so you can not rsvp")
        return

    # Record the decline and remove from attendees if they previously accepted
    db_client.add_decliner(server_id, ctx.author)
    db_client.rm_attendee(server_id, ctx.author)

    await ctx.message.reply(
        embed=Embed().from_dict(
            {
                "fields": [
                    {"name": "Declined", "value": "No problem, see you next time!"},
                    {
                        "name": "Those that have declined",
                        "value": plist(db_client.get_decliners(server_id)),
                    },
                ]
            }
        )
    )


# ======================== Vote Commands ========================


@bot.hybrid_group(name="vote", description="Vote to cancel the upcoming session")
async def vote_command(ctx: Context):
    """Parent group for vote subcommands. Shows usage hint if no subcommand given."""
    if ctx.invoked_subcommand is None:
        await ctx.message.channel.send(f"Please `{constants.discord_config.bot_prefix}vote cancel`")


@vote_command.command(name="cancel", description="Vote to cancel the upcoming session")
async def _vote_cancel(ctx: Context):
    """Casts the player's vote to cancel the session when there isn't a full group."""
    db_client.add_canceller(ctx.guild.id, ctx.author)
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "fields": [
                    {
                        "name": "Cancelling",
                        "value": "You've voted to cancel this week.",
                    },
                    {
                        "name": "Others that have voted to cancel",
                        "value": plist(db_client.get_cancellers(ctx.guild.id)),
                    },
                ]
            }
        )
    )


# ======================== Internal Helpers ========================


async def _create_session_event(ctx: Context) -> ScheduledEvent:
    """Creates a Discord scheduled voice-channel event for the next session.
    Called automatically when all registered players have accepted.
    Requires the bot to have the manage_events permission on the server.
    """
    server_id = ctx.guild.id
    session_vc_id = db_client.get_voice_channel_id(server_id)
    session_vc = bot.get_channel(session_vc_id)

    # Look up the configured session day/time to calculate the next occurrence
    sess_day, sess_time = db_client.get_campaign_session_dt(server_id)
    next_sess = helpers.get_next_session_day(sess_day, sess_time)

    return await ctx.guild.create_scheduled_event(
        name=f"{constants.dnd_config.campaign_name} Session!",
        description=f"Regular {constants.dnd_config.campaign_alias} session",
        start_time=next_sess,
        channel=session_vc,
        entity_type=discord.EntityType.voice,
        reason="D&D Session",
    )


# ======================== Scheduled Alert Task ========================

bt = BotTasks(bot)


@tasks.loop(hours=1)
async def alert_dispatcher(force=False):
    """Runs every hour to check if it's time to send RSVP reminders.
    Handles first-alert day, second-alert day, session-day DM to the GM,
    and post-session-day cleanup (reset). Can be force-triggered via !alert.
    """
    logging.info("Checking to see if it is time to remind players")

    # Skip if it's not the configured alert hour (unless force-triggered)
    if int(datetime.now(constants.eastern_tz).strftime("%H")) != constants.discord_config.alert_time and force is False:
        logging.debug("It is not yet time to alert")
        return

    logging.debug("It IS time to alert")
    today = datetime.now(constants.eastern_tz).weekday()
    day_before, _ = adjacent_days(today)

    # First alert day: remind unanswered players to RSVP
    for config in db_client.get_first_alert_configs(today):
        server_id = config["guild"]
        if db_client.is_session_cancelled(server_id):
            logging.debug("Next session was cancelled! Won't alert")
            await bt.cancel_alert_msg(config)
            return

        if not db_client.is_full_group(server_id):
            logging.debug("Group is not full")
            unanswered = db_client.get_unanswered_players(server_id)
            await bt.first_alert(config, unanswered)
            return

    # Second alert day: follow-up reminder for anyone who still hasn't responded
    for config in db_client.get_second_alert_configs(today):
        server_id = config["guild"]
        if db_client.is_session_cancelled(server_id):
            logging.debug("Next session was cancelled! Won't alert")
            await bt.cancel_alert_msg(config)
            return

        if not db_client.is_full_group(server_id):
            unanswered = db_client.get_unanswered_players(server_id)
            await bt.second_alert(config, unanswered)
            return

    # Session day: DM the GM with the final accept/decline list
    for config in db_client.get_session_day_configs(today):
        server_id = config["guild"]
        if not db_client.is_session_cancelled(server_id):
            await bt.send_dm(config, db_client)

    # Day after session: reset RSVP lists and the cancel flag for next week
    for config in db_client.get_session_day_configs(day_before):
        bt.reset(config, db_client)


if __name__ == "__main__":
    try:
        bot.run(constants.discord_config.token)
    finally:
        logging.debug("Ending bot")

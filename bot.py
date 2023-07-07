import logging
from asyncio import TimeoutError
from datetime import datetime
from subprocess import check_output

import discord
from discord import Embed, ScheduledEvent, app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Context
from pymongo.errors import ConnectionFailure

from app import constants, helpers
from app.db.mongo_odm import MongoEngine
from app.db_client import Tracker
from app.helpers import Emojis, adjacent_days, plist
from app.tasks import BotTasks

logging.basicConfig(level=logging.DEBUG)

# Load in configs

# Bot init
# tz = timezone('US/Eastern')
# intents = Intents.all()
# intents.members = True
# intents.message_content = True
# description = """A bot to assist with hearding players for D&D sessions."""
bot = commands.Bot(command_prefix=constants.discord_config.bot_prefix,
                   description=constants.discord_config.bot_desc,
                   intents=constants.discord_config.bot_intents)

# Connect to mongo and create a client
db_client = Tracker(MongoEngine())
startTime = helpers.current_time()


# Events
@bot.event
async def on_ready():
    logging.debug(f"[{startTime}] - Logged in as {bot.user.name} - {bot.user.id}")
    await alert_dispatcher.start()


# Commands
@bot.command()
async def status(ctx: Context):
    try:
        # Try a quick ping to make sure things can connect
        mongo_client["admin"].command("ping")
    except ConnectionFailure as ce:
        db_status = "offline"
        logging.exception(ce)
    else:
        db_status = "online"

    # Get git commit hash, so we know what version of the bot we're running
    git = check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()
    now = helpers.current_time()
    await ctx.message.channel.send(
        f"Up for **{now - startTime}** on `{git}`. Time is {datetime.now(constants.eastern_tz).strftime('%T')} eastern. Database is **{db_status}**."
    )


@bot.command()
async def config(ctx: Context):
    """ Starts the config of the bot. Goes through asking the session day, when to send the first alert, and when to send the second alert.

    :param ctx: Context of the discord bot
    :return:
    """
    questions: list[tuple] = [("session-day", "What day of the week is the session typically had?"),
                              ("first-alert", "When would you like to send the first alert?"),
                              ("second-alert", "When would you like to send the second alert?")]
    answers = [await ask_for_day(ctx, q) for q in questions]
    session_vc_id = discord.utils.get(ctx.guild.voice_channels, name=constants.discord_config.voice_channel)
    session_vc_id = session_vc_id.id

    # Whatever emoji is clicked in discord, will be mapped to a day of the week str
    mapped_answers = [helpers.emoji_to_day(a) for a in answers]
    bot_config = {
        questions[i][0]: mapped_answers[i]
        for i in range(len(mapped_answers))
    }
    bot_config["session-time"] = await ask_for_time(ctx)
    db_client.create_guild_config(
        guild_id=ctx.guild.id,
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


async def ask_for_time(ctx: Context):
    my_message = await ctx.message.channel.send("Configure Session time ET (24h HH:MM):")

    def check(m):
        return ctx.author == m.author

    try:
        response = await bot.wait_for("message", timeout=60.0, check=check)
    except TimeoutError:
        await ctx.message.channel.send("Fail! React faster!")
        to_return = None
    else:
        to_return = response.content.strip()
    finally:
        await my_message.delete()
        return to_return


async def ask_for_day(ctx, ask: tuple):
    my_message = await ctx.message.channel.send(f"Configure: {ask[1]}")
    for emoji in Emojis:
        await my_message.add_reaction(emoji.value)

    def check(reaction, user):
        return user == ctx.author and any(e.value == str(reaction) for e in Emojis)

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=20.0, check=check)
    except TimeoutError:
        await ctx.message.channel.send("Fail! React faster!")
        to_return = None
    else:
        to_return = str(reaction)
    finally:
        await my_message.delete()
        return to_return


@bot.command()
async def unconfig(ctx: Context):
    db_client.rm_guild_config(ctx.guild.id)
    await ctx.message.add_reaction("👋")


@bot.command()
async def register(ctx: Context):
    db_client.register_player(guild_id=ctx.guild.id, dm_username=ctx.author.name, dm_id=ctx.author.id)
    await ctx.message.add_reaction("✅")


@bot.command()
async def players(ctx: Context):
    players: list = db_client.get_players_for_guild(ctx.guild.id)
    if not players:
        await ctx.message.channel.send("No players registered!")
    else:
        player_response = {
            "title": "Registered Players",
            "fields": [
                {"name": player["name"], "value": f"ID: {player['id']}"}
                for player in players
            ],
        }
        await ctx.message.channel.send(embed=Embed().from_dict(player_response))


@bot.command()
async def cmds(ctx: Context):
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "title": "Available Commands",
                "fields": [{"name": cmd.name, "value": f"`{cmd.name}`"} for cmd in bot.commands],
            }
        )
    )


@bot.command()
async def reset(ctx: Context):
    db_client.reset(ctx.guild.id)
    await ctx.message.add_reaction("✅")


@bot.command()
async def alert(ctx: Context):
    await alert_dispatcher(force=True)


@bot.command()
async def skip(ctx: Context):
    db_client.skip(ctx.guild.id)
    await ctx.message.channel.send("Skipping this week!")


@bot.command()
async def list(ctx: Context):
    accept, decline, cancel = db_client.get_all(ctx.guild.id)
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "title": "Lists",
                "fields": [
                    {"name": "Accepted", "value": plist(accept)},
                    {"name": "Declined", "value": plist(decline)},
                    {"name": "Cancelled", "value": plist(cancel)},
                ],
            }
        )
    )


@bot.command()
async def cancel(ctx: Context):
    guild_id = ctx.guild.id
    player_id = ctx.author.id

    # If player calling command isn't DM, then tell them so and return
    if not db_client.is_player_dm(guild_id, player_id):
        await ctx.message.reply(f"Sorry this is a DM-only command. Have the DM run this instead")
        return

    was_cancelled = db_client.cancel_session(guild_id)
    if was_cancelled:
        await ctx.message.channel.send("The upcoming session has been cancelled!")
    else:
        await ctx.message.reply("Ran into an error cancelling the session. Please try again")


# Support rsvp [accept|decline]
@bot.group()
async def rsvp(ctx: Context):
    if ctx.invoked_subcommand is None:
        await ctx.message.reply(
            f"Please use either `{constants.discord_config.bot_prefix}rsvp accept` or `{constants.discord_config.bot_prefix}rsvp decline`."
        )


@rsvp.command(name="accept")
async def _accept(ctx: Context):
    guild_id = ctx.guild.id
    if db_client.is_session_cancelled(guild_id):
        await ctx.message.reply(f"The upcoming session has been cancelled, so no need to RSVP")
        return

    if not db_client.is_registered_player(ctx.guild.id, ctx.author):
        await ctx.message.reply(f"You are not a registered player in this campaign, so you can not rsvp")
    else:
        db_client.add_attendee_for_guild(ctx.guild.id, ctx.author)
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
                            "value": plist(db_client.get_attendees_for_guild(ctx.guild.id)),
                        },
                    ]
                }
            )
        )
        db_client.rm_decliner_for_guild(ctx.guild.id, ctx.author)

    if db_client.is_full_group(ctx.guild.id):
        sess_event = await _create_session_event(ctx)
        await ctx.message.channel.send(
            f"All players have confirmed attendance, so I've automatically created an event: {sess_event.url}"
        )


@rsvp.command(name="decline")
async def _decline(ctx: Context):
    guild_id = ctx.guild.id
    if db_client.is_session_cancelled(guild_id):
        await ctx.message.reply(f"The upcoming session has been cancelled, so no need to RSVP")
        return

    if not db_client.is_registered_player(ctx.guild.id, ctx.author):
        await ctx.message.reply(f"You are not a registered player in this campaign so you can not rsvp")
    else:
        db_client.add_decliner_for_guild(ctx.guild.id, ctx.author)
        await ctx.message.reply(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {"name": "Declined", "value": "No problem, see you next time!"},
                        {
                            "name": "Those that have declined",
                            "value": plist(db_client.get_decliners_for_guild(ctx.guild.id)),
                        },
                    ]
                }
            )
        )
        db_client.rm_attendee_for_guild(ctx.guild.id, ctx.author)


# Support vote [cancel]
@bot.group()
async def vote(ctx: Context):
    if ctx.invoked_subcommand is None:
        await ctx.message.channel.send(
            f"Please `{constants.discord_config.bot_prefix}vote cancel`"
        )


@vote.command(name="cancel")
async def _vote_cancel(ctx: Context):
    db_client.add_canceller_for_guild(ctx.guild.id, ctx.author)
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "fields": [
                    {
                        "name": "Cancelling",
                        "value": "You've voted to cancel this week.",
                    },
                    {
                        "name": "Others that have cancelled",
                        "value": plist(db_client.get_cancellers_for_guild(ctx.guild.id)),
                    },
                ]
            }
        )
    )


@app_commands.checks.bot_has_permissions(manage_events=True)
async def _create_session_event(ctx: Context) -> ScheduledEvent:
    server_id = ctx.guild.id
    session_vc_id = db_client.get_voice_channel_id(server_id)
    session_vc = bot.get_channel(session_vc_id)
    # Get details about session in order to create a discord event
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


bt = BotTasks(bot)


@tasks.loop(hours=1)
async def alert_dispatcher(force=False):
    logging.info(f"Checking to see if it is time to remind players")
    logging.debug(f"Logging into Discord")
    await bot.login(constants.discord_config.token)

    # See if it's time to send message asking if players are available
    if int(datetime.now(constants.eastern_tz).strftime("%H")) != constants.discord_config.alert_time and force is False:
        logging.debug(f"It is not yet time to alert")
        return

    logging.debug(f"It IS time to alert")
    today = datetime.now(constants.eastern_tz).weekday()
    day_before, _ = adjacent_days(today)

    # Check if all players have registered for the upcoming session (on the first day)
    for config in db_client.get_first_alert_configs(today):
        guild_id = config["guild"]
        if db_client.is_session_cancelled(guild_id):
            logging.debug(f"Next session was cancelled! Won't alert")
            await bt.cancel_alert_msg(config)
            return

        if not db_client.is_full_group(guild_id):
            logging.debug("Group is not full")
            unanswered = db_client.get_unanswered_players(guild_id=config["guild"])
            await bt.first_alert(config, unanswered)
            return
    # Check if all players have registered for the upcoming session (but on the second day)
    for config in db_client.get_second_alert_configs(today):
        guild_id = config["guild"]
        if db_client.is_session_cancelled(guild_id):
            logging.debug(f"Next session was cancelled! Won't alert")
            await bt.cancel_alert_msg(config)
            return

        if not db_client.is_full_group(config["guild"]):
            unanswered = db_client.get_unanswered_players(guild_id=config["guild"])
            await bt.second_alert(config, unanswered)
            return

    # DM the GM the accept/reject rsvp list
    for config in db_client.get_session_day_configs(today):
        guild_id = config["guild"]
        if not db_client.is_session_cancelled(guild_id):
            await bt.send_dm(config, db_client)

    # Reset rsvp list and session cancel flag
    for config in db_client.get_session_day_configs(day_before):
        bt.reset(config, db_client)


if __name__ == "__main__":
    try:
        bot.run(constants.discord_config.token)
    finally:
        logging.debug("Ending bot")

[![Prod Deploy](https://github.com/dragid10/dnd-bot/actions/workflows/deploy.yml/badge.svg)](https://github.com/dragid10/dnd-bot/actions/workflows/deploy.yml)
# Discord D&D Gathering Bot

Bot to help you heard your players.
https://discord.com/api/oauth2/authorize?client_id=966865214937112657&permissions=544119192688&scope=applications.commands%20bot

## Commands

All commands must be prefixed (e.g. `!ping`). The prefix is determined by the [server-side config](#config).

- `status`: How long the bot has been running, what `git` hash is running, and the status of the database connection. This command may take some time to return if the database is unavailable.
- `config`: Walks the DM through configuring the bot.
- `commands`: Lists all available commands.
- `reset`: Resets the RSVP and voting lists.
- `rsvp [accept|decline]`: `accept` or `decline` the invitation to the session.
- `vote [cancel]`: Cast your vote for `cancelling`
  the session when you do not have a full group of players.
- `skip`: "Skips" the current week; disables alerting.
- `list`: Displays the RSVP and voting lists.
- `inv [add|remove|update]`: Alone, `inv` will dispay the caller's inventory. Paired with `add`, `remove`, or `update` will add, remove, or update quantities of items respectively.
  - `inv add QTY:ITEM_NAME, QTY:ITEM_NAME, [...]`: Add multiple items in quantity:name pairs.
  - `inv remove ITEM_NAME`: Removes item `ITEM_NAME` from inventory. Note, this does not _use_ (decrement quantity) an item, but removes it completely.
  - `inv update QTY:ITEM_NAME, QTY:ITEM_NAME, [...]`: Update the quantities of multiple items.
- `register`: Registers player to their specific guild to be counted as a member of the game. This helps manage the count for messages/reminders pushed to the server channel.
- `unregister`: Unregisters player from the game.
- `players`: Displays list of current registered players with their username and unique ID.


## Config

<!-- TODO: Update with latest configs -->
Server-side configuration is done via a config file. Copy `.env-sample` to `.env` and fill in the details.

```dotenv
### Deployment
GH_REPO_TOKEN=ghp_FakeToken
DOCKERHUB_USERNAME=FakeUsername
DOCKERHUB_TOKEN=dckr_pat_FakeToken
FLY_API_TOKEN=FakeToken

### Discord Vars
# Prod
discordToken=FakeToken
botPrefix=!
botDescr='A bot to assist with hearding players for D&D sessions.'
alertTime=12 # 24h format
discordVC=VoiceChannelName # Without the leading '#'

### MongoDB Vars
dbHost=mongodb.host
dbPort=27017
dbUser=FakeUser
dbPassword=FakePassword
dbName=dnd-bot

### D&D vars
campaignName='Campaign Name'
campaignAlias=ACRONYM
```

> Note: This can all be done with environment variables instead. In the absence of a config file, the bot will fall 
> back to using environment variables.


## Discord Config

After inviting the bot, the DM should use the `config` command in the "meeting hall" channel (i.e. the channel you wish 
to receive alerts and keep track of players).

- session day: Day of the session.
- session time: Time of the session in 24h, HH:MM format.
- first alert: First _alert_ from the bot reminding players to RSVP.
- second alert: Second RSVP reminder.

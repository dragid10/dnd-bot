import urllib.parse
from dataclasses import dataclass, field

from decouple import config
from discord import Intents
from pytz import timezone


# ======== Discord ========
def declare_intents():
    intents = Intents.all()
    intents.members = True
    intents.message_content = True
    return intents


@dataclass
class DiscordConfig:
    token: str
    bot_prefix: str
    bot_desc: str
    alert_time: int
    voice_channel: str
    bot_intents: Intents = field(default_factory=declare_intents)


# Read in env vars to make sure they exist
__token = config("discordToken")
__bot_prefix = config("botPrefix", default="!")
__bot_descr = config("botDescr", default="A bot to assist with hearding players for D&D sessions.")
__alert_time = config("alertTime", default="12", cast=int)
__discord_vc = config("discordVC")

# Create discord config dataclass
discord_config = DiscordConfig(__token, __bot_prefix, __bot_descr, __alert_time, __discord_vc)


# ======== Database ========
@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    db_name: str


__db_host = config("dbHost")
__db_port = config("dbPort", cast=int)
__db_user = config("dbUser")
__db_password = config("dbPassword")
__db_name = config("dbName", default="dnd-bot")

# Create db config dataclass
db_config = DatabaseConfig(__db_host, __db_port, __db_user, __db_password, __db_name)

# give db config a connection str attribute
db_config.connection_str = f"mongodb+srv://{urllib.parse.quote(db_config.user)}:{urllib.parse.quote(db_config.password)}@{db_config.host}"


# ======== D&D ========
@dataclass
class DndConfig:
    campaign_name: str
    campaign_alias: str


__campaign_name = config("campaignName", default="D&D")
__campaign_alias = config("campaignAlias", default=__campaign_name)

# Create d&d config dataclass
dnd_config = DndConfig(__campaign_name, __campaign_alias)

# ======== Common ========
eastern_tz = timezone('US/Eastern')

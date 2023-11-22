import urllib.parse
from dataclasses import dataclass, field
from enum import Enum, unique
from io import StringIO

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
def __create_connect_str(
    username: str, password: str, host: str, database: str, port: int = 27017, dialect: str = "mongodb", **kwargs
):
    # start a string builder, so we can put the connection uri together more easily
    conn_str = StringIO()

    # If srv in the dialect, then we can't include the port number
    is_srv = "srv" in dialect.casefold()
    username = urllib.parse.quote(username)
    password = urllib.parse.quote(password)
    options = {**kwargs}

    # Start building connection string: `mongodb[+srv]://{username}:{password}@{host}[:{port}]/{database}[?{options}]`

    conn_str.write(dialect)
    conn_str.write("://")
    conn_str.write(username)
    conn_str.write(":")
    conn_str.write(password)
    conn_str.write("@")
    conn_str.write(host)
    if not is_srv:
        conn_str.write(":")
        conn_str.write(str(port))
    conn_str.write("/")
    conn_str.write(database)

    # If no options, then create str
    if not options:
        return conn_str.getvalue()

    # Write any db options
    conn_str.write("?")
    for k, v in options.items():
        conn_str.write(f"{k}={v}")
        conn_str.write("&")

    return conn_str.getvalue().strip(" ,&?")


@unique
class Collections(str, Enum):
    ATTENDEES = "attendees"
    DECLINERS = "decliners"
    CANCELLERS = "cancellers"
    INVENTORIES = "inventories"
    CONFIG = "config"
    PLAYERS = "players"
    CANCEL_SESSION = "cancel-session"


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    db_name: str
    connection_str: str = ""


# Connection vars
__db_host = config("dbHost")
__db_port = config("dbPort", cast=int)
__db_user = config("dbUser")
__db_password = config("dbPassword")
__db_name = config("dbName", default="dnd-bot")
__db_dialect = "mongodb+srv"
__db_options = {"retrywrites": "true", "w": "majority"}

# Create db config dataclass
db_config = DatabaseConfig(__db_host, __db_port, __db_user, __db_password, __db_name)

# give db config a connection str attribute
db_config.connection_str = __create_connect_str(
    username=__db_user,
    password=__db_password,
    host=__db_host,
    port=__db_port,
    database=__db_name,
    dialect=__db_dialect,
    **__db_options,
)


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
eastern_tz = timezone("US/Eastern")


@unique
class Weekdays(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@unique
class Emojis(str, Enum):
    MONDAY = "🇲"
    TUESDAY = "🇹"
    WEDNESDAY = "🇼"
    THURSDAY = "🇷"
    FRIDAY = "🇫"
    SATURDAY = "🇸"
    SUNDAY = "🇺"

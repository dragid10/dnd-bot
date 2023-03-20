import datetime
import glob
import os

import discord.ext.commands as commands
import discord.ext.test as dpytest
import pytest_asyncio
from discord import Intents
from pytz import timezone


@pytest_asyncio.fixture
async def bot():
    try:
        import configparser

        # Load config
        bot_config = configparser.ConfigParser()
        bot_config.read("config.ini")
        token = bot_config["secrets"]["token"]
        bot_prefix = bot_config["discord"]["botPrefix"]
        db_host = bot_config["db"]["host"]
        db_port = int(bot_config["db"]["port"])
        db_user = bot_config["db"]["user"]
        db_password = bot_config["db"]["password"]
        alert_time = int(bot_config["alerts"]["time"])
        campaign_name = bot_config["campaign"]["name"] or "D&D"
        campaign_alias = bot_config["campaign"]["alias"] or campaign_name
        discord_vc = bot_config["discord"]["vc"]
    except KeyError:
        # Fall back to environment variables
        from os import environ

        from decouple import config

        token = config("token")
        bot_prefix = config("botPrefix", default="!")
        db_host = config("dbHost")
        db_port = config("dbPort", cast=int)
        db_user = config("dbUser")
        db_password = config("dbPassword")
        alert_time = config("alertTime", default="12", cast=int)
        campaign_name = config("campaignName", default="D&D")
        campaign_alias = config("campaignAlias", default=campaign_name)
        discord_vc = config("discordVC")

    intents = Intents.all()
    intents.members = True
    intents.message_content = True
    description = """A bot to assist with hearding players for D&D sessions."""
    bot = commands.Bot(command_prefix=bot_prefix,
                       description=description,
                       intents=intents)
    await bot._async_setup_hook()
    dpytest.configure(bot)
    return bot


@pytest_asyncio.fixture
def est_tz() -> datetime.tzinfo:
    return timezone("America/New_York")


@pytest_asyncio.fixture(autouse=True)
async def cleanup():
    yield
    await dpytest.empty_queue()


def pytest_sessionfinish(session, exitstatus):
    """Code to execute after all tests."""

    # dat files are created when using attachements
    print("\n-------------------------\nClean dpytest_*.dat files")
    fileList = glob.glob("./dpytest_*.dat")
    for filePath in fileList:
        try:
            os.remove(filePath)
        except Exception:
            print("Error while deleting file : ", filePath)

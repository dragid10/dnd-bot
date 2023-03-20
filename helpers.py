from datetime import datetime
from enum import Enum
from enum import unique
from typing import List
from typing import Tuple

from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import weekdays
from pytz import timezone

est_tz = timezone("America/New_York")


@unique
class Collections(str, Enum):
    ATTENDEES = "attendees"
    DECLINERS = "decliners"
    CANCELLERS = "cancellers"
    INVENTORIES = "inventories"
    CONFIG = "config"
    PLAYERS = "players"
    CANCEL_SESSION = "cancel-session"


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
    WENDESAY = "🇼"
    THURSDAY = "🇷"
    FRIDAY = "🇫"
    SATURDAY = "🇸"
    SUNDAY = "🇺"


def plist(inlist: List) -> str:
    """
    Turn list of player names into comma-separated list

    :param inlist: List of player objects
    :return: comma-separated list of player names
    """
    if len(inlist) > 0:
        return ", ".join([u["name"] for u in inlist])
    else:
        return "None"


def adjacent_days(dotw: int) -> Tuple[int, int]:
    """
    Given an index representing the day of the week, get the adjacent days of the week.

    >>> adjacent_days(1)
    (0, 2)

    :param dotw: Day of the week represented as an integer
    :type dotw: int
    :return: Tuple containing the 2 surrounding days of the week represented as integers
    """
    if dotw < 0 or dotw > 6:
        raise ValueError(
            f"{dotw} is not a valid index of a weekday. Valid values are 0..6"
        )
    days = [i for i in range(len(Weekdays))]
    before = days[(dotw - 1) % len(days)]
    after = days[(dotw + 1) % len(days)]
    return int(before), int(after)


def get_next_session_day(session_day: int, session_time: str) -> datetime:
    """
    Determine the next session day for a campaign

    Usage:
    >>> get_next_session_day(0, "11:00")

    :param session_day: Integer representation of session day of the week (Mon = 0, Sun = 6)
    :type session_day: int
    :param session_time: 24hr representation of session time (e.g. 01:00pm == 13:00)
    :type session_time: str
    :return: Datetime object of next session day and time
    """
    session_hr = int(session_time.split(":")[0])
    session_min = int(session_time.split(":")[1])

    # If session day is less than 0 or greater than 6, its invalid
    if session_day < 0 or session_day > 6:
        raise ValueError(
            f"{session_day} is not a valid index of a weekday. Valid values are 0..6"
        )

    # If session hour is less than 0 or greater than 24, its invalid
    if session_hr < 0 or session_hr > 23:
        raise ValueError(f"{session_hr} is not a valid hour. Valid values are 00..23")

    # If session min is less than 0 or greater than 59, its invalid
    if session_min < 0 or session_min > 59:
        raise ValueError(
            f"{session_min} is not a valid minute. Valid values are 00..59"
        )

    # Get current DT and localize it to EST
    est_dt = est_tz.localize(datetime.utcnow().replace(second=0, microsecond=0))

    ret_sess_day = (est_dt + relativedelta(weekday=weekdays[session_day](1))).replace(
        hour=session_hr, minute=session_min
    )
    return ret_sess_day


def callable_username(username: str):
    """
    Turn a Discord username into a callable version of itself so that the corresponding user can be notified in Discord

    >>> callable_username("test")
    <@test>
    :param username:
    :return:
    """
    if str_null_empty(username):
        raise ValueError("A valid username was not passed in!")
    return f"<@{username}>".strip()


def str_null_empty(input_str: str) -> bool:
    """
    Check if string is null or empty

    :param input_str: str to check if its null or empty
    :return: True is string is null or empty, False otherwise
    """
    if input_str is None:
        return True

    if not isinstance(input_str, str):
        raise ValueError(f"{input_str} is not a str!")

    input_str = input_str.casefold().strip()
    if input_str == "":
        return True
    return False

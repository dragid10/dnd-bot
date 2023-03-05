from datetime import datetime, timedelta
from enum import Enum, unique
from typing import List, Tuple

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
    WENDESAY = 2
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
    if len(inlist) > 0:
        return ", ".join([u["name"] for u in inlist])
    else:
        return "None"


def adjacent_days(dotw: int) -> Tuple[int, int]:
    if dotw < 0 or dotw > 6:
        raise ValueError
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

    # If session day is greater than 6, its invalid
    if session_day > 6:
        raise ValueError(f"{session_day} is not a valid index of a weekday. Valid values are 0..6")

    # If session hour is greater than 24, its invalid
    if session_hr > 24:
        raise ValueError(f"{session_hr} is not a valid time. Valid values are 00..24")

    # If session min is greater than 24, its invalid
    if session_min > 24:
        raise ValueError(f"{session_min} is not a valid time. Valid values are 00..59")

    # Get current DT and localize it to EST
    est_dt = datetime.utcnow().replace(second=0, microsecond=0).astimezone(est_tz)

    # Figure out next session date with time deltas
    # TODO (3/5/23) [dragid10]: Repplace with dateutils.relativedelta
    # TODO EX: `curr_date + relativedelta(weekday=weekdays[SESSION_DAY](1))`
    for i in range(1, 8):
        ret_sess_day = datetime.utcnow().replace(second=0, microsecond=0).astimezone(est_tz)
        potential_day: datetime = est_dt + timedelta(days=i)
        potential_day_dotw = potential_day.weekday()

        if potential_day_dotw == session_day:
            ret_sess_day = potential_day.replace(
                hour=int(session_time.split(":")[0]),
                minute=int(session_time.split(":")[1]))
            return ret_sess_day


def callable_username(username: str):
    return f"<@{username}>".strip()

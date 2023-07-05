from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Tuple

from mongoengine import QuerySet
from mongoengine.base import BaseDocument
from mongoengine.queryset.base import BaseQuerySet

from app import constants
from app.constants import Emojis, Weekdays


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


def get_next_session_day(session_day, session_time) -> datetime:
    # Get current DT and localize it to EST
    est_dt = datetime.utcnow().astimezone(constants.eastern_tz)

    # Figure out next session date with time deltas
    for i in range(1, 8):
        ret_sess_day = datetime.utcnow().astimezone(constants.eastern_tz)
        potential_day: datetime = est_dt + timedelta(days=i)
        potential_day_dotw = potential_day.weekday()

        if potential_day_dotw == session_day:
            ret_sess_day = potential_day.replace(
                hour=int(session_time.split(":")[0]),
                minute=int(session_time.split(":")[1]),
            )
        return ret_sess_day


def callable_username(username: str):
    return f"<@{username}>".strip()


def current_time() -> datetime:
    time = datetime.now(constants.eastern_tz).replace(microsecond=0)
    return time


def _doc_to_dict(doc: BaseDocument) -> dict:
    return doc.to_mongo().to_dict()


def doc_to_dict(result: [BaseDocument | QuerySet]) -> dict | list[dict]:
    """ Converts a Mongo Document object to a python dictionary

    :param result: (BaseDocument | QuerySet): the BaseDocument or QuerySet object from the database
    :return: (dict | list[dict]) A dictionary (or list of dictionaries) representation of the mongo documents
    """

    # Default value of the return
    res = dict()

    # If the arg is null or an empty list, then just return default value
    if not result:
        # res = dict()
        pass

    # If the arg is a Document then convert it to a dict
    if isinstance(result, BaseDocument):
        res = _doc_to_dict(result)

    # If the arg is a list, then convert each item to a dict
    if isinstance(result, BaseQuerySet):
        res = []
        for row in result:
            dict_row = _doc_to_dict(row)
            res.append(dict_row)
    return res


def emoji_to_day(emoji: str) -> str:
    # Default value will be monday
    ret = Emojis.MONDAY.value
    for e in Emojis:
        if e.value == emoji:
            ret = Weekdays[e.name].value
    return ret

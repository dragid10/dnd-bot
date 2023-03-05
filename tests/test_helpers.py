import datetime

from dateutil.relativedelta import relativedelta, weekdays

import helpers


def test_plist():
    assert False


def test_adjacent_days():
    assert False


def test_get_next_session_day(est_tz):
    SESSION_DAY = 0
    SESSION_TIME = "11:00"

    session_hr = int(SESSION_TIME.split(":")[0])
    session_min = int(SESSION_TIME.split(":")[1])
    curr_date = datetime.datetime.today().replace(hour=session_hr, minute=session_min, second=0, microsecond=0)

    # Use the weekdays tuple from dateutil to get the `monday` object and find the next nth (1) monday from now
    EXPECTED_DATE = est_tz.localize(curr_date + relativedelta(weekday=weekdays[SESSION_DAY](1)))
    ACTUAL_DATE = helpers.get_next_session_day(SESSION_DAY, SESSION_TIME)
    assert EXPECTED_DATE == ACTUAL_DATE


def test_callable_username():
    assert False


def test_weekdays():
    assert False


def test_emojis():
    assert False

import datetime

import pytest
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import weekdays

import helpers


def test_valid_plist():
    player_list = [
        {
            "name": "test"
        },
        {
            "name": "cheese"
        },
        {
            "name": "junior"
        },
        {
            "name": "pal_friend"
        },
    ]
    EXPECTED_PLIST = "test, cheese, junior, pal_friend"
    ACTUAL_PLIST = helpers.plist(player_list)

    assert EXPECTED_PLIST == ACTUAL_PLIST


def test_valid_empty_plist():
    player_list = []
    EXPECTED_PLIST = "None"
    ACTUAL_PLIST = helpers.plist(player_list)

    assert EXPECTED_PLIST == ACTUAL_PLIST


@pytest.mark.parametrize(
    "dotw_index, EXPECTED_ADJACENT_DAY",
    [
        (0, (6, 1)),
        (1, (0, 2)),
        (2, (1, 3)),
        (3, (2, 4)),
        (4, (3, 5)),
        (5, (4, 6)),
        (6, (5, 0)),
    ],
)
def test_valid_adjacent_days(dotw_index: int,
                             EXPECTED_ADJACENT_DAY: tuple[int, int]):
    ACTUAL_ADJACENT_DAY: tuple[int, int] = helpers.adjacent_days(dotw_index)
    assert EXPECTED_ADJACENT_DAY == ACTUAL_ADJACENT_DAY


@pytest.mark.parametrize("dotw_index", [-1, -2, 8, 9])
def test_invalid_adjacent_days(dotw_index: int):
    with pytest.raises(ValueError) as invalid_dotw:
        EXPECTED_ADJACENT_DAY = None
        ACTUAL_ADJACENT_DAY: tuple[int,
                                   int] = helpers.adjacent_days(dotw_index)
    assert "not a valid index of a weekday" in str(invalid_dotw.value)


def test_valid_get_next_session_day(est_tz):
    SESSION_DAY = 0
    SESSION_TIME = "11:30"

    session_hr = int(SESSION_TIME.split(":")[0])
    session_min = int(SESSION_TIME.split(":")[1])
    curr_date = est_tz.localize(datetime.datetime.today().replace(
        hour=session_hr, minute=session_min, second=0, microsecond=0))

    # Use the weekdays tuple from dateutil to get the `monday` object and find the next nth (1) monday from now
    EXPECTED_DATE = curr_date + relativedelta(weekday=weekdays[SESSION_DAY](1))
    ACTUAL_DATE = helpers.get_next_session_day(SESSION_DAY, SESSION_TIME)
    assert EXPECTED_DATE == ACTUAL_DATE


def test_invalid_dotw_get_next_session_day(est_tz):
    SESSION_DAY = 9
    SESSION_TIME = "11:00"

    session_hr = int(SESSION_TIME.split(":")[0])
    session_min = int(SESSION_TIME.split(":")[1])
    curr_date = datetime.datetime.today().replace(hour=session_hr,
                                                  minute=session_min,
                                                  second=0,
                                                  microsecond=0)

    try:
        # Use the weekdays tuple from dateutil to get the `monday` object and find the next nth (1) monday from now
        # This test won't get past this line when invalid, so we ignore its value anyway
        EXPECTED_DATE = (
            est_tz.localize(curr_date +
                            relativedelta(weekday=weekdays[SESSION_DAY](1)))
            or None)
    except:
        EXPECTED_DATE = None

    with pytest.raises(ValueError) as invalid_dotw:
        ACTUAL_DATE = helpers.get_next_session_day(SESSION_DAY, SESSION_TIME)
    assert "not a valid index of a weekday" in str(invalid_dotw.value)


@pytest.mark.parametrize("SESSION_TIME",
                         ["31:00", "-31:00", "60:30", "-100:49"])
def test_invalid_session_hour_get_next_session_day(est_tz, SESSION_TIME: str):
    SESSION_DAY = 1
    session_hr = int(SESSION_TIME.split(":")[0])
    session_min = int(SESSION_TIME.split(":")[1])

    with pytest.raises(ValueError) as invalid_dotw:
        try:
            curr_date = datetime.datetime.today().replace(hour=session_hr,
                                                          minute=session_min,
                                                          second=0,
                                                          microsecond=0)

            # Use the weekdays tuple from dateutil to get the `monday` object and find the next nth (1) monday from now
            # This test won't get past this line when invalid, so we ignore its value anyway
            EXPECTED_DATE = (est_tz.localize(curr_date + relativedelta(
                weekday=weekdays[SESSION_DAY](1))) or None)
        except:
            EXPECTED_DATE = None

        ACTUAL_DATE = helpers.get_next_session_day(SESSION_DAY, SESSION_TIME)
    assert "not a valid hour" in str(invalid_dotw.value)


@pytest.mark.parametrize("SESSION_TIME",
                         ["11:90", "11:-01", "06:-30", "10:69"])
def test_invalid_session_min_get_next_session_day(est_tz, SESSION_TIME: str):
    SESSION_DAY = 1

    session_hr = int(SESSION_TIME.split(":")[0])
    session_min = int(SESSION_TIME.split(":")[1])

    with pytest.raises(ValueError) as invalid_dotw:
        try:
            curr_date = datetime.datetime.today().replace(hour=session_hr,
                                                          minute=session_min,
                                                          second=0,
                                                          microsecond=0)

            # Use the weekdays tuple from dateutil to get the `monday` object and find the next nth (1) monday from now
            # This test won't get past this line when invalid, so we ignore its value anyway
            EXPECTED_DATE = (est_tz.localize(curr_date + relativedelta(
                weekday=weekdays[SESSION_DAY](1))) or None)
        except:
            EXPECTED_DATE = None

        ACTUAL_DATE = helpers.get_next_session_day(SESSION_DAY, SESSION_TIME)
    assert "not a valid minute" in str(invalid_dotw.value)


@pytest.mark.parametrize(
    "username, EXPECTED_USERNAME",
    [
        ("Cocoa", "<@Cocoa>"),
        ("dark_Cocoa", "<@dark_Cocoa>"),
        ("Cocoa123", "<@Cocoa123>"),
    ],
)
def test_valid_callable_username(username, EXPECTED_USERNAME):
    ACTUAL_USERNAME = helpers.callable_username(username)
    assert EXPECTED_USERNAME == ACTUAL_USERNAME


def test_invalid_callable_username_int():
    with pytest.raises(ValueError) as invalid_user:
        username = 12
        EXPECTED_USERNAME = "<@12>"
        ACTUAL_USERNAME = helpers.callable_username(username)
    assert "not a str" in str(invalid_user.value)


@pytest.mark.parametrize("username", [None, ""])
def test_invalid_callable_username_null_or_null(username: str):
    with pytest.raises(ValueError) as invalid_user:
        EXPECTED_USERNAME = None
        ACTUAL_USERNAME = helpers.callable_username(username)
    assert "valid username was not passed in" in str(invalid_user.value)


@pytest.mark.parametrize(
    "dotw_index, EXPECTED_WEEKDAY",
    [
        (0, helpers.Weekdays.MONDAY),
        (1, helpers.Weekdays.TUESDAY),
        (2, helpers.Weekdays.WEDNESDAY),
        (3, helpers.Weekdays.THURSDAY),
        (4, helpers.Weekdays.FRIDAY),
        (5, helpers.Weekdays.SATURDAY),
        (6, helpers.Weekdays.SUNDAY),
    ],
)  # Day of the week index (Mon = 0, Sun = 6)
def test_valid_weekdays(dotw_index: int, EXPECTED_WEEKDAY: helpers.Weekdays):
    ACTUAL_WEEKDAY = helpers.Weekdays(dotw_index)

    assert EXPECTED_WEEKDAY == ACTUAL_WEEKDAY


@pytest.mark.parametrize("dotw_index", [-1, -2, 8, 9])
def test_invalid_weekdays(dotw_index: int):
    with pytest.raises(ValueError) as invalid_dotw:
        EXPECTED_WEEKDAY = None
        ACTUAL_WEEKDAY = helpers.Weekdays(dotw_index)
    assert invalid_dotw.type is ValueError


@pytest.mark.parametrize(
    "emoji, EXPECTED_DOTW",
    [
        ("🇲", helpers.Emojis.MONDAY),
        ("🇹", helpers.Emojis.TUESDAY),
        ("🇼", helpers.Emojis.WENDESAY),
        ("🇷", helpers.Emojis.THURSDAY),
        ("🇫", helpers.Emojis.FRIDAY),
        ("🇸", helpers.Emojis.SATURDAY),
        ("🇺", helpers.Emojis.SUNDAY),
    ],
)
def test_valid_emojis(emoji: str, EXPECTED_DOTW: str):
    ACUAL_DOTW = helpers.Emojis(emoji)
    assert EXPECTED_DOTW == ACUAL_DOTW

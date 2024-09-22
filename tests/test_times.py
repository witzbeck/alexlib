"""Test the new datetime methods."""

from datetime import datetime, timedelta, timezone

from pytest import FixtureRequest, fixture

from alexlib.constants import EPOCH
from alexlib.times import (
    HOLIDAYS,
    ONEDAY,
    CustomDatetime,
    CustomTimedelta,
    Timer,
    TimerLabel,
    get_local_tz,
    get_rand_datetime,
    get_rand_timedelta,
    timeit,
)


@fixture(scope="class", params=(get_rand_datetime() for _ in range(10)))
def dt(request: FixtureRequest) -> datetime:
    return request.param


@fixture(scope="class", params=(get_rand_timedelta() for _ in range(10)))
def td(request: FixtureRequest) -> timedelta:
    return request.param


@fixture(scope="class")
def cdt(dt: datetime) -> CustomDatetime:
    return CustomDatetime(dt)


@fixture(scope="class")
def ctd(td: timedelta) -> CustomTimedelta:
    return CustomTimedelta(td)


def test_get_local_tz():
    """Ensure it returns the correct local timezone."""
    assert isinstance(
        get_local_tz(), timezone
    ), "The returned value is not a timezone instance."


def test_epoch_is_datetime() -> None:
    """Test that epoch is a datetime object."""
    assert isinstance(EPOCH, datetime)


def test_makes_rand_datetime(dt: datetime) -> None:
    """Test that get_rand_datetime makes a datetime object."""
    assert isinstance(dt, datetime)


def test_makes_rand_timedelta(td: timedelta) -> None:
    """Test that get_rand_timedelta makes a timedelta object."""
    assert isinstance(td, timedelta)


def test_rounds_datetime(cdt: CustomDatetime) -> None:
    """Test that round_datetime rounds a custom datetime object."""
    assert isinstance(round(cdt, ONEDAY), datetime)


def test_can_get_custom_datetime(cdt: CustomDatetime) -> None:
    """Test that CustomDatetime can be created from a datetime object."""
    assert isinstance(cdt, CustomDatetime)


def test_can_get_custom_timedelta(ctd: CustomTimedelta) -> None:
    """Test that CustomTimedelta can be created from a timedelta object."""
    assert isinstance(ctd, CustomTimedelta)


def test_xmas_isholiday(this_xmas: CustomDatetime) -> None:
    """Test isholiday method."""
    assert (
        this_xmas.isholiday
    ), f"{this_xmas} should be a holiday but is not in {HOLIDAYS}."


def test_not_xmas_isholiday(day_after_xmas: CustomDatetime) -> None:
    """Test isholiday method."""
    assert not day_after_xmas.isholiday, f"{day_after_xmas} should not be a holiday."


def test_weekday_not_weekend(cdt: CustomDatetime) -> None:
    """Test isweekday method."""
    assert (
        cdt.isweekday is not cdt.isweekend
    ), f"{cdt} cannot be both a weekday and a weekend."


def test_isbusinessday(cdt: CustomDatetime) -> None:
    """Test isbusinessday method."""
    if cdt.isbusinessday:
        assert (
            not cdt.isholiday and not cdt.isweekend
        ), f"{cdt} should be not be a holiday or weekend."
    else:
        assert cdt.isholiday or cdt.isweekend, f"{cdt} should be a holiday or weekend."


def test_tomorrow(cdt: CustomDatetime) -> None:
    """Test tomorrow method."""
    assert cdt.tomorrow == cdt + ONEDAY


def test_yesterday(cdt: CustomDatetime) -> None:
    """Test yesterday method."""
    assert cdt.yesterday == cdt - ONEDAY


def test_get_last_busday(cdt: CustomDatetime) -> None:
    """Test get_last_busday method."""
    last_busday = cdt.get_last_busday()
    if cdt.yesterday.isbusinessday:
        assert last_busday == cdt.yesterday
    else:
        assert last_busday < cdt


@fixture(scope="class")
def timer():
    return Timer()


def test_timer_start(timer: Timer):
    assert isinstance(timer.start, float)


def test_timer_soft_last_record(timer: Timer):
    assert isinstance(timer.soft_last_record, float)


def test_timer_hard_last_record(timer: Timer):
    assert isinstance(timer.hard_last_record, float)


def test_timer_soft_elapsed_from_last(timer: Timer):
    assert isinstance(timer.soft_elapsed_from_last, float)


def test_timer_soft_elapsed_from_start(timer: Timer):
    assert isinstance(timer.soft_elapsed_from_start, float)


def test_timer_soft_start_label(timer: Timer):
    assert isinstance(timer.soft_start_label, TimerLabel)


def test_timer_soft_start_label_str(timer: Timer):
    assert isinstance(str(timer.soft_start_label), str)


def test_timer_soft_last_label(timer: Timer):
    assert isinstance(timer.soft_last_label, TimerLabel)


def test_timer_soft_last_label_str(timer: Timer):
    assert isinstance(str(timer.soft_last_label), str)


def test_timer_from_start_label(timer: Timer):
    assert isinstance(timer.from_start_label, TimerLabel)


def test_timer_from_start_label_str(timer: Timer):
    assert isinstance(str(timer.from_start_label), str)


def test_timer_from_last_label_str(timer: Timer):
    assert isinstance(str(timer.from_last_label), str)


def test_timer_from_last_label(timer: Timer):
    assert isinstance(timer.from_last_label, TimerLabel)


def test_timer_log_from_last(timer: Timer):
    assert isinstance(timer.log_from_last(), str)


def test_timer_log_from_start(timer: Timer):
    assert isinstance(timer.log_from_start(), str)


def test_timeit():
    @timeit()
    def to_time_func():
        pass

    to_time_func()
    assert True

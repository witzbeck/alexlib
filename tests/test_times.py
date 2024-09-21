"""Test the new datetime methods."""

from datetime import datetime, timedelta

from pytest import FixtureRequest, fixture

from alexlib.constants import EPOCH
from alexlib.times import (
    ONEDAY,
    CustomDatetime,
    CustomTimedelta,
    get_rand_datetime,
    get_rand_timedelta,
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
    assert this_xmas.isholiday


def test_not_xmas_isholiday(day_after_xmas: CustomDatetime) -> None:
    """Test isholiday method."""
    assert not day_after_xmas.isholiday


def test_weekday_not_weekend(cdt: CustomDatetime) -> None:
    """Test isweekday method."""
    assert cdt.isweekday is not cdt.isweekend


def test_isbusinessday(cdt: CustomDatetime) -> None:
    """Test isbusinessday method."""
    if cdt.isbusinessday:
        assert not cdt.isholiday and not cdt.isweekend
    else:
        assert cdt.isholiday or cdt.isweekend


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

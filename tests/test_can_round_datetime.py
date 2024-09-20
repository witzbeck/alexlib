"""Test the round_datetime function."""

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


def test_makes_rand_datetime(dt) -> None:
    """Test that get_rand_datetime makes a datetime object."""
    assert isinstance(dt, datetime)


def test_makes_rand_timedelta(td) -> None:
    """Test that get_rand_timedelta makes a timedelta object."""
    assert isinstance(td, timedelta)


def test_rounds_datetime(cdt) -> None:
    """Test that round_datetime rounds a custom datetime object."""
    assert isinstance(round(cdt, ONEDAY), datetime)


def test_can_get_custom_datetime(cdt) -> None:
    """Test that CustomDatetime can be created from a datetime object."""
    assert isinstance(cdt, CustomDatetime)


def test_can_get_custom_timedelta(ctd) -> None:
    """Test that CustomTimedelta can be created from a timedelta object."""
    assert isinstance(ctd, CustomTimedelta)

from pytest import FixtureRequest, fixture

from alexlib.maths import get_primes, randbool


@fixture(scope="module", params=list(range(10, 46, 7)))
def primes(request: FixtureRequest) -> list[int]:
    return get_primes(request.param)


@fixture(scope="module")
def rbool():
    return randbool()


def test_randbool(rbool):
    assert isinstance(rbool, bool)


def test_nprimes_are_ints(primes):
    assert all(isinstance(x, int) for x in primes)


def test_nprimes_gt_one(primes):
    assert all(x > 1 for x in primes)


# @mark.parametrize("n", params=(2, 3, 5, 7, 11, 13, 17, 19, 23, 29), indirect=True)
# def test_nprimes_mod(primes, n):
#    assert all(x % n or x == n for x in primes)
#
#
# INTORFLOAT_PARAMS = (
#    (1, True),
#    (1.0, True),
#    (1.1, True),
#    ("", False),
#    (False, False),
# )
#
#
# @mark.parametrize("n,expected", params=INTORFLOAT_PARAMS)
# def test_isintorfloat(n, expected):
#    assert isintorfloat(n) is expected
#
#
# INTERPOLATE_PARAMS = (
#    (1, 0, 2, 0, 2),
#    (2, 0, 2, 0, 2),
#    (3, 0, 2, 0, 2),
#    (4, 0, 2, 0, 2),
#    (5, 0, 2, 0, 2),
# )
#
#
# @mark.parametrize("x,x1,x2,y1,y2", params=INTERPOLATE_PARAMS)
# def test_interpolate(x, x1, x2, y1, y2):
#    assert interpolate(x, x1, x2, y1, y2) == y1 + (y2 - y1) * (x - x1) / (x2 - x1)
#

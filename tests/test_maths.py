from random import randint

from pytest import FixtureRequest, fixture, mark, raises

from alexlib.maths import (
    VariableBaseNumber,
    euclidean_distance,
    get_phi_by_precision,
    get_primes,
    interpolate,
    isintorfloat,
    phi_generator,
    randbool,
)


@fixture(scope="module", params=list(range(10, 46, 7)))
def primes(request: FixtureRequest) -> list[int]:
    return get_primes(request.param)


@fixture(scope="module")
def rbool() -> bool:
    return randbool()


def test_randbool(rbool: bool):
    assert isinstance(rbool, bool)


def test_nprimes_are_ints(primes: list[int]):
    assert all(isinstance(x, int) for x in primes)


def test_nprimes_gt_one(primes: list[int]):
    assert all(x > 1 for x in primes)


@mark.parametrize("n", (2, 3, 5, 7, 11, 13, 17, 19, 23, 29))
def test_nprimes_mod(primes, n):
    assert all(x % n or x == n for x in primes)


INTORFLOAT_PARAMS = (
    (1, True),
    (1.0, True),
    (1.1, True),
    ("", False),
    (False, False),
)


@mark.parametrize("n,expected", INTORFLOAT_PARAMS)
def test_isintorfloat(n, expected):
    assert isintorfloat(n) is expected


INTERPOLATE_REAL_PARAMS = (
    (1, 1, 2, 0, 2),
    (1, 0, 2, 0, 2),
    (2, 0, 2, 0, 2),
    (3, 0, 2, 0, 2),
    (4, 0, 2, 0, 2),
    (5, 0, 2, 0, 2),
)


@mark.parametrize("x,x1,x2,y1,y2", INTERPOLATE_REAL_PARAMS)
def test_interpolate_real(x, x1, x2, y1, y2):
    assert interpolate(x, x1, x2, y1, y2) == y1 + (y2 - y1) * (x - x1) / (x2 - x1)


INTERPOLATE_CALLABLE_PARAMS = ((5, 0, 2, lambda z: z**2, lambda a: a**1 / 2),)


@mark.parametrize("x,x1,x2,y1,y2", INTERPOLATE_CALLABLE_PARAMS)
def test_interpolate_callable(x, x1, x2, y1, y2):
    assert isinstance(interpolate(x, x1, x2, y1, y2), float)


def test_interpolate_error1():
    with raises(TypeError):
        interpolate(1, 0, 2, "a", "b")


def test_interpolate_error2():
    with raises(TypeError):
        interpolate(1, 0, 2, 0, "b")


@fixture(scope="module")
def phi_steps():
    return randint(1, 10)


@fixture(scope="module")
def phi(phi_steps):
    generator = phi_generator()
    values = [next(generator) for _ in range(phi_steps)]
    return values[-1]


def test_phi(phi):
    assert isinstance(phi, float)
    assert 1 < phi <= 2


@fixture(scope="module", params=(1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7))
def e(request: FixtureRequest):
    return request.param


def test_get_phi_by_precision(e):
    phi = get_phi_by_precision(e=e)
    assert 1 < phi <= 2
    assert abs(phi - 1.618033988749895) < e


@fixture(
    scope="module",
    params=(
        (-5, 4),
        (25, 10),
        (2, 2),
        (40.5, 20),
    ),
)
def variable_base_number(request: FixtureRequest):
    base10_val, base = request.param
    return VariableBaseNumber(base10_val, base)


def test_variable_base_number(variable_base_number):
    assert repr(variable_base_number)


@mark.parametrize("values", ((-5, 4), (25, 10), (2, 2), (40.5, 20), (12, 346, 568568)))
def test_euclidean_algorithm(values):
    assert isinstance(euclidean_distance(values), float)

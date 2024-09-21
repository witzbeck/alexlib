from random import randint

from pytest import fixture

from alexlib.maths import get_primes, randbool


@fixture(scope="module")
def max_n():
    return randint(10, 30)


@fixture(scope="module")
def primes(max_n):
    return get_primes(max_n)


@fixture(scope="module")
def rbool():
    return randbool()


def test_randbool(rbool):
    assert rbool in (True, False)
    assert isinstance(rbool, bool)


def test_nprimes_len(max_n, primes):
    assert len(primes) < max_n


def test_nprimes_are_ints(primes):
    assert all(isinstance(x, int) for x in primes)


def test_nprimes_gt_one(primes):
    assert all(x > 1 for x in primes)


def test_nprimes_mod2(primes):
    assert all(x % 2 or x == 2 for x in primes)


def test_nprimes_mod3(primes):
    assert all(x % 3 or x == 3 for x in primes)


def test_nprimes_mod5(primes):
    assert all(x % 5 or x == 5 for x in primes)


def test_nprimes_mod7(primes):
    assert all(x % 7 or x == 7 for x in primes)


def test_nprimes_mod11(primes):
    assert all(x % 11 or x == 11 for x in primes)


def test_nprimes_mod13(primes):
    assert all(x % 13 or x == 13 for x in primes)


def test_nprimes_mod17(primes):
    assert all(x % 17 or x == 17 for x in primes)


def test_nprimes_mod19(primes):
    assert all(x % 19 or x == 19 for x in primes)


def test_nprimes_mod23(primes):
    assert all(x % 23 or x == 23 for x in primes)


def test_nprimes_mod29(primes):
    assert all(x % 29 or x == 29 for x in primes)

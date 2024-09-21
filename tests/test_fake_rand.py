from functools import partial
from random import randint
from string import ascii_letters, digits, printable, punctuation

from pytest import raises

from alexlib.fake import (
    infgen,
    limgen,
    randdigit,
    randintstr,
    randlet,
    randprint,
    randrange,
)
from alexlib.maths import randbool

TEST_LOOP_RANGE = range(10)
RANDINTSTR_KWARGS = {"min_int": -100_000, "max_int": 100_000}
limgen_randint = partial(randint, 5, 50)


def test_randdigit():
    """Test randdigit."""
    assert min(randdigit() in digits for _ in TEST_LOOP_RANGE)


def test_randintstr():
    """Test randintstr."""
    assert min(int(randintstr()) in range(11) for _ in TEST_LOOP_RANGE)
    assert min(
        isinstance(randintstr(**RANDINTSTR_KWARGS), str) for _ in TEST_LOOP_RANGE
    )


def test_randintstr_negatives():
    """Test randintstr with negative integers."""
    assert min(int(randintstr(-10, -1)) in range(-10, 0) for _ in TEST_LOOP_RANGE)


def test_randintstr_min_over_max():
    """Test randintstr with min_int > max_int."""
    with raises(ValueError):
        randintstr(10, 1)


def test_randprint():
    """Test randprint."""
    assert min(randprint() in printable for _ in TEST_LOOP_RANGE)


def test_randlet():
    """Test randlet."""
    assert min(randlet() in ascii_letters for _ in TEST_LOOP_RANGE)


def test_infgen_digit():
    """Test infgen with digit."""
    gen = infgen(digit=True)
    assert min(int(next(gen)) in range(10) for _ in randrange())


def test_infgen_vowel():
    """Test infgen with vowel."""
    gen = infgen(vowel=True)
    assert min(next(gen) in "aeiou" for _ in randrange())


def test_infgen_letter():
    """Test infgen with letter."""
    gen = infgen(letter=True)
    assert min(next(gen) in ascii_letters for _ in randrange())


def test_infgen_intstr():
    """Test infgen with intstr."""
    gen = infgen(intstr=True)
    assert min(int(next(gen)) in range(11) for _ in randrange())


def test_infgen_printable():
    """Test infgen with printable."""
    gen = infgen(printable_=True)
    assert min(next(gen) in printable for _ in randrange())


def test_infgen_punct():
    """Test infgen with punct."""
    gen = infgen(punct=True)
    assert min(next(gen) in punctuation for _ in randrange())


def test_infgen_no_args():
    """Test infgen with no args."""
    with raises(ValueError):
        next(infgen())


def test_infgen_many_args_is_fine():
    """Test infgen with many args."""
    for _ in TEST_LOOP_RANGE:
        rand_args = [randbool() for _ in range(6)]
        if max(rand_args):
            gen = infgen(*rand_args)
            assert [next(gen) for _ in TEST_LOOP_RANGE]


def test_limgen_digit():
    """Test limgen with digit."""
    gen = limgen(limgen_randint(), digit=True)
    assert isinstance(gen, str)
    gen = limgen(limgen_randint(), concat=False, digit=True)
    assert isinstance(gen, list)


def test_limgen_vowel():
    """Test limgen with vowel."""
    gen = limgen(limgen_randint(), vowel=True)
    assert isinstance(gen, str)
    gen = limgen(limgen_randint(), concat=False, vowel=True)
    assert isinstance(gen, list)


def test_limgen_letter():
    """Test limgen with letter."""
    gen = limgen(limgen_randint(), letter=True)
    assert isinstance(gen, str)
    gen = limgen(limgen_randint(), concat=False, letter=True)
    assert isinstance(gen, list)


def test_limgen_intstr():
    """Test limgen with intstr."""
    gen = limgen(limgen_randint(), intstr=True)
    assert isinstance(gen, str)
    gen = limgen(limgen_randint(), concat=False, intstr=True)
    assert isinstance(gen, list)


def test_limgen_printable():
    """Test limgen with printable."""
    gen = limgen(limgen_randint(), printable_=True)
    assert isinstance(gen, str)
    gen = limgen(limgen_randint(), concat=False, printable_=True)
    assert isinstance(gen, list)


def test_limgen_punct():
    """Test limgen with punct."""
    gen = limgen(limgen_randint(), punct=True)
    assert isinstance(gen, str)
    gen = limgen(limgen_randint(), concat=False, punct=True)
    assert isinstance(gen, list)


def test_limgen_no_args():
    """Test limgen with no args."""
    with raises(ValueError):
        limgen(limgen_randint())


def test_limgen_many_args_is_fine_concat():
    """Test limgen with many args."""
    for _ in TEST_LOOP_RANGE:
        rand_args = [randbool() for _ in range(6)]
        if max(rand_args):
            rand_kwargs = {
                "digit": rand_args[0],
                "vowel": rand_args[1],
                "letter": rand_args[2],
                "intstr": rand_args[3],
                "printable_": rand_args[4],
                "punct": rand_args[5],
            }
            gen = limgen(limgen_randint(), **rand_kwargs)
            assert isinstance(gen, str)


def test_limgen_many_args_is_fine_no_concat():
    """Test limgen with many args."""
    for _ in TEST_LOOP_RANGE:
        rand_args = [randbool() for _ in range(6)]
        if max(rand_args):
            rand_kwargs = {
                "digit": rand_args[0],
                "vowel": rand_args[1],
                "letter": rand_args[2],
                "intstr": rand_args[3],
                "printable_": rand_args[4],
                "punct": rand_args[5],
            }
            gen = limgen(limgen_randint(), concat=False, **rand_kwargs)
            assert isinstance(gen, list)
            assert list(gen)

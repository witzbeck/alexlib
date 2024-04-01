from functools import partial
from random import randint
from string import ascii_letters, digits, printable, punctuation
from unittest import TestCase, main
from alexlib.constants import ISTYPE_EXTS

from alexlib.fake import (
    infgen,
    limgen,
    randdigit,
    randfileext,
    randlet,
    randprint,
    randintstr,
    randrange,
)
from alexlib.maths.maths import randbool

TEST_LOOP_RANGE = range(10)
RANDINTSTR_KWARGS = {"min_int": -100_000, "max_int": 100_000}
limgen_randint = partial(randint, 5, 50)


class TestFakeRand(TestCase):
    """Test fake_rand module."""

    def test_randdigit(self):
        """Test randdigit."""
        self.assertTrue(min(randdigit() in digits for _ in TEST_LOOP_RANGE))

    def test_randintstr(self):
        """Test randintstr."""
        self.assertTrue(min(int(randintstr()) in range(11) for _ in TEST_LOOP_RANGE))
        self.assertTrue(
            min(
                isinstance(randintstr(**RANDINTSTR_KWARGS), str)
                for _ in TEST_LOOP_RANGE
            )
        )

    def test_randintstr_negatives(self):
        """Test randintstr with negative integers."""
        self.assertTrue(
            min(int(randintstr(-10, -1)) in range(-10, 0) for _ in TEST_LOOP_RANGE)
        )

    def test_randintstr_min_over_max(self):
        """Test randintstr with min_int > max_int."""
        with self.assertRaises(ValueError):
            randintstr(10, 1)

    def test_randprint(self):
        """Test randprint."""
        self.assertTrue(min(randprint() in printable for _ in TEST_LOOP_RANGE))

    def test_randfileext(self):
        """Test randfileext."""
        self.assertTrue(min(randfileext() in ISTYPE_EXTS for _ in TEST_LOOP_RANGE))

    def test_randlet(self):
        """Test randlet."""
        self.assertTrue(min(randlet() in ascii_letters for _ in TEST_LOOP_RANGE))

    def test_infgen_digit(self):
        """Test infgen with digit."""
        gen = infgen(digit=True)
        self.assertTrue(min(int(next(gen)) in range(10) for _ in randrange()))

    def test_infgen_vowel(self):
        """Test infgen with vowel."""
        gen = infgen(vowel=True)
        self.assertTrue(min(next(gen) in "aeiou" for _ in randrange()))

    def test_infgen_letter(self):
        """Test infgen with letter."""
        gen = infgen(letter=True)
        self.assertTrue(min(next(gen) in ascii_letters for _ in randrange()))

    def test_infgen_intstr(self):
        """Test infgen with intstr."""
        gen = infgen(intstr=True)
        self.assertTrue(min(int(next(gen)) in range(11) for _ in randrange()))

    def test_infgen_printable(self):
        """Test infgen with printable."""
        gen = infgen(printable_=True)
        self.assertTrue(min(next(gen) in printable for _ in randrange()))

    def test_infgen_punct(self):
        """Test infgen with punct."""
        gen = infgen(punct=True)
        self.assertTrue(min(next(gen) in punctuation for _ in randrange()))

    def test_infgen_no_args(self):
        """Test infgen with no args."""
        with self.assertRaises(ValueError):
            next(infgen())

    def test_infgen_many_args_is_fine(self):
        """Test infgen with many args."""
        for _ in TEST_LOOP_RANGE:
            rand_args = [randbool() for _ in range(6)]
            if max(rand_args):
                gen = infgen(*rand_args)
                self.assertTrue([next(gen) for _ in TEST_LOOP_RANGE])

    def test_limgen_digit(self):
        """Test limgen with digit."""
        gen = limgen(limgen_randint(), digit=True)
        self.assertIsInstance(gen, str)
        gen = limgen(limgen_randint(), concat=False, digit=True)
        self.assertIsInstance(gen, list)

    def test_limgen_vowel(self):
        """Test limgen with vowel."""
        gen = limgen(limgen_randint(), vowel=True)
        self.assertIsInstance(gen, str)
        gen = limgen(limgen_randint(), concat=False, vowel=True)
        self.assertIsInstance(gen, list)

    def test_limgen_letter(self):
        """Test limgen with letter."""
        gen = limgen(limgen_randint(), letter=True)
        self.assertIsInstance(gen, str)
        gen = limgen(limgen_randint(), concat=False, letter=True)
        self.assertIsInstance(gen, list)

    def test_limgen_intstr(self):
        """Test limgen with intstr."""
        gen = limgen(limgen_randint(), intstr=True)
        self.assertIsInstance(gen, str)
        gen = limgen(limgen_randint(), concat=False, intstr=True)
        self.assertIsInstance(gen, list)

    def test_limgen_printable(self):
        """Test limgen with printable."""
        gen = limgen(limgen_randint(), printable_=True)
        self.assertIsInstance(gen, str)
        gen = limgen(limgen_randint(), concat=False, printable_=True)
        self.assertIsInstance(gen, list)

    def test_limgen_punct(self):
        """Test limgen with punct."""
        gen = limgen(limgen_randint(), punct=True)
        self.assertIsInstance(gen, str)
        gen = limgen(limgen_randint(), concat=False, punct=True)
        self.assertIsInstance(gen, list)

    def test_limgen_no_args(self):
        """Test limgen with no args."""
        with self.assertRaises(ValueError):
            limgen(limgen_randint())

    def test_limgen_many_args_is_fine_concat(self):
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
                self.assertIsInstance(gen, str)

    def test_limgen_many_args_is_fine_no_concat(self):
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
                self.assertIsInstance(gen, list)
                self.assertTrue([x for x in gen])


if __name__ == "__main__":
    main()

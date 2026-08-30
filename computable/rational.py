"""Finite exact rational substrate for :mod:`computable`.

``Rational`` denotes exactly Q.  Public class calls are canonical/frozen and
weak-interned, while raw instance allocation remains an unmodified ``__new__``
path for mutable arithmetic workspaces.
"""
from __future__ import annotations

import math
import re
import sys
from fractions import Fraction
from typing import ClassVar
from weakref import WeakValueDictionary

from ._rational_helpers import (
    bounded_denominator_bracket,
    integer_nth_root,
    nearest_bounded_denominator,
    product_integer_ratios,
    sum_integer_ratios,
)
from .core.family import NumericFamily
from .core.kinds import NumericKind
from .core.promotion import SUBDOMAINS, ConversionRegistry
from .projections.binary import rational_to_binary64

_SCALAR_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")
_SUBDOMAINS_REGISTERED = False


def _normalize_pair_no_gcd(n: int, d: int) -> tuple[int, int, bool]:
    """Restore storage invariants without proving a nontrivial gcd fact.

    The Boolean is a conservative certificate that the resulting pair is
    already canonical.  It is intentionally *not* a request to simplify.
    """

    if d == 0:
        raise ZeroDivisionError("rational denominator is zero")
    if d < 0:
        n, d = -n, -d
    if n == 0:
        return 0, 1, True
    return n, d, d == 1 or abs(n) == 1


def _canonical_pair(n: int, d: int) -> tuple[int, int]:
    n, d, known = _normalize_pair_no_gcd(n, d)
    if known:
        return n, d
    g = math.gcd(n, d)
    return n // g, d // g


def _hash_integer_ratio(n: int, d: int) -> int:
    """Python numeric hash for a reduced integer ratio, without float conversion."""

    if d == 1:
        return hash(n)
    modulus = sys.hash_info.modulus
    try:
        inverse = pow(d, -1, modulus)
    except ValueError:
        value = sys.hash_info.inf
    else:
        value = (abs(n) % modulus) * inverse % modulus
    if n < 0:
        value = -value
    return -2 if value == -1 else value


def _parse_decimal_scalar(text: str) -> tuple[int, int, bool]:
    if not _SCALAR_RE.fullmatch(text):
        raise ValueError(f"invalid Rational string scalar: {text!r}")

    sign = -1 if text.startswith("-") else 1
    if text[:1] in "+-":
        text = text[1:]

    if "e" in text.lower():
        mantissa, exp_text = re.split("[eE]", text, maxsplit=1)
        exponent = int(exp_text)
    else:
        mantissa = text
        exponent = 0

    if "." in mantissa:
        head, tail = mantissa.split(".", 1)
        digits = (head or "0") + tail
        scale = len(tail)
    else:
        digits = mantissa
        scale = 0

    n = sign * int(digits)
    power = exponent - scale
    if power >= 0:
        return _normalize_pair_no_gcd(n * (10**power), 1)
    return _normalize_pair_no_gcd(n, 10 ** (-power))


class _RationalMeta(type):
    """Public Rational factory policy, deliberately above raw ``__new__``."""

    def __call__(cls, *args):
        n, d, canonical_known = cls._parse_constructor_args(args)

        # As in the reference implementation, try the raw key first even when
        # canonicality is only unknown.  A live canonical cache hit proves that
        # no gcd work is necessary.
        cache = cls._cache
        key = (n, d)
        cached = cache.get(key)
        if cached is not None:
            return cached

        if not canonical_known:
            n, d = _canonical_pair(n, d)
            key = (n, d)
            cached = cache.get(key)
            if cached is not None:
                return cached

        h = _hash_integer_ratio(n, d)
        obj = cls.__new__(cls)  # inherited object.__new__: the raw birth path
        object.__setattr__(obj, "_numerator", n)
        object.__setattr__(obj, "_denominator", d)
        object.__setattr__(obj, "_is_simplified", True)
        object.__setattr__(obj, "_is_frozen", True)
        object.__setattr__(obj, "_hash", h)
        cache[key] = obj
        return obj


class Rational(metaclass=_RationalMeta):
    """Exact rational value with mutable-working / frozen-canonical lifecycle."""

    _kind: ClassVar[NumericKind] = NumericKind.RATIONAL
    _family: ClassVar[NumericFamily | None] = None
    _cache: ClassVar[WeakValueDictionary[tuple[int, int], "Rational"]] = WeakValueDictionary()

    __slots__ = (
        "_numerator",
        "_denominator",
        "_is_simplified",
        "_is_frozen",
        "_hash",
        "__weakref__",
    )

    # Intentionally no __new__ and no __init__.  Public Rational(...) policy is
    # in _RationalMeta.__call__; cls.__new__(cls) stays a genuine raw allocator.

    @classmethod
    def _allocate_working(
        cls,
        n: int,
        d: int,
        *,
        is_simplified: bool,
        hash_value: int | None = None,
    ) -> "Rational":
        obj = cls.__new__(cls)
        object.__setattr__(obj, "_numerator", n)
        object.__setattr__(obj, "_denominator", d)
        object.__setattr__(obj, "_is_simplified", is_simplified)
        object.__setattr__(obj, "_is_frozen", False)
        object.__setattr__(obj, "_hash", hash_value)
        return obj

    @classmethod
    def _new_working_raw(cls, n: int, d: int) -> "Rational":
        """Create one mutable result without gcd reduction."""

        n, d, trivially_canonical = _normalize_pair_no_gcd(int(n), int(d))
        return cls._allocate_working(n, d, is_simplified=trivially_canonical)

    @classmethod
    def _new_working_canonical(cls, n: int, d: int) -> "Rational":
        """Create one mutable result from a pair already known canonical.

        No gcd is performed: canonicality is a caller-provided internal fact.
        """

        n, d, _ = _normalize_pair_no_gcd(int(n), int(d))
        return cls._allocate_working(n, d, is_simplified=True)

    @classmethod
    def _compose_division(
        cls,
        up: tuple[int, int, bool],
        down: tuple[int, int, bool],
        *,
        zero_message: str,
    ) -> tuple[int, int, bool]:
        an, ad, _ = up
        bn, bd, _ = down
        if bn == 0:
            raise ZeroDivisionError(zero_message)
        return _normalize_pair_no_gcd(an * bd, ad * bn)

    @classmethod
    def _parse_constructor_args(cls, args: tuple[object, ...]) -> tuple[int, int, bool]:
        if len(args) == 1:
            return cls._parse_input(args[0])
        if len(args) == 2:
            return cls._compose_division(
                cls._parse_input(args[0]),
                cls._parse_input(args[1]),
                zero_message="Rational denominator is zero",
            )
        raise TypeError("Rational expects one value or numerator and denominator")

    @classmethod
    def _parse_input(cls, value) -> tuple[int, int, bool]:
        if isinstance(value, cls):
            # Read the exact raw ratio without simplifying/freezing/interning the
            # source.  _is_simplified is reusable representation knowledge.
            return value._numerator, value._denominator, value._is_simplified

        if isinstance(value, int):
            return int(value), 1, True

        if isinstance(value, Fraction):
            return value.numerator, value.denominator, True

        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("non-finite float is not a Rational")
            n, d = value.as_integer_ratio()
            return n, d, True

        if isinstance(value, complex):
            if not math.isfinite(value.real) or not math.isfinite(value.imag):
                raise ValueError("non-finite complex is not a Rational")
            if value.imag != 0.0:
                raise TypeError("complex value is not real and therefore not Rational")
            n, d = value.real.as_integer_ratio()
            return n, d, True

        if isinstance(value, str):
            return cls._parse_string(value)

        if isinstance(value, tuple):
            if len(value) != 2:
                raise TypeError("Rational tuple input must contain exactly two elements")
            return cls._compose_division(
                cls._parse_input(value[0]),
                cls._parse_input(value[1]),
                zero_message="Rational tuple divisor is zero",
            )

        recognized = SUBDOMAINS.recognize_rational_value(value)
        if recognized is not None and isinstance(recognized, cls):
            return (
                recognized._numerator,
                recognized._denominator,
                recognized._is_simplified,
            )
        raise TypeError(f"unsupported Rational input type: {type(value).__name__}")

    @classmethod
    def _parse_string(cls, text: str) -> tuple[int, int, bool]:
        stripped = text.strip()
        if not stripped:
            raise ValueError("empty Rational string")
        parts = stripped.split("/")
        if len(parts) > 2:
            raise ValueError(f"invalid Rational string: {text!r}")
        if len(parts) == 1:
            return _parse_decimal_scalar(parts[0])

        left, right = parts[0].strip(), parts[1].strip()
        if not left or not right:
            raise ValueError(f"invalid Rational string: {text!r}")
        return cls._compose_division(
            _parse_decimal_scalar(left),
            _parse_decimal_scalar(right),
            zero_message="Rational string divisor is zero",
        )

    @property
    def numerator(self) -> int:
        self.simplify()
        return self._numerator

    @numerator.setter
    def numerator(self, value) -> None:
        if self._is_frozen:
            raise ValueError("cannot mutate a frozen Rational")
        p, q, _ = type(self)._parse_input(value)
        self.simplify()
        d = self._denominator
        new_n, new_d, known = _normalize_pair_no_gcd(p, q * d)
        object.__setattr__(self, "_numerator", new_n)
        object.__setattr__(self, "_denominator", new_d)
        object.__setattr__(self, "_is_simplified", known)
        object.__setattr__(self, "_hash", None)

    @property
    def denominator(self) -> int:
        self.simplify()
        return self._denominator

    @denominator.setter
    def denominator(self, value) -> None:
        if self._is_frozen:
            raise ValueError("cannot mutate a frozen Rational")
        p, q, _ = type(self)._parse_input(value)
        if p == 0:
            raise ZeroDivisionError("Rational denominator assignment is zero")
        self.simplify()
        n, d = self._numerator, self._denominator
        new_n, new_d, known = _normalize_pair_no_gcd(n * q, d * p)
        object.__setattr__(self, "_numerator", new_n)
        object.__setattr__(self, "_denominator", new_d)
        object.__setattr__(self, "_is_simplified", known)
        object.__setattr__(self, "_hash", None)

    def simplify(self) -> None:
        if self._is_simplified:
            return
        n, d = _canonical_pair(self._numerator, self._denominator)
        object.__setattr__(self, "_numerator", n)
        object.__setattr__(self, "_denominator", d)
        object.__setattr__(self, "_is_simplified", True)
        # A mutable value should only have a cached hash when copied unchanged
        # from a frozen canonical source.  If simplification was needed, that
        # cached value cannot be trusted after unsupported raw-field mutation.
        if not self._is_frozen:
            object.__setattr__(self, "_hash", None)

    def __copy__(self) -> "Rational":
        cls = type(self)
        # Copy exact representation knowledge too; no gcd and no public factory.
        return cls._allocate_working(
            self._numerator,
            self._denominator,
            is_simplified=self._is_simplified,
            hash_value=self._hash,
        )

    def intern(self) -> "Rational":
        self.simplify()
        cls = type(self)
        key = (self._numerator, self._denominator)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        h = self._hash
        if h is None:
            h = _hash_integer_ratio(*key)
            object.__setattr__(self, "_hash", h)
        object.__setattr__(self, "_is_frozen", True)
        cls._cache[key] = self
        return self

    @classmethod
    def _coerce_rational(cls, value):
        if isinstance(value, (str, tuple)):
            return None
        if isinstance(value, cls):
            return value._numerator, value._denominator
        if isinstance(value, int):
            return int(value), 1
        if isinstance(value, Fraction):
            return value.numerator, value.denominator
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("non-finite float cannot enter exact Rational arithmetic")
            return value.as_integer_ratio()
        if isinstance(value, complex):
            if not math.isfinite(value.real) or not math.isfinite(value.imag):
                raise ValueError("non-finite complex cannot enter exact arithmetic")
            if value.imag != 0.0:
                return None
            return value.real.as_integer_ratio()
        q = SUBDOMAINS.recognize_rational_value(value)
        if isinstance(q, cls):
            return q._numerator, q._denominator
        return None

    @classmethod
    def _recognized_integer(cls, value) -> int:
        n = SUBDOMAINS.recognize_integer_value(value)
        if n is None:
            raise TypeError("expected a guaranteed-finite exact integer-valued numeric input")
        return n

    @staticmethod
    def _complex_arithmetic_guard(other) -> None:
        if isinstance(other, complex):
            if not math.isfinite(other.real) or not math.isfinite(other.imag):
                raise ValueError("non-finite complex cannot enter exact arithmetic")
            raise NotImplementedError(
                "finite complex arithmetic lifts through GaussianRational in Phase 3"
            )

    @classmethod
    def _binary_pair(cls, a: int, b: int, c: int, d: int, op: str) -> tuple[int, int, bool]:
        if op == "add":
            return _normalize_pair_no_gcd(a * d + c * b, b * d)
        if op == "sub":
            return _normalize_pair_no_gcd(a * d - c * b, b * d)
        if op == "mul":
            return _normalize_pair_no_gcd(a * c, b * d)
        if c == 0:
            raise ZeroDivisionError("division by zero")
        return _normalize_pair_no_gcd(a * d, b * c)

    def _binary_working(self, other, op: str):
        type(self)._complex_arithmetic_guard(other)
        pair = type(self)._coerce_rational(other)
        if pair is None:
            return NotImplemented
        c, d = pair
        n, q, known = type(self)._binary_pair(
            self._numerator, self._denominator, c, d, op
        )
        return type(self)._allocate_working(n, q, is_simplified=known)

    def __add__(self, other):
        return self._binary_working(other, "add")

    def __sub__(self, other):
        return self._binary_working(other, "sub")

    def __mul__(self, other):
        return self._binary_working(other, "mul")

    def __truediv__(self, other):
        return self._binary_working(other, "div")

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        type(self)._complex_arithmetic_guard(other)
        pair = type(self)._coerce_rational(other)
        if pair is None:
            return NotImplemented
        a, b = pair
        n, d, known = _normalize_pair_no_gcd(
            a * self._denominator - self._numerator * b,
            b * self._denominator,
        )
        return type(self)._allocate_working(n, d, is_simplified=known)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        type(self)._complex_arithmetic_guard(other)
        pair = type(self)._coerce_rational(other)
        if pair is None:
            return NotImplemented
        if self._numerator == 0:
            raise ZeroDivisionError("division by zero")
        a, b = pair
        n, d, known = _normalize_pair_no_gcd(
            a * self._denominator,
            b * self._numerator,
        )
        return type(self)._allocate_working(n, d, is_simplified=known)

    def _inplace(self, other, op: str):
        type(self)._complex_arithmetic_guard(other)
        pair = type(self)._coerce_rational(other)
        if pair is None:
            return NotImplemented
        c, d = pair
        n, q, known = type(self)._binary_pair(
            self._numerator, self._denominator, c, d, op
        )

        if self._is_frozen:
            return type(self)._allocate_working(n, q, is_simplified=known)

        # Mutable hot path: zero Rational allocations.  Preserve representation
        # knowledge/hash when the raw pair itself is unchanged.
        if n == self._numerator and q == self._denominator:
            return self
        object.__setattr__(self, "_numerator", n)
        object.__setattr__(self, "_denominator", q)
        object.__setattr__(self, "_is_simplified", known)
        object.__setattr__(self, "_hash", None)
        return self

    def __iadd__(self, other):
        return self._inplace(other, "add")

    def __isub__(self, other):
        return self._inplace(other, "sub")

    def __imul__(self, other):
        return self._inplace(other, "mul")

    def __itruediv__(self, other):
        return self._inplace(other, "div")

    def __neg__(self):
        cls = type(self)
        if self._is_simplified:
            return cls._new_working_canonical(-self._numerator, self._denominator)
        return cls._new_working_raw(-self._numerator, self._denominator)

    def __pos__(self):
        return self.__copy__()

    def __abs__(self):
        if self._numerator >= 0:
            return self.__copy__()
        cls = type(self)
        if self._is_simplified:
            return cls._new_working_canonical(-self._numerator, self._denominator)
        return cls._new_working_raw(-self._numerator, self._denominator)

    def __pow__(self, exponent, modulo=None):
        if modulo is not None:
            return NotImplemented
        n = type(self)._recognized_integer(exponent)
        a, b = self._numerator, self._denominator
        if n == 0:
            return type(self)._new_working_canonical(1, 1)
        if n < 0:
            if a == 0:
                raise ZeroDivisionError("zero cannot be raised to a negative power")
            a, b = b, a
            n = -n
        num = pow(a, n)
        den = pow(b, n)
        if self._is_simplified:
            return type(self)._new_working_canonical(num, den)
        return type(self)._new_working_raw(num, den)

    def __bool__(self) -> bool:
        return self._numerator != 0

    def __int__(self) -> int:
        n, d = self._numerator, self._denominator
        return n // d if n >= 0 else -((-n) // d)

    def __floor__(self) -> int:
        return self._numerator // self._denominator

    def __ceil__(self) -> int:
        return -((-self._numerator) // self._denominator)

    @staticmethod
    def _round_ratio(n: int, d: int) -> int:
        q, r = divmod(n, d)
        twice = r << 1
        if twice > d or (twice == d and (q & 1)):
            q += 1
        return q

    def __round__(self, ndigits=None):
        if ndigits is None:
            return self._round_ratio(self._numerator, self._denominator)
        k = type(self)._recognized_integer(ndigits)
        if k >= 0:
            scale = 10**k
            q = self._round_ratio(self._numerator * scale, self._denominator)
            return type(self)._new_working_raw(q, scale)
        scale = 10 ** (-k)
        q = self._round_ratio(self._numerator, self._denominator * scale)
        return type(self)._new_working_raw(q * scale, 1)

    def __float__(self) -> float:
        return rational_to_binary64(self._numerator, self._denominator)

    def __complex__(self) -> complex:
        return complex(float(self), 0.0)

    def __eq__(self, other):
        pair = type(self)._coerce_rational(other)
        if pair is None:
            if isinstance(other, (complex, float, int, Fraction)):
                return False
            return NotImplemented
        c, d = pair
        return self._numerator * d == c * self._denominator

    def __ne__(self, other):
        result = self.__eq__(other)
        return NotImplemented if result is NotImplemented else not result

    def _compare(self, other, op: str):
        pair = type(self)._coerce_rational(other)
        if pair is None:
            if isinstance(other, complex):
                raise TypeError("ordering is undefined for non-real complex values")
            return NotImplemented
        c, d = pair
        left = self._numerator * d
        right = c * self._denominator
        if op == "lt":
            return left < right
        if op == "le":
            return left <= right
        if op == "gt":
            return left > right
        return left >= right

    def __lt__(self, other):
        return self._compare(other, "lt")

    def __le__(self, other):
        return self._compare(other, "le")

    def __gt__(self, other):
        return self._compare(other, "gt")

    def __ge__(self, other):
        return self._compare(other, "ge")

    def __hash__(self) -> int:
        if self._is_frozen:
            return self._hash
        self.simplify()
        cls = type(self)
        key = (self._numerator, self._denominator)
        cached = cls._cache.get(key)
        h = self._hash
        if h is None:
            # A live canonical equal object already carries the exact stable
            # Python numeric hash; reuse that knowledge instead of recomputing.
            h = cached._hash if cached is not None else _hash_integer_ratio(*key)
            object.__setattr__(self, "_hash", h)
        object.__setattr__(self, "_is_frozen", True)
        if cached is None:
            cls._cache[key] = self
        return h

    def __str__(self) -> str:
        self.simplify()
        if self._denominator == 1:
            return str(self._numerator)
        return f"{self._numerator}/{self._denominator}"

    def __repr__(self) -> str:
        self.simplify()
        if self._denominator == 1:
            return f"Rational({self._numerator})"
        return f"Rational({self._numerator}, {self._denominator})"

    # Private Phase-2 helper hooks. Public grid spelling arrives in Phase 9.
    @staticmethod
    def _integer_nth_root(n: int, degree: int) -> tuple[int, bool]:
        return integer_nth_root(n, degree)

    def _bounded_denominator_bracket(self, max_denominator: int):
        n = type(self)._recognized_integer(max_denominator)
        if n < 1:
            raise ValueError("max_denominator must be positive")
        self.simplify()
        left, right = bounded_denominator_bracket(
            self._numerator, self._denominator, n, reduced=True
        )
        return (
            type(self)._new_working_canonical(*left),
            type(self)._new_working_canonical(*right),
        )

    def _nearest_bounded_denominator(self, max_denominator: int):
        n = type(self)._recognized_integer(max_denominator)
        if n < 1:
            raise ValueError("max_denominator must be positive")
        self.simplify()
        pair = nearest_bounded_denominator(
            self._numerator, self._denominator, n, reduced=True
        )
        return type(self)._new_working_canonical(*pair)

    @classmethod
    def _sum_integer_ratios(cls, values):
        return cls._new_working_raw(*sum_integer_ratios(values))

    @classmethod
    def _product_integer_ratios(cls, values):
        return cls._new_working_raw(*product_integer_ratios(values))


def _recognize_fraction_integer(value: Fraction) -> int | None:
    return value.numerator if value.denominator == 1 else None


def _recognize_float_integer(value: float) -> int | None:
    if not math.isfinite(value):
        raise ValueError("non-finite float cannot enter exact finite recognition")
    n, d = value.as_integer_ratio()
    return n if d == 1 else None


def _recognize_complex_integer(value: complex) -> int | None:
    if not math.isfinite(value.real) or not math.isfinite(value.imag):
        raise ValueError("non-finite complex cannot enter exact finite recognition")
    if value.imag != 0.0:
        return None
    n, d = value.real.as_integer_ratio()
    return n if d == 1 else None


def _recognize_rational_integer(value: Rational) -> int | None:
    # Do not simplify or materialize anything.  Reuse canonicality knowledge: a
    # reduced Rational is integral iff its denominator is already 1.
    if value._is_simplified:
        return value._numerator if value._denominator == 1 else None
    q, r = divmod(value._numerator, value._denominator)
    return q if r == 0 else None


def _recognize_complex_rational(value: complex):
    if not math.isfinite(value.real) or not math.isfinite(value.imag):
        raise ValueError("non-finite complex cannot enter exact finite recognition")
    if value.imag != 0.0:
        return None
    return Rational(value.real)


def register_phase2_recognizers(conversions: ConversionRegistry | None = None) -> None:
    """Idempotently install Phase-2 built-in/Rational finite exact bridges."""

    global _SUBDOMAINS_REGISTERED
    if not _SUBDOMAINS_REGISTERED:
        SUBDOMAINS.register_rational(int, lambda x: Rational(int(x)))
        SUBDOMAINS.register_rational(bool, lambda x: Rational(int(x)))
        SUBDOMAINS.register_rational(Fraction, Rational)
        SUBDOMAINS.register_rational(float, Rational)
        SUBDOMAINS.register_rational(complex, _recognize_complex_rational)
        SUBDOMAINS.register_rational(Rational, Rational)

        SUBDOMAINS.register_integer(int, int)
        SUBDOMAINS.register_integer(bool, int)
        SUBDOMAINS.register_integer(Fraction, _recognize_fraction_integer)
        SUBDOMAINS.register_integer(float, _recognize_float_integer)
        SUBDOMAINS.register_integer(complex, _recognize_complex_integer)
        SUBDOMAINS.register_integer(Rational, _recognize_rational_integer)
        _SUBDOMAINS_REGISTERED = True

    if conversions is not None:
        for source in (int, bool, Fraction, float, Rational):
            if conversions.get(source, Rational) is None:
                conversions.register(source, Rational, Rational)

"""Reproducible Phase-2 Rational benchmark family.

The default mode is a quick smoke run.  Pass ``--full`` to increase chain
lengths substantially while preserving the same deterministic workloads.
Times are diagnostic performance evidence, not correctness evidence.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from fractions import Fraction

from computable import Rational

BIT_SIZES = (32, 128, 512, 2048, 8192)


def timed(fn):
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def nonzero_odd(rng: random.Random, bits: int) -> int:
    return (rng.getrandbits(bits) | 1) or 1


def make_pairs(rng: random.Random, bits: int, count: int):
    out = []
    for _ in range(count):
        a = rng.getrandbits(bits)
        if rng.randrange(2):
            a = -a
        b = nonzero_odd(rng, bits)
        out.append((a, b))
    return out


def lazy_add(pairs):
    x = Rational._new_working(0, 1, simplified=True)
    for a, b in pairs:
        x += Rational(a, b)
    x.simplify()


def eager_add(pairs):
    x = Fraction(0, 1)
    for a, b in pairs:
        x += Fraction(a, b)


def gcd_add(pairs):
    n, d = 0, 1
    for a, b in pairs:
        g = math.gcd(d, b)
        left = b // g
        right = d // g
        n = n * left + a * right
        d *= left
        g2 = math.gcd(n, g)
        n //= g2
        d //= g2
    Fraction(n, d)


def lazy_mul(pairs):
    x = Rational._new_working(1, 1, simplified=True)
    for a, b in pairs:
        if a == 0:
            a = 1
        x *= Rational(a, b)
    x.simplify()


def eager_mul(pairs):
    x = Fraction(1, 1)
    for a, b in pairs:
        x *= Fraction(a or 1, b)


def cross_cancel_mul(pairs):
    n, d = 1, 1
    for a, b in pairs:
        a = a or 1
        g1 = math.gcd(abs(a), d)
        g2 = math.gcd(b, abs(n))
        n = (n // g2) * (a // g1)
        d = (d // g1) * (b // g2)
    Fraction(n, d)


def high_cancellation(bits: int, count: int):
    p = (1 << bits) - 159
    q = (1 << bits) - 313
    x = Rational._new_working(1, 1, simplified=True)
    for _ in range(count):
        x *= Rational(p, q)
        x *= Rational(q, p)
    x.simplify()


def shared_denominator(bits: int, count: int):
    rng = random.Random(7000 + bits)
    d = nonzero_odd(rng, bits)
    x = Rational._new_working(0, 1, simplified=True)
    for _ in range(count):
        x += Rational(rng.getrandbits(bits), d)
    x.simplify()


def bulk_sum(bits: int, count: int):
    rng = random.Random(8000 + bits)
    Rational._sum_integer_ratios(make_pairs(rng, bits, count)).simplify()


def bulk_product(bits: int, count: int):
    rng = random.Random(9000 + bits)
    Rational._product_integer_ratios(make_pairs(rng, bits, count)).simplify()


def run(full: bool) -> dict:
    chain = 64 if full else 8
    bulk = 256 if full else 24
    cancel = 128 if full else 12
    rows = []
    for bits in BIT_SIZES:
        rng = random.Random(1000 + bits)
        pairs = make_pairs(rng, bits, chain)
        row = {
            "bits": bits,
            "add_lazy_s": timed(lambda: lazy_add(pairs)),
            "add_eager_fraction_s": timed(lambda: eager_add(pairs)),
            "add_gcd_s": timed(lambda: gcd_add(pairs)),
            "mul_lazy_s": timed(lambda: lazy_mul(pairs)),
            "mul_eager_fraction_s": timed(lambda: eager_mul(pairs)),
            "mul_cross_cancel_s": timed(lambda: cross_cancel_mul(pairs)),
            "high_cancellation_s": timed(lambda: high_cancellation(bits, cancel)),
            "shared_denominator_s": timed(lambda: shared_denominator(bits, bulk)),
            "bulk_sum_s": timed(lambda: bulk_sum(bits, bulk)),
            "bulk_product_s": timed(lambda: bulk_product(bits, bulk)),
        }
        rows.append(row)
    return {"mode": "full" if full else "smoke", "chain_length": chain, "bulk_length": bulk, "cancellation_pairs": cancel, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.full), indent=2, sort_keys=True))

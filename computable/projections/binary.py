"""Exact finite-output binary64 projection helpers."""
from __future__ import annotations
import struct

T64=(1<<1024)-(1<<970)

def _round_ratio_to_int_ties_even(numerator:int,denominator:int)->int:
    q,r=divmod(numerator,denominator)
    twice=r<<1
    if twice>denominator or (twice==denominator and (q&1)):q+=1
    return q

def _floor_log2_ratio(p:int,q:int)->int:
    e=p.bit_length()-q.bit_length()
    if e>=0:
        if p < (q<<e):e-=1
    elif (p<<(-e)) < q:e-=1
    return e

def rational_to_binary64(numerator:int,denominator:int)->float:
    """Correctly round a finite rational to a finite IEEE-754 binary64 value.

    No machine floating arithmetic participates in the rounding decision.
    ``OverflowError`` is raised exactly at/above the Python exact-number
    boundary ``T64 = 2**1024 - 2**970``.
    """
    if denominator<=0:raise ValueError("denominator must be positive")
    if numerator==0:return 0.0
    sign=1 if numerator<0 else 0
    p=-numerator if numerator<0 else numerator
    if p >= T64*denominator:raise OverflowError("Rational too large to convert to finite binary64")
    e=_floor_log2_ratio(p,denominator)
    if e < -1022:
        m=_round_ratio_to_int_ties_even(p<<1074,denominator)
        if m==0:bits=sign<<63
        elif m < (1<<52):bits=(sign<<63)|m
        else:bits=(sign<<63)|(1<<52)  # minimum normal after subnormal rounding
    else:
        shift=52-e
        if shift>=0:m=_round_ratio_to_int_ties_even(p<<shift,denominator)
        else:m=_round_ratio_to_int_ties_even(p,denominator<<(-shift))
        if m==(1<<53):
            m>>=1;e+=1
        exponent=e+1023
        fraction=m-(1<<52)
        bits=(sign<<63)|(exponent<<52)|fraction
    return struct.unpack('>d',struct.pack('>Q',bits))[0]

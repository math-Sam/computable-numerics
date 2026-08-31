"""Reproducible Phase-2 Rational benchmark family.

Default is a quick smoke run. Pass ``--full`` for the complete longer workload.
Times are diagnostic performance evidence, never correctness evidence.
"""
from __future__ import annotations
import argparse,json,math,random,sys,time
from pathlib import Path
from fractions import Fraction

# Allow direct execution from a source checkout without requiring installation.
if __package__ in (None, ""):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from computable import Rational
from computable.core.promotion import SUBDOMAINS
BIT_SIZES=(32,128,512,2048,8192)
def timed(fn):
    start=time.perf_counter();fn();return time.perf_counter()-start
def nonzero_odd(rng,bits):return (rng.getrandbits(bits)|1) or 1
def make_pairs(rng,bits,count):
    out=[]
    for _ in range(count):
        a=rng.getrandbits(bits)
        if rng.randrange(2):a=-a
        out.append((a,nonzero_odd(rng,bits)))
    return out
def lazy_add(pairs):
    x=Rational._new_working_canonical(0,1)
    for a,b in pairs:x+=Rational(a,b)
    x.simplify()
def eager_add(pairs):
    x=Fraction(0,1)
    for a,b in pairs:x+=Fraction(a,b)
def gcd_add(pairs):
    n,d=0,1
    for a,b in pairs:
        g=math.gcd(d,b);left=b//g;right=d//g;n=n*left+a*right;d*=left;g2=math.gcd(n,g);n//=g2;d//=g2
    Fraction(n,d)
def lazy_mul(pairs):
    x=Rational._new_working_canonical(1,1)
    for a,b in pairs:x*=Rational(a or 1,b)
    x.simplify()
def eager_mul(pairs):
    x=Fraction(1,1)
    for a,b in pairs:x*=Fraction(a or 1,b)
def cross_cancel_mul(pairs):
    n,d=1,1
    for a,b in pairs:
        a=a or 1;g1=math.gcd(abs(a),d);g2=math.gcd(b,abs(n));n=(n//g2)*(a//g1);d=(d//g1)*(b//g2)
    Fraction(n,d)
def high_cancellation(bits,count):
    p=(1<<bits)-159;q=(1<<bits)-313;x=Rational._new_working_canonical(1,1)
    for _ in range(count):x*=Rational(p,q);x*=Rational(q,p)
    x.simplify()
def shared_denominator(bits,count):
    rng=random.Random(7000+bits);d=nonzero_odd(rng,bits);x=Rational._new_working_canonical(0,1)
    for _ in range(count):x+=Rational(rng.getrandbits(bits),d)
    x.simplify()
def bulk_sum(bits,count):
    rng=random.Random(8000+bits);Rational._sum_integer_ratios(make_pairs(rng,bits,count)).simplify()
def bulk_product(bits,count):
    rng=random.Random(9000+bits);Rational._product_integer_ratios(make_pairs(rng,bits,count)).simplify()
def hot_path_diagnostics(iterations):
    a=Rational(17,19);one=Rational(1);w=a.__copy__()
    def inplace_loop():
        nonlocal w
        for _ in range(iterations):w+=one;w-=one
    def integer_recognition_loop():
        for _ in range(iterations):SUBDOMAINS.recognize_integer_value(123456789)
    return {"mutable_inplace_pair_s":timed(inplace_loop),"integer_recognition_s":timed(integer_recognition_loop)}
def run(full):
    chain=64 if full else 8;bulk=256 if full else 24;cancel=128 if full else 12
    rows=[]
    for bits in BIT_SIZES:
        rng=random.Random(1000+bits);pairs=make_pairs(rng,bits,chain)
        rows.append({"bits":bits,"add_lazy_s":timed(lambda:lazy_add(pairs)),"add_eager_fraction_s":timed(lambda:eager_add(pairs)),"add_gcd_s":timed(lambda:gcd_add(pairs)),"mul_lazy_s":timed(lambda:lazy_mul(pairs)),"mul_eager_fraction_s":timed(lambda:eager_mul(pairs)),"mul_cross_cancel_s":timed(lambda:cross_cancel_mul(pairs)),"high_cancellation_s":timed(lambda:high_cancellation(bits,cancel)),"shared_denominator_s":timed(lambda:shared_denominator(bits,bulk)),"bulk_sum_s":timed(lambda:bulk_sum(bits,bulk)),"bulk_product_s":timed(lambda:bulk_product(bits,bulk))})
    return {"mode":"full" if full else "smoke","chain_length":chain,"bulk_length":bulk,"cancellation_pairs":cancel,"hot_path_diagnostics":hot_path_diagnostics(100000 if full else 10000),"rows":rows}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');args=parser.parse_args();print(json.dumps(run(args.full),indent=2,sort_keys=True))

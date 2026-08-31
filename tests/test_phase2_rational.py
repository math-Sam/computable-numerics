"""Roadmap Phase-2 Rational conformance, exactness, and hot-path tests."""
from __future__ import annotations
import copy
import gc
import math
import random
import sys
import unittest
import weakref
from fractions import Fraction
from unittest.mock import patch
from computable import DecisionProcess,Pending,Rational
from computable.core.promotion import ExactSubdomainRegistry,SUBDOMAINS
from computable.projections.binary import T64

class TestConstruction(unittest.TestCase):
    def test_basic_inputs(self):
        self.assertEqual(Rational(3),Rational(3,1));self.assertEqual(Rational(False),Rational(0));self.assertEqual(Rational(True),Rational(1))
        self.assertEqual(Rational(Fraction(-6,8)),Rational(-3,4));self.assertEqual(Rational(0.1),Rational(*0.1.as_integer_ratio()));self.assertNotEqual(Rational(0.1),Rational('0.1'))
        self.assertEqual(Rational(complex(1.5,-0.0)),Rational(3,2));self.assertEqual(Rational(1,-2),Rational(-1,2))
    def test_arity_and_unsupported_type_errors(self):
        with self.assertRaises(TypeError):Rational()
        with self.assertRaises(TypeError):Rational(1,2,3)
        with self.assertRaises(TypeError):Rational(object())
    def test_nonreal_and_nonfinite(self):
        with self.assertRaises(TypeError):Rational(complex(1,1))
        for x in (float('inf'),float('-inf'),float('nan'),complex(float('inf'),0),complex(0,float('nan'))):
            with self.subTest(x=x),self.assertRaises(ValueError):Rational(x)
    def test_string_grammar(self):
        cases={'12':Rational(12),'-3.25':Rational(-13,4),'.5':Rational(1,2),'1.':Rational(1),'2.5e-3':Rational(1,400),'+1.5 / -0.5':Rational(-3)}
        for s,v in cases.items():self.assertEqual(Rational(s),v)
        for s in ('','1 2','1 .0','1e','e2','1/2/3','inf','nan','.'):
            with self.subTest(s=s),self.assertRaises(ValueError):Rational(s)
        with self.assertRaises(ZeroDivisionError):Rational('1/0')
    def test_recursive_tuple_and_two_arg(self):
        self.assertEqual(Rational((1,2)),Rational(1,2));self.assertEqual(Rational((1,2),(3,4)),Rational(2,3));self.assertEqual(Rational(((1,2),(3,4))),Rational(2,3));self.assertEqual(Rational('1/2',Fraction(3,4)),Rational(2,3))
        with self.assertRaises(TypeError):Rational((1,2,3))
        with self.assertRaises(ZeroDivisionError):Rational((1,(False,True)))
    def test_mutable_input_constructor_no_side_effect(self):
        source=copy.copy(Rational(1,1));source+=Rational(1,1)
        self.assertEqual((source._numerator,source._denominator),(2,1))
        source._numerator=4;source._denominator=2;source._is_simplified=False
        before=(source._numerator,source._denominator,source._is_simplified,source._is_frozen)
        out=Rational(source);self.assertEqual(out,Rational(2));self.assertEqual((source._numerator,source._denominator,source._is_simplified,source._is_frozen),before)

class TestConstructionTopology(unittest.TestCase):
    def test_public_factory_does_not_occupy_instance_new(self):
        self.assertNotIn('__new__',Rational.__dict__)
        self.assertIs(Rational.__new__,object.__new__)
        self.assertIsNot(type(Rational).__call__,type.__call__)
    def test_known_canonical_constructor_does_not_reprove_gcd(self):
        value=Fraction(1000000007,1000000009)
        with patch('computable.rational.math.gcd',side_effect=AssertionError('unexpected gcd')):
            r=Rational(value)
        self.assertEqual(r,Rational(value.numerator,value.denominator))
    def test_raw_cache_hit_precedes_gcd(self):
        canonical=Rational(1000003,1000033)
        working=copy.copy(canonical)
        working._is_simplified=False  # conservative unknown, raw pair is still canonical
        with patch('computable.rational.math.gcd',side_effect=AssertionError('cache hit should avoid gcd')):
            result=Rational(working)
        self.assertIs(result,canonical)
    def test_known_canonical_working_path_does_not_gcd(self):
        c=copy.copy(Rational(23,29))
        with patch('computable.rational.math.gcd',side_effect=AssertionError('unexpected gcd')):
            w=Rational._new_working_canonical(17,19)
            n=-c;a=abs(c)
        self.assertEqual(w,Rational(17,19));self.assertEqual(n,Rational(-23,29));self.assertEqual(a,Rational(23,29))
    def test_hash_reuses_live_canonical_hash(self):
        canonical=Rational(1000037,1000039)
        w=Rational._new_working_canonical(canonical._numerator,canonical._denominator)
        self.assertIsNone(w._hash)
        with patch('computable.rational._hash_integer_ratio',side_effect=AssertionError('recomputed live canonical hash')):
            h=hash(w)
        self.assertEqual(h,hash(canonical));self.assertTrue(w._is_frozen)
    def test_bounded_helpers_reuse_reduced_representation(self):
        x=Rational(355,113)
        with patch('math.gcd',side_effect=AssertionError('reproved reduced input gcd')):
            left,right=x._bounded_denominator_bracket(100)
        self.assertLessEqual(left,x);self.assertGreaterEqual(right,x)

class TestLifecycle(unittest.TestCase):
    def test_constructor_frozen_copy_mutable(self):
        r=Rational(2,4);self.assertTrue(r._is_frozen);self.assertEqual((r.numerator,r.denominator),(1,2))
        w=copy.copy(r);self.assertIsNot(w,r);self.assertFalse(w._is_frozen);self.assertEqual(w,r)
        self.assertEqual((w._numerator,w._denominator,w._is_simplified),(1,2,True))
        self.assertEqual(w._hash,r._hash)
    def test_lazy_simplify_and_property_read(self):
        w=copy.copy(Rational(1));w._numerator=8;w._denominator=12;w._is_simplified=False;w._hash=None
        self.assertIsNone(w.simplify());self.assertEqual((w._numerator,w._denominator),(2,3));self.assertFalse(w._is_frozen);self.assertTrue(w._is_simplified)
        frozen=Rational(5,7);before=(frozen._numerator,frozen._denominator,frozen._hash)
        self.assertIsNone(frozen.simplify());self.assertEqual((frozen._numerator,frozen._denominator,frozen._hash),before)
    def test_bool_handles_unreduced_zero(self):
        w=copy.copy(Rational(0));w._numerator=0;w._denominator=999;w._is_simplified=False;w._hash=None
        self.assertFalse(bool(w));self.assertEqual((w._numerator,w._denominator),(0,999))
    def test_noninplace_does_not_mutate_operands(self):
        a=copy.copy(Rational(2,3));b=copy.copy(Rational(5,7));before_a=(a._numerator,a._denominator,a._is_simplified,a._is_frozen);before_b=(b._numerator,b._denominator,b._is_simplified,b._is_frozen)
        result=a+b
        self.assertIsNot(result,a);self.assertIsNot(result,b);self.assertFalse(result._is_frozen);self.assertEqual(a,Rational(2,3));self.assertEqual(b,Rational(5,7));self.assertEqual((a._numerator,a._denominator,a._is_simplified,a._is_frozen),before_a);self.assertEqual((b._numerator,b._denominator,b._is_simplified,b._is_frozen),before_b)
    def test_inplace_mutable_and_frozen(self):
        frozen=Rational(1,2);alias=frozen;frozen+=Rational(1,2);self.assertIs(alias,Rational(1,2));self.assertIsNot(frozen,alias);self.assertFalse(frozen._is_frozen);self.assertEqual(frozen,Rational(1))
        w=copy.copy(Rational(1,2));ident=id(w);w+=Rational(1,2);self.assertEqual(id(w),ident);self.assertEqual(w,Rational(1));self.assertFalse(w._is_frozen)
    def test_mutable_inplace_allocates_no_rational_result(self):
        w=copy.copy(Rational(1,3));other=Rational(1,5);ident=id(w)
        original=Rational._allocate_working
        with patch.object(Rational,'_allocate_working',side_effect=AssertionError('mutable inplace allocated')):
            w+=other
        self.assertEqual(id(w),ident);self.assertEqual(w,Rational(8,15))
        # Frozen path must instead produce a fresh mutable object.
        f=Rational(1,3)
        with patch.object(Rational,'_allocate_working',wraps=original) as allocator:
            f2=f.__iadd__(other)
        self.assertEqual(allocator.call_count,1);self.assertIsNot(f2,f);self.assertFalse(f2._is_frozen)
    def test_setters_value_level_and_transactional(self):
        w=copy.copy(Rational(1));w._numerator=4;w._denominator=4;w._is_simplified=False;w._hash=None;w.numerator=2;self.assertEqual(w,Rational(2))
        w=copy.copy(Rational(3,5));w.numerator=Fraction(2,3);self.assertEqual(w,Rational(2,15))
        w=copy.copy(Rational(3,5));w.denominator=Fraction(-2,3);self.assertEqual(w,Rational(-9,2));self.assertGreater(w._denominator,0)
        # Setter semantics depend on canonical coordinates, not the raw working pair.
        a=copy.copy(Rational(3,5));b=copy.copy(Rational(3,5));b._numerator=6;b._denominator=10;b._is_simplified=False;b._hash=None
        a.denominator=Fraction(7,11);b.denominator=Fraction(7,11);self.assertEqual(a,Rational(33,7));self.assertEqual(b,a)
        before=(w._numerator,w._denominator,w._is_simplified)
        with self.assertRaises(ZeroDivisionError):w.denominator=(False,True)
        self.assertEqual((w._numerator,w._denominator,w._is_simplified),before)
        f=Rational(1,2)
        with self.assertRaises(ValueError):f.denominator='not even parsed'
    def test_hash_freezes_same_object_and_compatible(self):
        w=copy.copy(Rational(1,3));ident=id(w);h=hash(w);self.assertEqual(id(w),ident);self.assertTrue(w._is_frozen);self.assertEqual(h,hash(Fraction(1,3)))
        with self.assertRaises(ValueError):w.numerator=2
        fixtures=[Rational(1),Rational(1,2),Rational(-7,8),Rational(float.fromhex('0x0.0000000000001p-1022')),Rational(10**100)]
        for r in fixtures:
            f=Fraction(r.numerator,r.denominator);self.assertEqual(hash(r),hash(f))
            try:x=float(f)
            except OverflowError:continue
            if Fraction(*x.as_integer_ratio())==f:self.assertEqual(hash(r),hash(x))
        self.assertEqual(hash(Rational(1)),hash(True));self.assertEqual(hash(Rational(0)),hash(False));self.assertEqual(hash(Rational(1)),hash(complex(1,0)));self.assertEqual(hash(Rational(1,2)),hash(complex(0.5,0)))
    def test_dict_and_set_hashing_freezes_working_value(self):
        w=copy.copy(Rational(11,13));d={w:'value'};self.assertTrue(w._is_frozen);self.assertEqual(d[Rational(11,13)],'value')
        u=copy.copy(Rational(-5,9));s={u};self.assertTrue(u._is_frozen);self.assertIn(Rational(-5,9),s)
    def test_intern_cache_hit_and_weakness(self):
        canonical=Rational(17,19);w=copy.copy(canonical);got=w.intern();self.assertIs(got,canonical);self.assertFalse(w._is_frozen);self.assertTrue(w._is_simplified)
        unique=Rational(123456789123456789,9876543211);key=(unique.numerator,unique.denominator);ref=weakref.ref(unique);del unique;gc.collect();self.assertIsNone(ref());self.assertNotIn(key,Rational._cache)
        w=Rational._new_working_raw(999999937,999999929);self.assertNotIn((999999937,999999929),Rational._cache);self.assertIs(w.intern(),w);self.assertTrue(w._is_frozen)

class TestArithmeticAndRecognition(unittest.TestCase):
    def test_field_identities(self):
        rng=random.Random(12345)
        for _ in range(500):
            a=Rational(rng.randint(-1000,1000),rng.randint(1,1000));b=Rational(rng.randint(-1000,1000),rng.randint(1,1000));c=Rational(rng.randint(-1000,1000),rng.randint(1,1000));af=Fraction(a.numerator,a.denominator);bf=Fraction(b.numerator,b.denominator)
            apb=a+b;amb=a-b;atb=a*b
            self.assertEqual(Fraction(apb.numerator,apb.denominator),af+bf);self.assertEqual(Fraction(amb.numerator,amb.denominator),af-bf);self.assertEqual(Fraction(atb.numerator,atb.denominator),af*bf)
            if b:
                adb=a/b;self.assertEqual(Fraction(adb.numerator,adb.denominator),af/bf)
            self.assertEqual((a+b)-b,a);self.assertEqual(a*(b+c),a*b+a*c)
            if b:self.assertEqual((a*b)/b,a)
    def test_builtin_scalar_exactness(self):
        self.assertEqual(Rational(1,2)+Fraction(1,3),Rational(5,6));self.assertEqual(Rational(1,2)+0.25,Rational(3,4));self.assertTrue(Rational(1)==True);self.assertTrue(True==Rational(1));self.assertTrue(complex(1,0)==Rational(1));self.assertFalse(Rational(1)==complex(1,1))
        with self.assertRaises(TypeError):_ = Rational(1)+"2"
        with self.assertRaises(TypeError):_ = Rational(1)+(2,1)
        with self.assertRaises(NotImplementedError):_ = Rational(1)+complex(2,0)
    def test_integer_recognizer_and_power(self):
        reps=[2,2.0,Fraction(2,1),complex(2,0),Rational(2)]
        for e in reps:self.assertEqual(Rational(3,2)**e,Rational(9,4))
        self.assertEqual(Rational(0)**0,Rational(1));self.assertEqual(Rational(2)**-2,Rational(1,4))
        with self.assertRaises(ZeroDivisionError):Rational(0)**-1
        for e in (1.5,Fraction(3,2),complex(2,1)):
            with self.assertRaises(TypeError):Rational(2)**e
    def test_direct_integer_recognizer_avoids_rational_materialization(self):
        registry=ExactSubdomainRegistry()
        registry.register_rational(int,lambda value:(_ for _ in ()).throw(AssertionError('materialized Rational')))
        registry.register_integer(int,int)
        self.assertEqual(registry.recognize_integer_value(7),7)
        w=Rational._new_working_raw(20,10)
        self.assertFalse(w._is_simplified)
        self.assertEqual(SUBDOMAINS.recognize_integer_value(w),2)
        self.assertFalse(w._is_simplified)  # recognition preserves working representation
        for v,expected in [(True,1),(2.0,2),(Fraction(-3,1),-3),(complex(4,-0.0),4)]:self.assertEqual(SUBDOMAINS.recognize_integer_value(v),expected)
        for v in (1.5,Fraction(3,2),complex(1,2),Rational(3,2)):self.assertIsNone(SUBDOMAINS.recognize_integer_value(v))
    def test_decision_work_shared_recognizer(self):
        for value,steps in [(False,0),(0.0,0),(Rational(0),0),(True,1),(1.0,1),(Fraction(1,1),1),(complex(1,0),1),(Rational(1),1)]:
            calls=0
            def step():
                nonlocal calls;calls+=1;return Pending()
            p=DecisionProcess(step);p.advance(work=value);self.assertEqual(calls,steps)
        with self.assertRaises(TypeError):DecisionProcess(lambda:Pending()).advance(work=Fraction(1,2))
        with self.assertRaises(ValueError):DecisionProcess(lambda:Pending()).advance(work=Rational(-1))

class TestIntegerAndRounding(unittest.TestCase):
    def test_int_floor_ceil_round(self):
        self.assertEqual(int(Rational(-7,3)),-2);self.assertEqual(math.floor(Rational(-7,3)),-3);self.assertEqual(math.ceil(Rational(-7,3)),-2)
        self.assertEqual(round(Rational(5,2)),2);self.assertEqual(round(Rational(7,2)),4);self.assertEqual(round(Rational(-5,2)),-2);self.assertEqual(round(Rational(-7,2)),-4)
        self.assertEqual(round(Rational(12345,1000),2),Rational(617,50));self.assertEqual(round(Rational(125,1),-1),Rational(120));self.assertEqual(round(Rational(135,1),-1),Rational(140))
        for n in (2.0,Fraction(2,1),complex(2,0),Rational(2)):self.assertEqual(round(Rational(12345,1000),n),Rational(617,50))

class TestProjection(unittest.TestCase):
    def test_binary64_matches_fraction_oracle(self):
        rng=random.Random(911)
        for _ in range(5000):
            n=rng.getrandbits(rng.randint(0,1100))*(-1 if rng.randrange(2) else 1);d=rng.getrandbits(rng.randint(1,1100)) or 1;r=Rational(n,d);f=Fraction(n,d)
            try:expected=float(f)
            except OverflowError:
                with self.assertRaises(OverflowError):float(r)
            else:self.assertEqual(float(r).hex(),expected.hex())
    def test_exact_overflow_boundary_and_underflow(self):
        self.assertEqual(float(Rational(T64-1)),sys.float_info.max);self.assertEqual(float(Rational(-T64+1)),-sys.float_info.max)
        for n in (T64,T64+1,-T64,-T64-1):
            with self.assertRaises(OverflowError):float(Rational(n))
        self.assertEqual(float(Rational(1,1<<1075)),0.0);self.assertEqual(complex(Rational(1,2)),complex(0.5,0.0))

class TestPrivateHelpers(unittest.TestCase):
    def test_integer_nth_root(self):
        self.assertEqual(Rational._integer_nth_root(0,7),(0,True));self.assertEqual(Rational._integer_nth_root(2**100,10),(1024,True));self.assertEqual(Rational._integer_nth_root(17,2),(4,False))
    def test_bounded_denominator_helpers(self):
        x=Rational(7,13);l,r=x._bounded_denominator_bracket(5);self.assertLessEqual(l,x);self.assertGreaterEqual(r,x);self.assertLessEqual(l.denominator,5);self.assertLessEqual(r.denominator,5)
        near=x._nearest_bounded_denominator(5);candidates={Fraction(p,q) for q in range(1,6) for p in range(-10,11)};best=min(abs(c-Fraction(7,13)) for c in candidates);self.assertEqual(abs(Fraction(near.numerator,near.denominator)-Fraction(7,13)),best)
    def test_bulk_helpers(self):
        vals=[(1,2),(1,3),(1,6)];self.assertEqual(Rational._sum_integer_ratios(vals),Rational(1));self.assertEqual(Rational._product_integer_ratios(vals),Rational(1,36))
if __name__=='__main__':unittest.main()

"""Roadmap Phase-2 Rational conformance and exactness tests."""
from __future__ import annotations
import copy,gc,math,random,sys,unittest,weakref
from fractions import Fraction
from computable import DecisionProcess,Pending,Rational
from computable.core.promotion import SUBDOMAINS
from computable.projections.binary import T64

class TestConstruction(unittest.TestCase):
    def test_basic_inputs(self):
        self.assertEqual(Rational(3),Rational(3,1));self.assertEqual(Rational(False),Rational(0));self.assertEqual(Rational(True),Rational(1))
        self.assertEqual(Rational(Fraction(-6,8)),Rational(-3,4));self.assertEqual(Rational(0.1),Rational(*0.1.as_integer_ratio()));self.assertNotEqual(Rational(0.1),Rational('0.1'))
        self.assertEqual(Rational(complex(1.5,-0.0)),Rational(3,2));self.assertEqual(Rational(1,-2),Rational(-1,2))
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

class TestLifecycle(unittest.TestCase):
    def test_constructor_frozen_copy_mutable(self):
        r=Rational(2,4);self.assertTrue(r._is_frozen);self.assertEqual((r.numerator,r.denominator),(1,2))
        w=copy.copy(r);self.assertIsNot(w,r);self.assertFalse(w._is_frozen);self.assertEqual(w,r)
    def test_lazy_simplify_and_property_read(self):
        w=copy.copy(Rational(1));w._numerator=8;w._denominator=12;w._is_simplified=False
        self.assertEqual(w.numerator,2);self.assertEqual(w.denominator,3);self.assertFalse(w._is_frozen);self.assertTrue(w._is_simplified)
    def test_inplace_mutable_and_frozen(self):
        frozen=Rational(1,2);alias=frozen;frozen+=Rational(1,2);self.assertIs(alias,Rational(1,2));self.assertIsNot(frozen,alias);self.assertFalse(frozen._is_frozen);self.assertEqual(frozen,Rational(1))
        w=copy.copy(Rational(1,2));ident=id(w);w+=Rational(1,2);self.assertEqual(id(w),ident);self.assertEqual(w,Rational(1));self.assertFalse(w._is_frozen)
    def test_setters_value_level_and_transactional(self):
        w=copy.copy(Rational(1));w._numerator=4;w._denominator=4;w._is_simplified=False;w.numerator=2;self.assertEqual(w,Rational(2))
        w=copy.copy(Rational(3,5));w.denominator=Fraction(-2,3);self.assertEqual(w,Rational(-9,10));self.assertGreater(w._denominator,0)
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
    def test_intern_cache_hit_and_weakness(self):
        canonical=Rational(17,19);w=copy.copy(canonical);got=w.intern();self.assertIs(got,canonical);self.assertFalse(w._is_frozen);self.assertTrue(w._is_simplified)
        unique=Rational(123456789123456789,9876543211);key=(unique.numerator,unique.denominator);ref=weakref.ref(unique);del unique;gc.collect();self.assertIsNone(ref());self.assertNotIn(key,Rational._cache)
        w=Rational._new_working(999999937,999999929);self.assertNotIn((999999937,999999929),Rational._cache);self.assertIs(w.intern(),w);self.assertTrue(w._is_frozen)

class TestArithmeticAndRecognition(unittest.TestCase):
    def test_field_identities(self):
        rng=random.Random(12345)
        for _ in range(500):
            a=Rational(rng.randint(-1000,1000),rng.randint(1,1000));b=Rational(rng.randint(-1000,1000),rng.randint(1,1000));c=Rational(rng.randint(-1000,1000),rng.randint(1,1000))
            af=Fraction(a.numerator,a.denominator);bf=Fraction(b.numerator,b.denominator)
            self.assertEqual(Fraction((a+b).numerator,(a+b).denominator),af+bf)
            self.assertEqual(Fraction((a-b).numerator,(a-b).denominator),af-bf)
            self.assertEqual(Fraction((a*b).numerator,(a*b).denominator),af*bf)
            if b:self.assertEqual(Fraction((a/b).numerator,(a/b).denominator),af/bf)
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

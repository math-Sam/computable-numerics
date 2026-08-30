"""Finite exact rational substrate for :mod:`computable`.

``Rational`` denotes exactly Q.  Public construction is canonical/frozen and
weak-interned; arithmetic produces mutable working values that may postpone gcd
reduction until a canonical boundary is requested.
"""
from __future__ import annotations

import math
import re
import sys
from fractions import Fraction
from typing import ClassVar
from weakref import WeakValueDictionary

from .core.family import NumericFamily
from .core.kinds import NumericKind
from .core.promotion import SUBDOMAINS, ConversionRegistry
from .projections.binary import rational_to_binary64
from ._rational_helpers import (
    bounded_denominator_bracket,
    integer_nth_root,
    nearest_bounded_denominator,
    product_integer_ratios,
    sum_integer_ratios,
)

_SCALAR_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")
_SUBDOMAINS_REGISTERED=False


def _canonical_pair(n:int,d:int)->tuple[int,int]:
    if d==0:raise ZeroDivisionError("rational denominator is zero")
    if d<0:n,d=-n,-d
    if n==0:return 0,1
    g=math.gcd(n,d)
    return n//g,d//g


def _hash_integer_ratio(n:int,d:int)->int:
    """Python numeric hash for a reduced integer ratio, without float conversion."""
    modulus=sys.hash_info.modulus
    try:inverse=pow(d,-1,modulus)
    except ValueError:value=sys.hash_info.inf
    else:value=(abs(n)%modulus)*inverse%modulus
    if n<0:value=-value
    return -2 if value==-1 else value


def _parse_decimal_scalar(text:str)->tuple[int,int]:
    if not _SCALAR_RE.fullmatch(text):raise ValueError(f"invalid Rational string scalar: {text!r}")
    sign=-1 if text.startswith('-') else 1
    if text[:1] in '+-':text=text[1:]
    if 'e' in text.lower():
        mantissa,exp_text=re.split('[eE]',text,maxsplit=1); exponent=int(exp_text)
    else:mantissa=text;exponent=0
    if '.' in mantissa:
        head,tail=mantissa.split('.',1); digits=(head or '0')+tail; scale=len(tail)
    else:digits=mantissa;scale=0
    n=sign*int(digits)
    power=exponent-scale
    if power>=0:return n*(10**power),1
    return _canonical_pair(n,10**(-power))


class Rational:
    """Exact rational value with mutable-working / frozen-canonical lifecycle."""
    _kind:ClassVar[NumericKind]=NumericKind.RATIONAL
    _family:ClassVar[NumericFamily|None]=None
    _cache:ClassVar[WeakValueDictionary[tuple[int,int],"Rational"]]=WeakValueDictionary()
    __slots__=("_numerator","_denominator","_is_simplified","_is_frozen","_hash","__weakref__")

    def __new__(cls,*args):
        if len(args)==1:
            value=args[0]
            if isinstance(value,cls) and value._is_frozen and value._is_simplified:
                cached=cls._cache.get((value._numerator,value._denominator))
                if cached is value:return value
            n,d=cls._parse_input(value)
        elif len(args)==2:
            an,ad=cls._parse_input(args[0]);bn,bd=cls._parse_input(args[1])
            if bn==0:raise ZeroDivisionError("Rational denominator is zero")
            n,d=an*bd,ad*bn
        else:raise TypeError("Rational expects one value or numerator and denominator")
        n,d=_canonical_pair(n,d)
        cached=cls._cache.get((n,d))
        if cached is not None:return cached
        obj=object.__new__(cls)
        object.__setattr__(obj,"_numerator",n);object.__setattr__(obj,"_denominator",d)
        object.__setattr__(obj,"_is_simplified",True);object.__setattr__(obj,"_is_frozen",True)
        object.__setattr__(obj,"_hash",_hash_integer_ratio(n,d))
        cls._cache[(n,d)]=obj
        return obj

    @classmethod
    def _new_working(cls,n:int,d:int,*,simplified:bool=False)->"Rational":
        if d==0:raise ZeroDivisionError("rational denominator is zero")
        if d<0:n,d=-n,-d
        if simplified:n,d=_canonical_pair(n,d)
        obj=object.__new__(cls)
        object.__setattr__(obj,"_numerator",int(n));object.__setattr__(obj,"_denominator",int(d))
        object.__setattr__(obj,"_is_simplified",bool(simplified));object.__setattr__(obj,"_is_frozen",False);object.__setattr__(obj,"_hash",None)
        return obj

    @classmethod
    def _parse_input(cls,value)->tuple[int,int]:
        if isinstance(value,cls):
            # Read raw exact representation without canonicalizing/freezing the input.
            return _canonical_pair(value._numerator,value._denominator)
        if isinstance(value,int):return int(value),1
        if isinstance(value,Fraction):return value.numerator,value.denominator
        if isinstance(value,float):
            if not math.isfinite(value):raise ValueError("non-finite float is not a Rational")
            return value.as_integer_ratio()
        if isinstance(value,complex):
            if not math.isfinite(value.real) or not math.isfinite(value.imag):raise ValueError("non-finite complex is not a Rational")
            if value.imag!=0.0:raise TypeError("complex value is not real and therefore not Rational")
            return value.real.as_integer_ratio()
        if isinstance(value,str):return cls._parse_string(value)
        if isinstance(value,tuple):
            if len(value)!=2:raise TypeError("Rational tuple input must contain exactly two elements")
            an,ad=cls._parse_input(value[0]);bn,bd=cls._parse_input(value[1])
            if bn==0:raise ZeroDivisionError("Rational tuple divisor is zero")
            return _canonical_pair(an*bd,ad*bn)
        recognized=SUBDOMAINS.recognize_rational_value(value)
        if recognized is not None and isinstance(recognized,cls):
            return _canonical_pair(recognized._numerator,recognized._denominator)
        raise TypeError(f"unsupported Rational input type: {type(value).__name__}")

    @classmethod
    def _parse_string(cls,text:str)->tuple[int,int]:
        stripped=text.strip()
        if not stripped:raise ValueError("empty Rational string")
        parts=stripped.split('/')
        if len(parts)>2:raise ValueError(f"invalid Rational string: {text!r}")
        if len(parts)==1:return _parse_decimal_scalar(parts[0])
        left,right=parts[0].strip(),parts[1].strip()
        # Whitespace is allowed only around the slash; scalar grammar rejects it elsewhere.
        if not left or not right:raise ValueError(f"invalid Rational string: {text!r}")
        an,ad=_parse_decimal_scalar(left);bn,bd=_parse_decimal_scalar(right)
        if bn==0:raise ZeroDivisionError("Rational string divisor is zero")
        return _canonical_pair(an*bd,ad*bn)

    @property
    def numerator(self)->int:
        self.simplify();return self._numerator
    @numerator.setter
    def numerator(self,value)->None:
        if self._is_frozen:raise ValueError("cannot mutate a frozen Rational")
        p,q=type(self)._parse_input(value)  # parse transactionally before touching receiver
        self.simplify();n,d=self._numerator,self._denominator
        object.__setattr__(self,"_numerator",p);object.__setattr__(self,"_denominator",q*d)
        object.__setattr__(self,"_is_simplified",False);object.__setattr__(self,"_hash",None)
    @property
    def denominator(self)->int:
        self.simplify();return self._denominator
    @denominator.setter
    def denominator(self,value)->None:
        if self._is_frozen:raise ValueError("cannot mutate a frozen Rational")
        p,q=type(self)._parse_input(value)
        if p==0:raise ZeroDivisionError("Rational denominator assignment is zero")
        self.simplify();n,d=self._numerator,self._denominator
        new_n=n*q;new_d=d*p
        if new_d<0:new_n,new_d=-new_n,-new_d
        object.__setattr__(self,"_numerator",new_n);object.__setattr__(self,"_denominator",new_d)
        object.__setattr__(self,"_is_simplified",False);object.__setattr__(self,"_hash",None)

    def simplify(self)->None:
        if self._is_simplified:return
        n,d=_canonical_pair(self._numerator,self._denominator)
        object.__setattr__(self,"_numerator",n);object.__setattr__(self,"_denominator",d);object.__setattr__(self,"_is_simplified",True)

    def __copy__(self)->"Rational":
        return type(self)._new_working(self._numerator,self._denominator,simplified=self._is_simplified)

    def intern(self)->"Rational":
        self.simplify();key=(self._numerator,self._denominator);cached=type(self)._cache.get(key)
        if cached is not None:return cached
        h=_hash_integer_ratio(*key)
        object.__setattr__(self,"_hash",h);object.__setattr__(self,"_is_frozen",True);type(self)._cache[key]=self
        return self

    @classmethod
    def _coerce_rational(cls,value):
        if isinstance(value,(str,tuple)):return None
        if isinstance(value,cls):return value._numerator,value._denominator
        if isinstance(value,int):return int(value),1
        if isinstance(value,Fraction):return value.numerator,value.denominator
        if isinstance(value,float):
            if not math.isfinite(value):raise ValueError("non-finite float cannot enter exact Rational arithmetic")
            return value.as_integer_ratio()
        if isinstance(value,complex):
            if not math.isfinite(value.real) or not math.isfinite(value.imag):raise ValueError("non-finite complex cannot enter exact arithmetic")
            if value.imag!=0.0:return None
            return value.real.as_integer_ratio()
        q=SUBDOMAINS.recognize_rational_value(value)
        if isinstance(q,cls):return q._numerator,q._denominator
        return None

    @classmethod
    def _recognized_integer(cls,value)->int:
        n=SUBDOMAINS.recognize_integer_value(value)
        if n is None:raise TypeError("expected a guaranteed-finite exact integer-valued numeric input")
        return n

    def _binary_working(self,other,op):
        if isinstance(other,complex):
            if not math.isfinite(other.real) or not math.isfinite(other.imag):
                raise ValueError("non-finite complex cannot enter exact arithmetic")
            raise NotImplementedError("finite complex arithmetic lifts through GaussianRational in Phase 3")
        pair=type(self)._coerce_rational(other)
        if pair is None:return NotImplemented
        a,b=self._numerator,self._denominator;c,d=pair
        if op=='add':return type(self)._new_working(a*d+c*b,b*d)
        if op=='sub':return type(self)._new_working(a*d-c*b,b*d)
        if op=='mul':return type(self)._new_working(a*c,b*d)
        if c==0:raise ZeroDivisionError("division by zero")
        return type(self)._new_working(a*d,b*c)
    def __add__(self,other):return self._binary_working(other,'add')
    def __sub__(self,other):return self._binary_working(other,'sub')
    def __mul__(self,other):return self._binary_working(other,'mul')
    def __truediv__(self,other):return self._binary_working(other,'div')
    def __radd__(self,other):return self.__add__(other)
    def __rsub__(self,other):
        if isinstance(other,complex):
            if not math.isfinite(other.real) or not math.isfinite(other.imag):raise ValueError("non-finite complex cannot enter exact arithmetic")
            raise NotImplementedError("finite complex arithmetic lifts through GaussianRational in Phase 3")
        pair=type(self)._coerce_rational(other)
        if pair is None:return NotImplemented
        a,b=pair;return type(self)._new_working(a*self._denominator-self._numerator*b,b*self._denominator)
    def __rmul__(self,other):return self.__mul__(other)
    def __rtruediv__(self,other):
        if isinstance(other,complex):
            if not math.isfinite(other.real) or not math.isfinite(other.imag):raise ValueError("non-finite complex cannot enter exact arithmetic")
            raise NotImplementedError("finite complex arithmetic lifts through GaussianRational in Phase 3")
        pair=type(self)._coerce_rational(other)
        if pair is None:return NotImplemented
        if self._numerator==0:raise ZeroDivisionError("division by zero")
        a,b=pair;return type(self)._new_working(a*self._denominator,b*self._numerator)

    def _inplace(self,other,op):
        result=self._binary_working(other,op)
        if result is NotImplemented:return NotImplemented
        if self._is_frozen:return result
        object.__setattr__(self,"_numerator",result._numerator);object.__setattr__(self,"_denominator",result._denominator)
        object.__setattr__(self,"_is_simplified",result._is_simplified);object.__setattr__(self,"_hash",None)
        return self
    def __iadd__(self,other):return self._inplace(other,'add')
    def __isub__(self,other):return self._inplace(other,'sub')
    def __imul__(self,other):return self._inplace(other,'mul')
    def __itruediv__(self,other):return self._inplace(other,'div')

    def __neg__(self):return type(self)._new_working(-self._numerator,self._denominator,simplified=self._is_simplified)
    def __pos__(self):return self.__copy__()
    def __abs__(self):return type(self)._new_working(abs(self._numerator),self._denominator,simplified=self._is_simplified)

    def __pow__(self,exponent,modulo=None):
        if modulo is not None:return NotImplemented
        n=type(self)._recognized_integer(exponent)
        a,b=self._numerator,self._denominator
        if n==0:return type(self)._new_working(1,1,simplified=True)
        if n<0:
            if a==0:raise ZeroDivisionError("zero cannot be raised to a negative power")
            a,b=b,a;n=-n
        return type(self)._new_working(pow(a,n),pow(b,n))

    def __bool__(self)->bool:return self._numerator!=0
    def __int__(self)->int:
        n=self._numerator;d=self._denominator
        return n//d if n>=0 else -((-n)//d)
    def __floor__(self)->int:return self._numerator//self._denominator
    def __ceil__(self)->int:return -((-self._numerator)//self._denominator)
    @staticmethod
    def _round_ratio(n:int,d:int)->int:
        q,r=divmod(n,d);twice=r<<1
        if twice>d or (twice==d and (q&1)):q+=1
        return q
    def __round__(self,ndigits=None):
        if ndigits is None:return self._round_ratio(self._numerator,self._denominator)
        k=type(self)._recognized_integer(ndigits)
        if k>=0:
            scale=10**k;q=self._round_ratio(self._numerator*scale,self._denominator)
            return type(self)._new_working(q,scale)
        scale=10**(-k);q=self._round_ratio(self._numerator,self._denominator*scale)
        return type(self)._new_working(q*scale,1)

    def __float__(self)->float:return rational_to_binary64(self._numerator,self._denominator)
    def __complex__(self)->complex:return complex(float(self),0.0)

    def __eq__(self,other):
        pair=type(self)._coerce_rational(other)
        if pair is None:return False if isinstance(other,(complex,float,int,Fraction)) else NotImplemented
        c,d=pair;return self._numerator*d==c*self._denominator
    def __ne__(self,other):
        result=self.__eq__(other)
        return NotImplemented if result is NotImplemented else not result
    def _compare(self,other,op):
        pair=type(self)._coerce_rational(other)
        if pair is None:
            if isinstance(other,complex):raise TypeError("ordering is undefined for non-real complex values")
            return NotImplemented
        c,d=pair;left=self._numerator*d;right=c*self._denominator
        return {'lt':left<right,'le':left<=right,'gt':left>right,'ge':left>=right}[op]
    def __lt__(self,other):return self._compare(other,'lt')
    def __le__(self,other):return self._compare(other,'le')
    def __gt__(self,other):return self._compare(other,'gt')
    def __ge__(self,other):return self._compare(other,'ge')

    def __hash__(self)->int:
        if self._is_frozen:return self._hash
        self.simplify();h=_hash_integer_ratio(self._numerator,self._denominator)
        object.__setattr__(self,"_hash",h);object.__setattr__(self,"_is_frozen",True)
        key=(self._numerator,self._denominator)
        if type(self)._cache.get(key) is None:type(self)._cache[key]=self
        return h

    def __str__(self)->str:
        self.simplify();return str(self._numerator) if self._denominator==1 else f"{self._numerator}/{self._denominator}"
    def __repr__(self)->str:
        self.simplify();return f"Rational({self._numerator})" if self._denominator==1 else f"Rational({self._numerator}, {self._denominator})"

    # Private Phase-2 helper hooks.  Public grid spelling arrives in Phase 9.
    @staticmethod
    def _integer_nth_root(n:int,degree:int)->tuple[int,bool]:return integer_nth_root(n,degree)
    def _bounded_denominator_bracket(self,max_denominator:int):
        n=type(self)._recognized_integer(max_denominator)
        if n<1:raise ValueError("max_denominator must be positive")
        left,right=bounded_denominator_bracket(self._numerator,self._denominator,n)
        return type(self)._new_working(*left,simplified=True),type(self)._new_working(*right,simplified=True)
    def _nearest_bounded_denominator(self,max_denominator:int):
        n=type(self)._recognized_integer(max_denominator)
        if n<1:raise ValueError("max_denominator must be positive")
        pair=nearest_bounded_denominator(self._numerator,self._denominator,n)
        return type(self)._new_working(*pair,simplified=True)
    @classmethod
    def _sum_integer_ratios(cls,values):
        return cls._new_working(*sum_integer_ratios(values))
    @classmethod
    def _product_integer_ratios(cls,values):
        return cls._new_working(*product_integer_ratios(values))


def register_phase2_recognizers(conversions:ConversionRegistry|None=None)->None:
    """Idempotently install Phase-2 built-in/Rational finite exact bridges."""
    global _SUBDOMAINS_REGISTERED
    if not _SUBDOMAINS_REGISTERED:
        SUBDOMAINS.register_rational(int,lambda x:Rational(int(x)))
        SUBDOMAINS.register_rational(bool,lambda x:Rational(int(x)))
        SUBDOMAINS.register_rational(Fraction,lambda x:Rational(x))
        SUBDOMAINS.register_rational(float,lambda x:Rational(x))
        SUBDOMAINS.register_rational(complex, _recognize_complex_rational)
        SUBDOMAINS.register_rational(Rational,lambda x:Rational(x))
        _SUBDOMAINS_REGISTERED=True
    if conversions is not None:
        for source in (int,bool,Fraction,float,Rational):
            if conversions.get(source,Rational) is None:conversions.register(source,Rational,Rational)

def _recognize_complex_rational(value: complex):
    if not math.isfinite(value.real) or not math.isfinite(value.imag):
        raise ValueError("non-finite complex cannot enter exact finite recognition")
    if value.imag != 0.0:
        return None
    return Rational(value.real)

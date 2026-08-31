"""Private exact integer/rational helpers used by the Phase-2 substrate."""
from __future__ import annotations
def integer_nth_root(n:int,degree:int)->tuple[int,bool]:
    if not isinstance(n,int) or isinstance(n,bool):raise TypeError("n must be an integer")
    if n<0:raise ValueError("n must be non-negative")
    if not isinstance(degree,int) or isinstance(degree,bool):raise TypeError("degree must be an integer")
    if degree<=0:raise ValueError("degree must be positive")
    if n<=1 or degree==1:return n,True
    bit_len=n.bit_length()
    if degree>=bit_len:return 1,False
    x=1<<((bit_len+degree-1)//degree);dm1=degree-1
    while True:
        y=(dm1*x+n//(x**dm1))//degree
        if y>=x:break
        x=y
    return x,(x**degree==n)
def bounded_denominator_bracket(numerator:int,denominator:int,max_denominator:int,*,reduced:bool=False):
    if denominator<=0:raise ValueError("denominator must be positive")
    if max_denominator<1:raise ValueError("max_denominator must be positive")
    if reduced:
        n,d=numerator,denominator
    else:
        import math
        g=math.gcd(numerator,denominator);n=numerator//g;d=denominator//g
    if d<=max_denominator:return (n,d),(n,d)
    shift,left_error=divmod(n,d);right_error=d-left_error
    if left_error==right_error:return (shift,1),(shift+1,1)
    dc=db=1
    if left_error>right_error:nb=shift+1;eb=right_error;nc=shift;ec=left_error;current_left=True
    else:nb=shift;eb=left_error;nc=shift+1;ec=right_error;current_left=False
    while True:
        k,enew=divmod(ec,eb);chosen=dc+k*db
        if chosen>max_denominator:
            k=(max_denominator-dc)//db;dc+=k*db;nc+=k*nb
            return ((nc,dc),(nb,db)) if current_left else ((nb,db),(nc,dc))
        ec,eb=eb,enew;dc,db=db,chosen;nc,nb=nb,nc+k*nb;current_left=not current_left
def nearest_bounded_denominator(numerator:int,denominator:int,max_denominator:int,*,reduced:bool=False):
    left,right=bounded_denominator_bracket(numerator,denominator,max_denominator,reduced=reduced)
    if left==right:return left
    ln,ld=left;rn,rd=right;cmp=2*numerator*ld*rd-denominator*(ln*rd+rn*ld)
    if cmp<0:return left
    if cmp>0:return right
    return left if ld<rd else right
def sum_integer_ratios(values):
    n,d=0,1
    for a,b in values:
        if b<=0:raise ValueError("denominator must be positive")
        if a==0:
            continue
        n=n*b+a*d;d*=b
    return n,d
def product_integer_ratios(values):
    n,d=1,1
    for a,b in values:
        if b<=0:raise ValueError("denominator must be positive")
        if a==0:
            # In v1 Rational=Q there are no infinity/NaN factors, so zero is
            # an unconditional absorbing value and the remaining input need not
            # enlarge the workspace.
            return 0,1
        n*=a;d*=b
    return n,d

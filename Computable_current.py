import sys
import math
import warnings
from weakref import WeakValueDictionary
from fractions import Fraction
from types import MappingProxyType,NotImplementedType
from typing import Literal,Callable,Iterable,Iterator,Self,ClassVar,Never,TYPE_CHECKING

if TYPE_CHECKING:
    type IntegerRatio=tuple[int,int]
    type Rational="ComputableNumber.RationalNumber"
    type RationalLike=Rational|int|Fraction|str|float|tuple[RationalLike,RationalLike]
    type CompareResult=Literal[-1,0,1]
    type SignFunction=Callable[[int,int],CompareResult]
    type SignFunctionWithInfo=Callable[[int,int,bool],CompareResult]
    type Real="ComputableNumber.RealNumber"
    type RealLike=Real|RationalLike|SignFunction
    type InformationType=Literal[-1,0,1]
    type RopR[T]=Callable[[int,int,int,int],T]
    type IopR[T]=Callable[[T,int,int],SignFunction]
    type UopR[T]=Callable[[T,T,int,int],SignFunction]
    type IopI[T]=Callable[[T,T],SignFunction]
    type OpWithU[T]=Callable[[T,T,T],SignFunction]
    type RefineOutput=Iterator[IntegerRatio|tuple[IntegerRatio,int]]
    type RefineGenerator[T]=Callable[[T,T],RefineOutput]
    type Interval_op[T]=Callable[[T|IntegerRatio,T|IntegerRatio,T|IntegerRatio,T|IntegerRatio],tuple[T,T]]
    type Operation[T]=Callable[[T,RealLike],T]
    type OperationRational[T]=Callable[[T,RationalLike],T]
    type StrictOperation[T]=Callable[[T,T],T]
    type Factories[T]=tuple[IopR[T],IopR[T],UopR[T],UopR[T],IopI[T],OpWithU[T],OpWithU[T],OpWithU[T]]
    type Products[T]=tuple[OperationRational[T],OperationRational[T],StrictOperation[T],StrictOperation[T],StrictOperation[T]]

sys.set_int_max_str_digits(0)

undecidablewarning_string='It is not certain whether this object is rational. You may encounter undecidable rational number input.'
class UndecidableWarning(UserWarning): pass
def warn_undecidable()->None: warnings.warn(undecidablewarning_string,UndecidableWarning,stacklevel=3)

class PrivateAttribute:
    __slots__=('name','value')
    def __init__(self,name:str,value):
        self.name=name
        self.value=value
    def __get__(self,instance,owner):
        if instance is None: raise AttributeError(f"Type object '{owner.__name__}' has no attribute '{self.name}'")
        else: raise AttributeError(f"'{owner.__name__}' object has no attribute '{self.name}'")
    def __set__(self,instance,value):
        raise AttributeError(f"{type(instance).__name__} object cannot be assigned an attribute named '{self.name}'")
    def __delete__(self,instance):
        raise AttributeError(f"{type(instance).__name__} object has no attribute '{self.name}'")

class ComputableType(type):
    class RationalType(type):
        _unqueryable_attribute=frozenset({'memo_dict','__weakref__'})
        _unreadable_attribute=frozenset({'memo_dict','__weakref__'})
        _unwritable_attribute=frozenset({'ZERO','ONE','infty','minfty','nan','memo_dict','numerator','denominator','_is_simplified','_hash','_is_frozen',
                                         '_unreadable_attribute','_unwritable_attribute','_family_root','_container_class','_Real','__weakref__'})
        _undeletable_attribute=frozenset({'ZERO','ONE','infty','minfty','nan','memo_dict','numerator','denominator','_is_simplified','_hash','_is_frozen',
                                          '_unreadable_attribute','_unwritable_attribute','_family_root','_container_class','_Real','__weakref__'})
        @staticmethod
        def _normalize(numerator:int,denominator:int)->tuple[int,int,bool]:
            if denominator==0:
                if numerator>0: return 1,0,True
                if numerator<0: return -1,0,True
                return 0,0,True
            if numerator==0: return 0,1,True
            if denominator<0: numerator,denominator=-numerator,-denominator
            return numerator,denominator,False
        @staticmethod
        def _simplify(numerator:int,denominator:int)->IntegerRatio:
            common_part=math.gcd(numerator,denominator)
            return numerator//common_part,denominator//common_part
        @staticmethod
        def _is_exactly_float(numerator:int,denominator:int)->bool:
            if denominator&(denominator-1): return False
            if denominator==0: return True
            if numerator==0: return True
            numerator_abs=-numerator if numerator<0 else numerator
            if numerator_abs>(((1<<53)-1)<<971)*denominator: return False
            if denominator==1:
                two_factor=(numerator_abs&(-numerator_abs)).bit_length()-1
                odd_part=numerator_abs>>two_factor
                return odd_part.bit_length()<=53
            if (numerator_abs<<1022)>=denominator: return numerator_abs.bit_length()<=53
            return denominator.bit_length()<=1075
        def _compute_hash(cls,numerator:int,denominator:int)->int:
            if denominator==1: return hash(numerator)
            if denominator==0:
                if numerator>0: return cls.infty._hash 
                if numerator<0: return cls.minfty._hash
                return cls.nan._hash
            if cls._is_exactly_float(numerator,denominator): return hash(numerator/denominator)
            return hash(Fraction(numerator,denominator))
        def _create_new_instance[T](cls:type[T],numerator:int,denominator:int,hash_value:int)->T:
            instance=cls.__new__(cls)
            property_setter=super(cls,instance).__setattr__
            property_setter('numerator',numerator)
            property_setter('denominator',denominator)
            property_setter('_is_simplified',True)
            property_setter('_hash',hash_value)
            property_setter('_is_frozen',True)
            return instance
        def _new_for_simple[T](cls:type[T],numerator:int,denominator:int)->T:
            key_tuple=(numerator,denominator)
            _memo_dict=cls.__dict__['memo_dict'].value
            cached=_memo_dict.get(key_tuple)
            if cached is not None: return cached
            hash_value=cls._compute_hash(numerator,denominator)
            instance=cls._create_new_instance(numerator,denominator,hash_value)
            _memo_dict[key_tuple]=instance
            return instance
        def __new__(mcls,name,bases,namespace):
            namespace['memo_dict']=PrivateAttribute('memo_dict',WeakValueDictionary())
            cls=super().__new__(mcls,name,bases,namespace)
            init_constants={(0,1):('ZERO',hash(0)),(1,1):('ONE',hash(1)),
                            (0,0):('nan',hash(float('nan'))),(-1,0):('minfty',hash(float('-inf'))),(1,0):('infty',hash(float('inf')))}
            meta_super_proxy=super(type(cls),cls)
            meta_super_setter=meta_super_proxy.__setattr__
            _memo_dict=cls.__dict__['memo_dict'].value
            for constant,name_value in init_constants.items():
                numerator,denominator=constant
                name,hash_value=name_value
                instance=cls._create_new_instance(numerator,denominator,hash_value)
                meta_super_setter(name,instance)
                _memo_dict[constant]=instance
            chain=cls.__mro__
            chain_length=len(chain)
            for i in range(chain_length-1,-1,-1):
                category=chain[i]
                if isinstance(category,ComputableType.RationalType):
                    meta_super_setter('_family_root',category)
                    break
            meta_super_setter('__weakref__',PrivateAttribute('__weakref__',None))
            return cls
        def _special_sub(cls,numerator_left:int,denominator_left:int,numerator_right:int,denominator_right:int)->tuple[int,int,bool]:
            if denominator_left==0 and denominator_right==0:
                if numerator_left>0 and numerator_right<0: return 1,0,True
                if numerator_left<0 and numerator_right>0: return -1,0,True
            numerator=numerator_left*denominator_right-numerator_right*denominator_left
            denominator=denominator_left*denominator_right
            return cls._normalize(numerator,denominator)
        def _special_div(cls,numerator_up:int,denominator_up:int,numerator_down:int,denominator_down:int)->tuple[int,int,bool]:
            if denominator_up==0 and numerator_up!=0 and denominator_down!=0 and numerator_down<0:
                numerator_up,numerator_down=-numerator_up,-numerator_down
            numerator,denominator=numerator_up*denominator_down,denominator_up*numerator_down
            return cls._normalize(numerator,denominator)
        def _analyze_string_for_scalar(cls,string:str)->tuple[int,int]:
            if '.' in string:
                separate_string=string.split('.')
                if len(separate_string)>2: raise ValueError(f"cannot convert string '{string}' to {cls.__name__}.")
                string_head,string_tail=separate_string
                numerator=int(string_head+string_tail)
                exponent=-len(string_tail)
                return numerator,exponent
            return int(string),0
        def _analyze_string(cls,string:str)->tuple[int,int,bool]:
            string="".join(string.split()).lower()
            if 'n' in string:
                float_str=float(string)
                if float_str==float('inf'): return 1,0,True
                if float_str==float('-inf'): return -1,0,True
                if float_str!=float_str: return 0,0,True
                raise ValueError(f"cannot convert string '{string}' to {cls.__name__}.")
            exponent_iter=iter(string.split('e'))
            scalar=next(exponent_iter)
            numerator,exponent=cls._analyze_string_for_scalar(scalar)
            exponent+=sum(int(exponent) for exponent in exponent_iter)
            if exponent>=0:
                numerator*=10**exponent
                return numerator,1,True
            return numerator,10**(-exponent),False
        def _analyze_input_for_one_argument(cls,arg:RationalLike)->tuple[int,int,bool]:
            family_root=super(type(cls),cls).__getattribute__('_family_root')
            if isinstance(arg,family_root): return arg.numerator,arg.denominator,False
            if isinstance(arg,int): return arg,1,True
            if isinstance(arg,Fraction): return arg.numerator,arg.denominator,True
            if isinstance(arg,tuple) and len(arg)==2:
                up,down=arg
                numerator_up,denominator_up,_=cls._analyze_input_for_one_argument(up)
                numerator_down,denominator_down,_=cls._analyze_input_for_one_argument(down)
                return cls._special_div(numerator_up,denominator_up,numerator_down,denominator_down)
            if isinstance(arg,str):
                if '/' in arg:
                    up_string,down_string=arg.split('/')
                    up,down=cls._analyze_string(up_string),cls._analyze_string(down_string)
                    numerator_up,denominator_up,_=up
                    numerator_down,denominator_down,_=down
                    return cls._special_div(numerator_up,denominator_up,numerator_down,denominator_down)
                return cls._analyze_string(arg)
            if isinstance(arg,float):
                if arg==float('inf'): return 1,0,True
                if arg==float('-inf'): return -1,0,True
                if arg!=arg: return 0,0,True
                numerator,denominator=arg.as_integer_ratio()
                return numerator,denominator,True
            raise TypeError(f"Expected rational number, int, str, float or a tuple of two elements, type of input is {type(arg)}")
        def _analyze_input(cls,*args:RationalLike)->tuple[int,int,bool]:
            if len(args)==1: return cls._analyze_input_for_one_argument(args[0])
            if len(args)==2:
                up,down=args
                numerator_up,denominator_up,_=cls._analyze_input(up)
                numerator_down,denominator_down,_=cls._analyze_input(down)
                return cls._special_div(numerator_up,denominator_up,numerator_down,denominator_down)
            raise TypeError("Expected one argument or two arguments")
        def __call__[T](cls:type[T],*args:RationalLike)->T:
            numerator,denominator,is_simple=cls._analyze_input(*args)
            key_tuple=(numerator,denominator)
            _memo_dict=cls.__dict__['memo_dict'].value
            cached=_memo_dict.get(key_tuple)
            if cached is not None: return cached
            if not is_simple:
                numerator,denominator=cls._simplify(numerator,denominator)
                key_tuple=(numerator,denominator)
                cached=_memo_dict.get(key_tuple)
                if cached is not None: return cached
            hash_value=cls._compute_hash(numerator,denominator)
            instance=cls._create_new_instance(numerator,denominator,hash_value)
            _memo_dict[key_tuple]=instance
            return instance
        def __dir__(cls): names=super().__dir__(); return [name for name in names if name not in type(cls)._unqueryable_attribute]
        def __setattr__(cls,name,value):
            mcls=type(cls)
            if name in mcls._unwritable_attribute:
                if name in mcls._unreadable_attribute: raise AttributeError("The class attribute cannot be assigned a value")
                raise AttributeError(f"{name} is a read-only {cls.__name__}'s attribute")
            super().__setattr__(name,value)
        def __delattr__(cls,name):
            mcls=type(cls)
            if name in mcls._undeletable_attribute:
                if name in mcls._unreadable_attribute:
                    raise AttributeError(f"Type object '{cls.__name__}' has no attribute '{name}'")
                raise AttributeError(f"{name} is a undeletable class attribute")
            super().__delattr__(name)
        @property
        def cache_keys(cls)->list[IntegerRatio]: dictionary=cls.__dict__['memo_dict'].value; return list(dictionary.keys())
        @property
        def cache_values[T](cls:type[T])->list[T]:
            dictionary=cls.__dict__['memo_dict'].value
            cache_values=list(dictionary.values())
            return [v.__copy__() for v in cache_values]
        @property
        def cache_dict_for_read[T](cls:type[T])->MappingProxyType[IntegerRatio,T]:
            dictionary=cls.__dict__['memo_dict'].value
            return MappingProxyType(dictionary)
        @property
        def cache_dict_for_use[T](cls:type[T])->dict[IntegerRatio,T]:
            dictionary=cls.__dict__['memo_dict'].value
            cache_items=list(dictionary.items())
            return {k:v.__copy__() for k,v in cache_items}
        @property
        def cache_size(cls)->int: dictionary=cls.__dict__['memo_dict'].value; return len(dictionary)
        def cache_clear(cls)->None:
            dictionary=cls.__dict__['memo_dict'].value
            z,o,i,m,n=cls.ZERO,cls.ONE,cls.infty,cls.minfty,cls.nan
            temp_dict={z.as_integer_ratio():z,o.as_integer_ratio():o,i.as_integer_ratio():i,m.as_integer_ratio():m,n.as_integer_ratio():n}
            dictionary.clear()
            dictionary.update(temp_dict)
    class RealType(type):
        _unwritable_attribute=frozenset({'PI','E','_family_root','_container_class','_Rational'})
        _undeletable_attribute=frozenset({'PI','E','_family_root','_container_class','_Rational','set_max_denominator_for_hash'})
        def __setattr__(cls,name,value):
            mcls=type(cls)
            if name in mcls._unwritable_attribute: raise AttributeError(f"{name} is a read-only {cls.__name__}'s attribute")
            if name=='set_max_denominator_for_hash':
                max_denominator=cls.set_max_denominator_for_hash
                if max_denominator is not None:
                    if value!=max_denominator: raise ValueError(f"{cls.__name__}.set_max_denominator_for_hash can be set at most once")
                    else: return
                elif not isinstance(value,int): raise TypeError(f"Expected an integer, type of input is {type(value)}")
                if value<1: raise ValueError(f"Expected a positive integer, input is {value}")
            super().__setattr__(name,value)
        def __delattr__(cls,name):
            mcls=type(cls)
            if name in mcls._undeletable_attribute: raise AttributeError(f"{name} is a undeletable class attribute")
            super().__delattr__(name)
        def __new__(mcls,name,bases,namespace):
            cls=super().__new__(mcls,name,bases,namespace)
            meta_super_setter=super(type(cls),cls).__setattr__
            chain=cls.__mro__
            chain_length=len(chain)
            for i in range(chain_length-1,-1,-1):
                category=chain[i]
                if isinstance(category,ComputableType.RealType):
                    meta_super_setter('_family_root',category)
                    break
            R_add_R=cls._rational_add_rational
            I_add_R=cls._irrational_add_rational
            add_generator=cls._refine_generator_for_add
            I_add=cls._interval_add
            left_addition,right_addition=cls._generated_operator_add(R_add_R,I_add_R,add_generator,I_add)
            meta_super_setter('__add__',left_addition)
            meta_super_setter('__radd__',right_addition)
            meta_super_setter('__iadd__',left_addition)
            del cls._rational_add_rational,cls._irrational_add_rational,cls._refine_generator_for_add,cls._interval_add,cls._generated_operator_add
            R_sub_R=cls._rational_sub_rational
            I_sub_R=cls._irrational_sub_rational
            R_sub_I=cls._irrational_rsub_rational
            sub_generator=cls._refine_generator_for_sub
            I_sub=cls._interval_sub
            left_subtraction,right_subtraction=cls._generated_operator_sub(R_sub_R,I_sub_R,R_sub_I,sub_generator,I_sub)
            meta_super_setter('__sub__',left_subtraction)
            meta_super_setter('__rsub__',right_subtraction)
            meta_super_setter('__isub__',left_subtraction)
            del cls._rational_sub_rational,cls._irrational_sub_rational,cls._irrational_rsub_rational,cls._refine_generator_for_sub,cls._interval_sub
            del cls._generated_operator_sub
            R_mul_R=cls._rational_mul_rational
            I_mul_pos_R=cls._irrational_mul_pos_rational
            I_mul_neg_R=cls._irrational_mul_neg_rational
            pos_mul_pos_generator=cls._refine_generator_for_pos_mul_pos
            pos_mul_neg_generator=cls._refine_generator_for_pos_mul_neg
            neg_mul_pos_generator=cls._refine_generator_for_neg_mul_pos
            neg_mul_neg_generator=cls._refine_generator_for_neg_mul_neg
            I_pos_mul_pos=cls._interval_pos_mul_pos
            I_pos_mul_neg=cls._interval_pos_mul_neg
            I_neg_mul_pos=cls._interval_neg_mul_pos
            I_neg_mul_neg=cls._interval_neg_mul_neg
            left_multiplication,right_multiplication=cls._generated_operator_mul(R_mul_R,I_mul_pos_R,I_mul_neg_R,
                                                                                 pos_mul_pos_generator,I_pos_mul_pos,
                                                                                 pos_mul_neg_generator,I_pos_mul_neg,
                                                                                 neg_mul_pos_generator,I_neg_mul_pos,
                                                                                 neg_mul_neg_generator,I_neg_mul_neg)
            meta_super_setter('__mul__',left_multiplication)
            meta_super_setter('__rmul__',right_multiplication)
            meta_super_setter('__imul__',left_multiplication)
            del cls._rational_mul_rational,cls._irrational_mul_pos_rational,cls._irrational_mul_neg_rational,cls._refine_generator_for_pos_mul_pos
            del cls._refine_generator_for_pos_mul_neg,cls._refine_generator_for_neg_mul_pos,cls._refine_generator_for_neg_mul_neg
            del cls._interval_pos_mul_pos,cls._interval_pos_mul_neg,cls._interval_neg_mul_pos,cls._interval_neg_mul_neg,cls._generated_operator_mul
            R_div_R=cls._rational_div_rational
            I_div_pos_R=cls._irrational_div_pos_rational
            I_div_neg_R=cls._irrational_div_neg_rational
            R_div_I_pos_pos=cls._pos_rational_div_pos_irrational
            R_div_I_pos_neg=cls._pos_rational_div_neg_irrational
            R_div_I_neg_pos=cls._neg_rational_div_pos_irrational
            R_div_I_neg_neg=cls._neg_rational_div_neg_irrational
            pos_div_pos_generator=cls._refine_generator_for_pos_div_pos
            pos_div_neg_generator=cls._refine_generator_for_pos_div_neg
            neg_div_pos_generator=cls._refine_generator_for_neg_div_pos
            neg_div_neg_generator=cls._refine_generator_for_neg_div_neg
            I_pos_div_pos=cls._interval_pos_div_pos
            I_pos_div_neg=cls._interval_pos_div_neg
            I_neg_div_pos=cls._interval_neg_div_pos
            I_neg_div_neg=cls._interval_neg_div_neg
            left_division,right_division=cls._generated_operator_div(R_div_R,I_div_pos_R,I_div_neg_R,
                                                                     R_div_I_pos_pos,pos_div_pos_generator,I_pos_div_pos,
                                                                     R_div_I_pos_neg,pos_div_neg_generator,I_pos_div_neg,
                                                                     R_div_I_neg_pos,neg_div_pos_generator,I_neg_div_pos,
                                                                     R_div_I_neg_neg,neg_div_neg_generator,I_neg_div_neg)
            meta_super_setter('__truediv__',left_division)
            meta_super_setter('__rtruediv__',right_division)
            meta_super_setter('__itruediv__',left_division)
            del cls._rational_div_rational,cls._irrational_div_pos_rational,cls._irrational_div_neg_rational,cls._pos_rational_div_pos_irrational
            del cls._pos_rational_div_neg_irrational,cls._neg_rational_div_pos_irrational,cls._neg_rational_div_neg_irrational
            del cls._refine_generator_for_pos_div_pos,cls._refine_generator_for_pos_div_neg,cls._refine_generator_for_neg_div_pos
            del cls._refine_generator_for_neg_div_neg,cls._interval_pos_div_pos,cls._interval_pos_div_neg,cls._interval_neg_div_pos,cls._interval_neg_div_neg
            del cls._generated_operator_div,cls._factory_for_operator,cls._products_for_operator
            return cls
        def _analyze_input_for_sign_function(cls,arg)->tuple[IntegerRatio|SignFunction,bool]:
            try:
                RaN=cls._Rational
                numerator_input,denominator_input,_=RaN._analyze_input_for_one_argument(arg)
                if denominator_input==0: raise ValueError('The input must be a finite number.')
                return (numerator_input,denominator_input),True
            except TypeError:
                if isinstance(arg,Callable) and not isinstance(arg,type): return arg,False
                raise TypeError(f"Expected a sign_function or rational number, type of input is {type(arg)}")
        def __call__[T](cls:type[T],*args,**kwargs)->T:
            args_length=len(args)
            if args_length==0:
                try: sign_function=kwargs.pop('sign_function')
                except KeyError: raise TypeError("Expected a sign_function")
                is_possible_rational=kwargs.pop('is_possible_rational',True)
                is_possible_irrational=kwargs.pop('is_possible_irrational',True)
                left=kwargs.pop('left',None)
                right=kwargs.pop('right',None)
                if kwargs: raise TypeError(f"Unexpected keyword argument(s): {', '.join(kwargs)}")
            elif args_length==1:
                sign_function=args[0]
                is_possible_rational=kwargs.pop('is_possible_rational',True)
                is_possible_irrational=kwargs.pop('is_possible_irrational',True)
                left=kwargs.pop('left',None)
                right=kwargs.pop('right',None)
                if kwargs: raise TypeError(f"Unexpected keyword argument(s): {', '.join(kwargs)}")
            elif args_length==2:
                sign_function,is_possible_rational=args
                is_possible_irrational=kwargs.pop('is_possible_irrational',True)
                left=kwargs.pop('left',None)
                right=kwargs.pop('right',None)
                if kwargs: raise TypeError(f"Unexpected keyword argument(s): {', '.join(kwargs)}")
            elif args_length==3:
                sign_function,is_possible_rational,is_possible_irrational=args
                left=kwargs.pop('left',None)
                right=kwargs.pop('right',None)
                if kwargs: raise TypeError(f"Unexpected keyword argument(s): {', '.join(kwargs)}")
            elif args_length==4:
                sign_function,is_possible_rational,is_possible_irrational,left=args
                right=kwargs.pop('right',None)
                if kwargs: raise TypeError(f"Unexpected keyword argument(s): {', '.join(kwargs)}")
            elif args_length==5:
                sign_function,is_possible_rational,is_possible_irrational,left,right=args
                if kwargs: raise TypeError(f"Unexpected keyword argument(s): {', '.join(kwargs)}")
            else: raise TypeError("Expected at most five arguments")
            is_true_type1,is_true_type2=isinstance(is_possible_rational,bool),isinstance(is_possible_irrational,bool)
            if not is_true_type1: raise TypeError(f"Expected a bool object, input is {type(is_possible_rational)}")
            if not is_true_type2: raise TypeError(f"Expected a bool object, input is {type(is_possible_irrational)}")
            if not is_possible_rational and not is_possible_irrational: raise ValueError('The input has a contradiction')
            if isinstance(sign_function,cls._family_root):
                sign_function._is_called=True
                sign_function.__init__(is_possible_rational,is_possible_irrational)
                return sign_function
            sign_function,is_exactly_rational=cls._analyze_input_for_sign_function(sign_function)
            RaN=cls._Rational
            if is_exactly_rational:
                if not is_possible_rational: raise ValueError('The input has a contradiction')
                if is_possible_irrational: is_possible_irrational=False
                numerator_input,denominator_input=sign_function
                if denominator_input==0: raise ValueError('The input must be a finite number.')
                result_rational=RaN(numerator_input,denominator_input)
                instance=cls.__new__(cls)
                instance._is_called=True
                instance.__init__(result_rational)
                return instance
            if is_possible_rational and is_possible_irrational: warn_undecidable()
            instance=cls.__new__(cls)
            instance._is_called=True
            instance.__init__(left,right,sign_function,is_possible_rational,is_possible_irrational)
            return instance
    def __new__(mcls,name,bases,namespace):
        cls=super().__new__(mcls,name,bases,namespace)
        RaT=mcls.RationalType
        ReT=mcls.RealType
        type_class_list=[RaT,ReT]
        type_class_dict={}
        for category in namespace.values():
            for meta_category in type_class_list:
                if isinstance(category,meta_category):
                    type_class_dict[meta_category]=category
                    break
        number_class_list=list(type_class_dict.values())
        for meta_category in type_class_list:
            category=type_class_dict[meta_category]
            super_setter=super(meta_category,category).__setattr__
            super_setter('_container_class',cls)
            for other_category in number_class_list:
                if category is not other_category:
                    number_class_name=other_category.__name__
                    if number_class_name.endswith('Number'):
                        number_class_name=number_class_name.removesuffix('Number')
                        super_setter('_'+number_class_name,other_category)
                    else: raise ValueError("The name of number class must end with 'Number'")
        RaN,ReN=number_class_list
        simplifyer=RaN._simplify
        super_setter=super(ReT,ReN).__setattr__
        
        #region: create pi module
        pi_module=ReN.__new__(ReN)
        def _compute_series_generator_for_pi()->Iterator[IntegerRatio]:
            denominator_scalar=10939058860032000
            l_k_scalar=545140134
            k,n_k,S_k_denominator=0,1,1
            l_k,S_k_numerator=13591409,13591409
            multiple1,multiple2,multiple3=-1,-5,-1
            while True:
                yield S_k_numerator,S_k_denominator
                k+=1
                l_k+=l_k_scalar
                multiple1+=2; multiple2+=6; multiple3+=6
                n_k_multiple=multiple1*multiple2*multiple3
                d_k_multiple=denominator_scalar*(k**3)
                n_k_multiple,d_k_multiple=simplifyer(n_k_multiple,d_k_multiple)
                n_k*=-n_k_multiple
                S_k_numerator=S_k_numerator*d_k_multiple+n_k*l_k
                S_k_denominator*=d_k_multiple
        pi_series_generator=_compute_series_generator_for_pi()
        get_next_for_pi=pi_series_generator.__next__
        compare_multiple_for_pi=1823176476672000
        shn,shd=get_next_for_pi()
        shn,shd=simplifyer(shn,shd)
        shnsq=shn*shn
        shnsq,commu=simplifyer(shnsq,compare_multiple_for_pi)
        pi_module._series_high_numerator_square=shnsq
        pi_module._series_high_denominator_mul=shd*shd*commu
        sln,sld=get_next_for_pi()
        sln,sld=simplifyer(sln,sld)
        slnsq=sln*sln
        slnsq,commu=simplifyer(slnsq,compare_multiple_for_pi)
        pi_module._series_low_numerator_square=slnsq
        pi_module._series_low_denominator_mul=sld*sld*commu
        def _update_attribute_for_pi(series_high_numerator_square:int,series_high_denominator_mul:int,
                                     series_low_numerator_square:int,series_low_denominator_mul:int)->None:
            series_high_numerator_square,series_high_denominator_mul=simplifyer(series_high_numerator_square,series_high_denominator_mul)
            series_low_numerator_square,series_low_denominator_mul=simplifyer(series_low_numerator_square,series_low_denominator_mul)
            pi_module._series_high_numerator_square=series_high_numerator_square
            pi_module._series_high_denominator_mul=series_high_denominator_mul
            pi_module._series_low_numerator_square=series_low_numerator_square
            pi_module._series_low_denominator_mul=series_low_denominator_mul
        def _sign_func_for_pi(numerator:int,denominator:int)->CompareResult:
            numerator_square,denominator_square=numerator*numerator,denominator*denominator
            shnsq,shdmu=pi_module._series_high_numerator_square,pi_module._series_high_denominator_mul
            if numerator_square*shnsq<=denominator_square*shdmu: return -1
            slnsq,sldmu=pi_module._series_low_numerator_square,pi_module._series_low_denominator_mul
            if numerator_square*slnsq>=denominator_square*sldmu: return 1
            while True:
                shn,shd=get_next_for_pi()
                shnsq=shn*shn
                shdmu=shd*shd*compare_multiple_for_pi
                sln,sld=get_next_for_pi()
                slnsq=sln*sln
                sldmu=sld*sld*compare_multiple_for_pi
                if numerator_square*shnsq<=denominator_square*shdmu: _update_attribute_for_pi(shnsq,shdmu,slnsq,sldmu); return -1
                if numerator_square*slnsq>=denominator_square*sldmu: _update_attribute_for_pi(shnsq,shdmu,slnsq,sldmu); return 1
        pi_module._is_called=False
        pi_module.__init__(3,4,_sign_func_for_pi,False,True)
        super_setter('PI',pi_module)
        #endregion
        
        #region: create e module
        e_module=ReN.__new__(ReN)
        def _compute_series_generator_for_e()->Iterator[IntegerRatio]:
            k=2
            n_k=1
            S_k_numerator=1
            S_k_denominator=2
            while True:
                yield S_k_numerator,S_k_denominator
                k+=1
                n_k=-n_k
                S_k_denominator*=k
                S_k_numerator=S_k_numerator*k+n_k
        e_series_generator=_compute_series_generator_for_e()
        get_next_for_e=e_series_generator.__next__
        e_module._series_generator=e_series_generator
        shn,shd=get_next_for_e()
        shn,shd=simplifyer(shn,shd)
        e_module._series_high_numerator,e_module._series_high_denominator=shn,shd
        sln,sld=get_next_for_e()
        sln,sld=simplifyer(sln,sld)
        e_module._series_low_numerator,e_module._series_low_denominator=sln,sld
        def _update_attribute_for_e(series_high_numerator:int,series_high_denominator:int,series_low_numerator:int,series_low_denominator:int)->None:
            series_high_numerator,series_high_denominator=simplifyer(series_high_numerator,series_high_denominator)
            series_low_numerator,series_low_denominator=simplifyer(series_low_numerator,series_low_denominator)
            e_module._series_high_numerator=series_high_numerator
            e_module._series_high_denominator=series_high_denominator
            e_module._series_low_numerator=series_low_numerator
            e_module._series_low_denominator=series_low_denominator
        def _sign_func_for_e(numerator:int,denominator:int)->CompareResult:
            shn,shd=e_module._series_high_numerator,e_module._series_high_denominator
            if numerator*shn<=denominator*shd: return -1
            sln,sld=e_module._series_low_numerator,e_module._series_low_denominator
            if numerator*sln>=denominator*sld: return 1
            while True:
                shn,shd=get_next_for_e()
                sln,sld=get_next_for_e()
                if numerator*shn<=denominator*shd: _update_attribute_for_e(shn,shd,sln,sld); return -1
                if numerator*sln>=denominator*sld: _update_attribute_for_e(shn,shd,sln,sld); return 1
        e_module._is_called=False
        e_module.__init__(2,3,_sign_func_for_e,False,True)
        super_setter('E',e_module)
        #endregion

        return cls

class ComputableNumber(metaclass=ComputableType):
    def __new__(cls,*args,**kwargs)->Never: raise TypeError("This class cannot be instantiated")
    class RationalNumber[R:Real](metaclass=ComputableType.RationalType):
        """
        Overview:
            Exact rational number implementation used by ``ComputableNumber``.
            Instances support two runtime states: mutable and frozen.

        Design Philosophy:
            ``RationalNumber`` is designed to keep mutable objects flexible and fast during heavy
            arithmetic. Mutable objects can delay simplification, so intermediate steps do not need
            to normalize on every operation. When hashability, canonical identity, or sharing is
            required, objects are frozen through ``intern()`` (or ``__hash__()`` side effects), so
            equal values become stable and cache-friendly.

        Mutability Model:
            mutable:
                ``_is_frozen == False``. The instance may be changed in place (for example by
                ``__setattr__`` or in-place arithmetic operators).
            frozen/immutable:
                ``_is_frozen == True``. In-place mutation is blocked and operations create or
                return other objects.

        State Transitions:
            A single object can only move from mutable to frozen. There is no in-place unfreeze.
            To get a mutable equivalent of a frozen value, use ``__copy__()``.

        State Matrix:
            Constructor and constants:
                ``ComputableRational(...)``:
                    Frozen by default. Objects are obtained through the global intern/cache path.
                ``ZERO``, ``ONE``, ``infty``, ``minfty``, ``nan``:
                    Frozen singleton constants.

            Canonicalization and hashing:
                ``__copy__()``:
                    Always returns a new mutable object.
                ``intern()``:
                    Simplifies, freezes, and canonicalizes through the global cache; may return a
                    previously cached frozen object.
                ``__hash__()``:
                    Freezes the current object (if still mutable) and may register it in cache.

            Binary arithmetic (new object):
                ``+``, ``-``, ``*``, ``/`` and reflected versions:
                    Return a new mutable ``RationalNumber`` by default.

            In-place arithmetic:
                ``+=``, ``-=``, ``*=``, ``/=`` on mutable receiver:
                    Mutates the same object in place (still mutable unless later frozen).
                ``+=``, ``-=``, ``*=``, ``/=`` on frozen receiver:
                    Returns a different new mutable object.

            Instance methods returning RationalNumber:
                Examples: ``__neg__``, ``__abs__``, ``rational_floor``, ``rational_ceil``,
                ``rational_trunc``, ``rational_round``, ``rational_divmod`` members,
                ``simplest_rational_in_interval``.
                Default: new mutable objects, unless explicitly interned/cached afterward.

            Class methods returning RationalNumber:
                Examples: ``convert_from_float``, ``sum``, ``product``, and exact-rational branches
                of advanced class methods such as ``logarithm``.
                Default: new mutable objects.

        Best Practices:
            - Before arithmetic-intensive loops, start from ``x = x.__copy__()`` to keep updates mutable.
            - Inside loops, prefer in-place operations (``+=``, ``*=``, etc.) to reduce allocations.
            - Call ``.intern()`` on final or important results to deduplicate memory and freeze canonical values.
            - Before inserting into ``dict`` keys or ``set``, call ``.intern()`` to avoid duplicated equal values.

        Notes:
            When a ``RealNumber`` method returns ``RationalNumber`` objects, the returned values are
            frozen by default.
        """
        _Real:ClassVar[type[R]]
        memo_dict:ClassVar[WeakValueDictionary[IntegerRatio,Self]]
        ZERO:ClassVar[Self]
        nan:ClassVar[Self]
        minfty:ClassVar[Self]
        infty:ClassVar[Self]
        _family_root:ClassVar[Rational]
        _container_class:ClassVar["ComputableNumber"]
        __slots__=('numerator','denominator','_is_simplified','_hash','_is_frozen','__weakref__')
        numerator:int
        denominator:int
        _is_simplified:bool
        _hash:int|None
        _is_frozen:bool
        _unwritable_attribute=frozenset({'_is_simplified','_hash','_is_frozen','__weakref__'})
        @classmethod
        def _construct_new_object_for_straight(cls,numerator:int,denominator:int)->Self:
            instance=cls.__new__(cls)
            property_setter=super(cls,instance).__setattr__
            property_setter('numerator',numerator)
            property_setter('denominator',denominator)
            property_setter('_is_simplified',False)
            property_setter('_hash',None)
            property_setter('_is_frozen',False)
            return instance
        @classmethod
        def _construct_new_object_for_simple(cls,numerator:int,denominator:int)->Self:
            instance=cls.__new__(cls)
            property_setter=super(cls,instance).__setattr__
            property_setter('numerator',numerator)
            property_setter('denominator',denominator)
            property_setter('_is_simplified',True)
            property_setter('_hash',None)
            property_setter('_is_frozen',False)
            return instance
        def __copy__(self):
            cls=type(self)
            instance=cls.__new__(cls)
            property_setter=super(cls,instance).__setattr__
            property_setter('numerator',self.numerator)
            property_setter('denominator',self.denominator)
            is_simple=self._is_simplified
            property_setter('_is_simplified',is_simple)
            if is_simple: property_setter('_hash',self._hash)
            property_setter('_is_frozen',False)
            return instance
        @classmethod
        def convert_from_float(cls,float_value:float)->Self:
            if float_value==float('inf'): return cls.infty.__copy__()
            elif float_value==float('-inf'): return cls.minfty.__copy__()
            elif float_value!=float_value: return cls.nan.__copy__()
            else: numerator,denominator=float_value.as_integer_ratio()
            return cls._construct_new_object_for_simple(numerator,denominator)
        def _inplace_div(self,numerator_up:int,denominator_up:int,numerator_down:int,denominator_down:int)->None:
            cls=type(self)
            property_setter=super().__setattr__
            numerator,denominator,is_special=cls._special_div(numerator_up,denominator_up,numerator_down,denominator_down)
            if is_special: property_setter('_is_simplified',True)
            else: property_setter('_is_simplified',False)
            property_setter('numerator',numerator)
            property_setter('denominator',denominator)
            property_setter('_hash',None)
        def __setattr__(self,name,value):
            cls=type(self)
            if name in cls._unwritable_attribute: raise AttributeError(f"{name} is a read-only attribute for {cls.__name__} object")
            if self._is_frozen: raise ValueError('This property setting is invalid because the object is frozen')
            numerator_v,denominator_v,_=cls._analyze_input_for_one_argument(value)
            if name=='numerator': self._inplace_div(numerator_v,denominator_v,self.denominator,1)
            else: self._inplace_div(self.numerator,1,numerator_v,denominator_v)
        def __delattr__(self,name)->Never: raise AttributeError(f"{name} cannot be deleted from {type(self).__name__} object")
        def _inplace_setting(self,numerator:int,denominator:int,is_special:bool)->None:
            if self.numerator==numerator and self.denominator==denominator: return
            property_setter=super().__setattr__
            property_setter('numerator',numerator)
            property_setter('denominator',denominator)
            property_setter('_hash',None)
            if is_special: property_setter('_is_simplified',True)
            else: property_setter('_is_simplified',False)
        def _inplace_return(self,numerator:int,denominator:int,is_special:bool)->Self:
            if not self._is_frozen: self._inplace_setting(numerator,denominator,is_special); return self
            cls=type(self)
            if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
            return cls._construct_new_object_for_straight(numerator,denominator)
        def simplify(self)->None:
            if self._is_simplified: return
            cls=type(self)
            property_setter=super().__setattr__
            numerator,denominator=self.numerator,self.denominator
            if denominator==0:
                if numerator>0: property_setter('numerator',1)
                elif numerator<0: property_setter('numerator',-1)
            elif numerator==0: property_setter('denominator',1)
            else:
                numerator,denominator=cls._simplify(numerator,denominator)
                property_setter('numerator',numerator)
                property_setter('denominator',denominator)
            property_setter('_is_simplified',True)
            property_setter('_hash',None)
        def as_integer_ratio(self)->IntegerRatio: self.simplify(); return (self.numerator,self.denominator)
        def to_scientific_notation(self,precision:int=17)->str:
            if precision<0: raise ValueError('precision must be non-negative')
            numerator,denominator=self.as_integer_ratio()
            if denominator==0: return str(self)
            if numerator==0: return '0e+0'
            sign,numerator=(('-',-numerator) if numerator<0 else ('',numerator))
            numerator_len=len(str(numerator))
            denominator_len=len(str(denominator))
            exponent=numerator_len-denominator_len
            if exponent>0: denominator*=10**exponent
            elif exponent<0: numerator*=10**(-exponent)
            if numerator<denominator: numerator*=10; exponent-=1
            exponent_str=('+'+str(exponent) if exponent>=0 else str(exponent))
            quotient,remainder=divmod(numerator*(10**precision),denominator)
            quotient_str=str(quotient)
            if remainder==0: quotient_str=quotient_str.rstrip("0")
            if len(quotient_str)>1: quotient_str=quotient_str[0]+'.'+quotient_str[1:]
            return f'{sign}{quotient_str}e{exponent_str}'
        def intern(self)->Self:
            key_tuple=self.as_integer_ratio()
            cls=type(self)
            _memo_dict=cls.__dict__['memo_dict'].value
            cached=_memo_dict.get(key_tuple)
            if cached is not None: return cached
            property_setter=super().__setattr__
            if self._hash is None: hash_value=cls._compute_hash(*key_tuple); property_setter('_hash',hash_value)
            property_setter('_is_frozen',True)
            _memo_dict[key_tuple]=self
            return self
        def safe_setting(self,name:str,value)->Self:
            # When object is frozen, this function return a new object. Please use the form new_object = old_object.safe_setting(name,value).
            cls=type(self)
            if name in cls._unwritable_attribute: raise AttributeError(f"{name} is a read-only attribute for {cls.__name__} object")
            numerator_v,denominator_v,_=cls._analyze_input_for_one_argument(value)
            if self._is_frozen:
                if name=='numerator': numerator,denominator,is_special=cls._special_div(numerator_v,denominator_v,self.denominator,1)
                else: numerator,denominator,is_special=cls._special_div(self.numerator,1,numerator_v,denominator_v)
                if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
                else: return cls._construct_new_object_for_straight(numerator,denominator)
            if name=='numerator': self._inplace_div(numerator_v,denominator_v,self.denominator,1)
            else: self._inplace_div(self.numerator,1,numerator_v,denominator_v)
            return self
        def __hash__(self):
            if self._is_frozen: return self._hash
            cls=type(self)
            numerator,denominator=self.as_integer_ratio()
            property_setter=super().__setattr__
            _memo_dict=cls.__dict__['memo_dict'].value
            key=(numerator,denominator)
            cached=_memo_dict.get(key)
            if cached is None:
                if self._hash is None: hash_value=cls._compute_hash(numerator,denominator); property_setter('_hash',hash_value)
                else: hash_value=self._hash
                property_setter('_is_frozen',True)
                _memo_dict[key]=self
            else:
                if self._hash is None: hash_value=cached._hash; property_setter('_hash',hash_value)
                else: hash_value=self._hash
                property_setter('_is_frozen',True)
            return hash_value
        def __repr__(self):
            cls=type(self)
            cls_name=cls.__name__
            container_class=cls._container_class
            container_class_name=container_class.__name__
            head_str=f'{container_class_name}.{cls_name}'
            self.simplify()
            numerator,denominator=self.numerator,self.denominator
            if denominator==0:
                if numerator>0: return f'{head_str}.infty'
                if numerator<0: return f'{head_str}.minfty'
                return f'{head_str}.nan'
            if numerator==0: return f'{head_str}.ZERO'
            if numerator==denominator: return f'{head_str}.ONE'
            return f'{head_str}({numerator},{denominator})'
        def __str__(self):
            self.simplify()
            if self.denominator==0:
                if self.numerator>0: return 'inf'
                if self.numerator<0: return '-inf'
                return 'nan'
            if self.denominator==1: return str(self.numerator)
            return f'{self.numerator}/{self.denominator}'
        def _check_overflow_for_int(self)->None:
            if self.denominator==0:
                if self.numerator>0: raise OverflowError(f'cannot convert {type(self)} Infinity to integer')
                if self.numerator<0: raise OverflowError(f'cannot convert {type(self)} -Infinity to integer')
                raise ValueError(f'cannot convert {type(self)} NaN to integer')
        def __floor__(self): self._check_overflow_for_int(); return self.numerator//self.denominator
        def __ceil__(self): self._check_overflow_for_int(); return -(-self.numerator//self.denominator)
        def __trunc__(self):
            self._check_overflow_for_int()
            if self.numerator>=0: return self.numerator//self.denominator
            else: return -(-self.numerator//self.denominator)
        def __int__(self): return self.__trunc__()
        def int_bound(self)->tuple[int,int]:
            self._check_overflow_for_int()
            self_numerator=self.numerator
            self_denominator=self.denominator
            return (self_numerator//self_denominator,-(-self_numerator//self_denominator))
        def __float__(self):
            if self.denominator==0:
                if self.numerator==0: return float('nan')
                if self.numerator>0: return float('inf')
                return float('-inf')
            try: return self.numerator/self.denominator
            except OverflowError: return (float('-inf') if self.numerator<0 else float('inf'))
        def __complex__(self): return complex(float(self),0)
        def __neg__(self):
            if self._is_simplified: return type(self)._construct_new_object_for_simple(-self.numerator,self.denominator)
            return type(self)._construct_new_object_for_straight(-self.numerator,self.denominator)
        def __pos__(self): return self.__copy__()
        def __add__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            numerator,denominator,is_special=cls._special_sub(self.numerator,self.denominator,-numerator_right,denominator_right)
            if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
            return cls._construct_new_object_for_straight(numerator,denominator)
        def __radd__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_left,denominator_left,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            numerator,denominator,is_special=cls._special_sub(numerator_left,denominator_left,-self.numerator,self.denominator)
            if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
            return cls._construct_new_object_for_straight(numerator,denominator)
        def __iadd__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            numerator,denominator,is_special=cls._special_sub(self.numerator,self.denominator,-numerator_right,denominator_right)
            return self._inplace_return(numerator,denominator,is_special)
        def __sub__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            numerator,denominator,is_special=cls._special_sub(self.numerator,self.denominator,numerator_right,denominator_right)
            if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
            return cls._construct_new_object_for_straight(numerator,denominator)
        def __rsub__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_left,denominator_left,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            numerator,denominator,is_special=cls._special_sub(numerator_left,denominator_left,self.numerator,self.denominator)
            if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
            return cls._construct_new_object_for_straight(numerator,denominator)
        def __isub__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            numerator,denominator,is_special=cls._special_sub(self.numerator,self.denominator,numerator_right,denominator_right)
            return self._inplace_return(numerator,denominator,is_special)
        def __mul__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_down,denominator_down,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            if numerator_down>=0: numerator,denominator,is_special=cls._special_div(self.numerator,self.denominator,denominator_down,numerator_down)
            else: numerator,denominator,is_special=cls._special_div(self.numerator,self.denominator,denominator_down,-numerator_down); numerator=-numerator
            if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
            return cls._construct_new_object_for_straight(numerator,denominator)
        def __rmul__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_up,denominator_up,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            if self.numerator>=0: numerator,denominator,is_special=cls._special_div(numerator_up,denominator_up,self.denominator,self.numerator)
            else: numerator,denominator,is_special=cls._special_div(numerator_up,denominator_up,self.denominator,-self.numerator); numerator=-numerator
            if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
            return cls._construct_new_object_for_straight(numerator,denominator)
        def __imul__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_down,denominator_down,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            if numerator_down>=0: numerator,denominator,is_special=cls._special_div(self.numerator,self.denominator,denominator_down,numerator_down)
            else: numerator,denominator,is_special=cls._special_div(self.numerator,self.denominator,denominator_down,-numerator_down); numerator=-numerator
            return self._inplace_return(numerator,denominator,is_special)
        def __truediv__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_down,denominator_down,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            numerator,denominator,is_special=cls._special_div(self.numerator,self.denominator,numerator_down,denominator_down)
            if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
            return cls._construct_new_object_for_straight(numerator,denominator)
        def __rtruediv__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_up,denominator_up,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            numerator,denominator,is_special=cls._special_div(numerator_up,denominator_up,self.numerator,self.denominator)
            if is_special: return cls._construct_new_object_for_simple(numerator,denominator)
            return cls._construct_new_object_for_straight(numerator,denominator)
        def __itruediv__(self,other:RationalLike)->Self|NotImplementedType:
            cls=type(self)
            try: numerator_down,denominator_down,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            numerator,denominator,is_special=cls._special_div(self.numerator,self.denominator,numerator_down,denominator_down)
            return self._inplace_return(numerator,denominator,is_special)
        def __eq__(self,other:RationalLike)->bool|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            if self.denominator==0:
                if self.numerator==0: return False
                if self.numerator>0:
                    if denominator_right==0 and numerator_right<=0: return False
                elif denominator_right==0 and numerator_right>=0: return False
            elif denominator_right==0: return False
            return self.numerator*denominator_right==self.denominator*numerator_right
        def __ne__(self,other:RationalLike)->bool|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            if self.denominator==0:
                if self.numerator==0: return True
                if self.numerator>0:
                    if denominator_right==0 and numerator_right<=0: return True
                elif denominator_right==0 and numerator_right>=0: return True
            elif denominator_right==0: return True
            return self.numerator*denominator_right!=self.denominator*numerator_right
        def __lt__(self,other:RationalLike)->bool|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            if self.denominator==0 and denominator_right==0 and self.numerator<0 and numerator_right>0: return True
            return self.numerator*denominator_right<self.denominator*numerator_right
        def __le__(self,other:RationalLike)->bool|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            if self.denominator==0:
                if self.numerator==0: return False
                if denominator_right==0:
                    if self.numerator>0 and numerator_right<0: return False
                    if numerator_right==0: return False
            elif denominator_right==0 and numerator_right==0: return False
            return self.numerator*denominator_right<=self.denominator*numerator_right
        def __gt__(self,other:RationalLike)->bool|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            if self.denominator==0 and denominator_right==0 and self.numerator>0 and numerator_right<0: return True
            return self.numerator*denominator_right>self.denominator*numerator_right
        def __ge__(self,other:RationalLike)->bool|NotImplementedType:
            cls=type(self)
            try: numerator_right,denominator_right,_=cls._analyze_input_for_one_argument(other)
            except TypeError: return NotImplemented
            if self.denominator==0:
                if self.numerator==0: return False
                if denominator_right==0:
                    if self.numerator<0 and numerator_right>0: return False
                    if numerator_right==0: return False
            elif denominator_right==0 and numerator_right==0: return False
            return self.numerator*denominator_right>=self.denominator*numerator_right
        def __bool__(self): return self.numerator!=0 or self.denominator==0
        def __abs__(self):
            if self.numerator>=0: return self.__copy__()
            cls=type(self)
            if self._is_simplified: return cls._construct_new_object_for_simple(-self.numerator,self.denominator)
            return cls._construct_new_object_for_straight(-self.numerator,self.denominator)
        @staticmethod
        def _round_half_to_even(numerator:int,denominator:int)->int:
            if denominator==0: raise ZeroDivisionError
            quotient,two_remainder=divmod(numerator,denominator)
            two_remainder<<=1
            if two_remainder>denominator: quotient+=1
            elif two_remainder==denominator and quotient&1: quotient+=1
            return quotient
        def __round__(self,n:int=None)->int|Self:
            cls=type(self)
            if n is None: self._check_overflow_for_int(); return cls._round_half_to_even(self.numerator,self.denominator)
            if self.denominator==0:
                if self.numerator>0: return cls.infty.__copy__()
                if self.numerator<0: return cls.minfty.__copy__()
                return cls.nan.__copy__()
            if n>=0:
                scalar=10**n
                numerator=self.numerator*scalar
                rounded_quotient=cls._round_half_to_even(numerator,self.denominator)
                return cls._construct_new_object_for_straight(rounded_quotient,scalar)
            else:
                scalar=10**(-n)
                denominator=self.denominator*scalar
                rounded_quotient=cls._round_half_to_even(self.numerator,denominator)
                return cls._construct_new_object_for_straight(rounded_quotient*scalar,1)
        @classmethod
        def error_to_max_denominator(cls,error:RationalLike)->int:
            numerator_error,denominator_error,_=cls._analyze_input_for_one_argument(error)
            if numerator_error<=0: raise ValueError('Error must be positive')
            if denominator_error==0: return 1
            max_denominator=(denominator_error//numerator_error)+1
            return max_denominator
        def _rational_bound_for_regular(self,max_denominator:int)->tuple[Self,Self]:
            cls=type(self)
            numerator,denominator=self.numerator,self.denominator
            shift_integer,left_error=divmod(numerator,denominator)
            right_error=denominator-left_error
            if left_error==right_error:
                rational_left=cls._construct_new_object_for_simple(shift_integer,1)
                rational_right=cls._construct_new_object_for_simple(shift_integer+1,1)
                return rational_left,rational_right
            denominator_current=denominator_base=1
            if left_error>right_error:
                numerator_base=shift_integer+1
                error_base=right_error
                numerator_current=shift_integer
                error_current=left_error
                current_is_left=True
            else:
                numerator_base=shift_integer
                error_base=left_error
                numerator_current=shift_integer+1
                error_current=right_error
                current_is_left=False
            while True:
                k,error_new=divmod(error_current,error_base)
                choose_denominator=denominator_current+k*denominator_base
                if choose_denominator>max_denominator:
                    k=(max_denominator-denominator_current)//denominator_base
                    denominator_current=denominator_current+k*denominator_base
                    numerator_current=numerator_current+k*numerator_base
                    if current_is_left:
                        rational_left=cls._construct_new_object_for_simple(numerator_current,denominator_current)
                        rational_right=cls._construct_new_object_for_simple(numerator_base,denominator_base)
                    else:
                        rational_left=cls._construct_new_object_for_simple(numerator_base,denominator_base)
                        rational_right=cls._construct_new_object_for_simple(numerator_current,denominator_current)
                    return rational_left,rational_right
                error_current=error_base
                error_base=error_new
                denominator_current=denominator_base
                denominator_base=choose_denominator
                numerator_current,numerator_base=numerator_base,numerator_current+k*numerator_base
                current_is_left=not current_is_left
        def rational_bound(self,max_denominator:int=1)->tuple[Self,Self]:
            if not isinstance(max_denominator,int): raise TypeError('max_denominator must be an integer')
            if max_denominator<1: raise ValueError('max_denominator must be greater than or equal to 1') 
            self.simplify()
            if self.denominator<=max_denominator: result=self.__copy__(); return result,result
            return self._rational_bound_for_regular(max_denominator)
        def rational_floor(self,max_denominator:int=1)->Self: return self.rational_bound(max_denominator)[0]
        def rational_ceil(self,max_denominator:int=1)->Self: return self.rational_bound(max_denominator)[1]
        def rational_trunc(self,max_denominator:int=1)->Self:
            rational_left,rational_right=self.rational_bound(max_denominator)
            if self.numerator>=0: return rational_left
            return rational_right
        def rational_round(self,max_denominator:int=1)->Self:
            cls=type(self)
            if not isinstance(max_denominator,int): raise TypeError('max_denominator must be an integer')
            if max_denominator<1: raise ValueError('max_denominator must be greater than or equal to 1')
            self.simplify()
            if self.denominator<=max_denominator: return self.__copy__()
            if max_denominator==1:
                quotient,two_remainder=divmod(self.numerator,self.denominator)
                two_remainder<<=1
                if two_remainder>self.denominator: quotient+=1
                elif two_remainder==self.denominator and quotient&1: quotient+=1
                return cls._construct_new_object_for_simple(quotient,1)
            rational_left,rational_right=self._rational_bound_for_regular(max_denominator)
            compare_left=self.numerator*rational_left.denominator*rational_right.denominator*2
            compare_right=self.denominator*(rational_left.numerator*rational_right.denominator+rational_left.denominator*rational_right.numerator)
            if compare_left<compare_right: return rational_left
            if compare_left>compare_right: return rational_right
            return (rational_left if rational_left.denominator<rational_right.denominator else rational_right)
        @classmethod
        def _divmod_helper(cls,numerator_up:int,denominator_up:int,numerator_down:int,denominator_down:int,max_denominator:int=1)->tuple[Self,Self]:
            if denominator_down==0:
                if numerator_down!=0 and denominator_up==0 and numerator_up!=0:
                    sign_numerator_down=(1 if numerator_down>0 else -1)
                    sign_self_numerator=(1 if numerator_up>0 else -1)
                    quotient=cls._construct_new_object_for_straight(sign_numerator_down*sign_self_numerator,1)
                    remainder=cls.ZERO.__copy__()
                    return quotient,remainder
                result=cls.nan.__copy__()
                return result,result
            if denominator_up==0:
                if numerator_up!=0:
                    quotient=cls.ZERO.__copy__()
                    return quotient,cls._construct_new_object_for_straight(numerator_up,denominator_up)
                result=cls.nan.__copy__()
                return result,result
            if numerator_down==0:
                quotient=cls.ZERO.__copy__()
                return quotient,cls._construct_new_object_for_straight(numerator_up,denominator_up)
            numerator_temp,denominator_temp,_=cls._special_div(numerator_up,denominator_up,numerator_down,denominator_down)
            quotient=cls._construct_new_object_for_straight(numerator_temp,denominator_temp).rational_floor(max_denominator)
            remainder=quotient*(-numerator_down,denominator_down)+(numerator_up,denominator_up)
            return quotient,remainder
        @classmethod
        def rational_divmod(cls,dividend:RationalLike,divisor:RationalLike,max_denominator:int=1)->tuple[Self,Self]:
            numerator_down,denominator_down,_=cls._analyze_input_for_one_argument(divisor)
            numerator_up,denominator_up,_=cls._analyze_input_for_one_argument(dividend)
            return cls._divmod_helper(numerator_up,denominator_up,numerator_down,denominator_down,max_denominator)
        @classmethod
        def rational_quotient(cls,dividend:RationalLike,divisor:RationalLike,max_denominator:int=1)->Self:
            return cls.rational_divmod(dividend,divisor,max_denominator)[0]
        @classmethod
        def rational_mod(cls,dividend:RationalLike,divisor:RationalLike,max_denominator:int=1)->Self:
            return cls.rational_divmod(dividend,divisor,max_denominator)[1]
        def __divmod__(self,other:RationalLike)->tuple[Self,Self]: return type(self).rational_divmod(self,other)
        def __rdivmod__(self,other:RationalLike)->tuple[Self,Self]: return type(self).rational_divmod(other,self)
        def __floordiv__(self,other:RationalLike)->Self: return self.__divmod__(other)[0]
        def __rfloordiv__(self,other:RationalLike)->Self: return self.__rdivmod__(other)[0]
        __ifloordiv__=__floordiv__
        def __mod__(self,other:RationalLike)->Self: return self.__divmod__(other)[1]
        def __rmod__(self,other:RationalLike)->Self: return self.__rdivmod__(other)[1]
        __imod__=__mod__
        def float_bound(self)->tuple[float,float]:
            cls=type(self)
            if self.denominator==0:
                if self.numerator>0: return float('inf'),float('inf')
                if self.numerator<0: return float('-inf'),float('-inf')
                return float('nan'),float('nan')
            MAX_FLOAT=sys.float_info.max
            try: round_float=self.numerator/self.denominator
            except OverflowError:
                if self.numerator>0: return MAX_FLOAT,float('inf')
                return float('-inf'),-MAX_FLOAT
            round_rational=cls.convert_from_float(round_float)
            if round_rational<self: return round_float,math.nextafter(round_float,float('inf'))
            if round_rational>self: return math.nextafter(round_float,float('-inf')),round_float
            return round_float,round_float
        @staticmethod
        def _simplest_rational_in_interval(numerator_left:int,denominator_left:int,numerator_right:int,denominator_right:int)->IntegerRatio:
            cross_product_diff=numerator_right*denominator_left-numerator_left*denominator_right
            if cross_product_diff==1: return numerator_left+numerator_right,denominator_left+denominator_right
            shift_integer=numerator_left//denominator_left
            prev_numerator=1
            prev_denominator=0
            result_numerator=shift_integer
            result_denominator=1
            numerator_left,denominator_left,numerator_right,denominator_right=(denominator_right,numerator_right-shift_integer*denominator_right,
                                                                               denominator_left,numerator_left-shift_integer*denominator_left)
            shift_integer=numerator_left//denominator_left
            shift_integer_plus1=shift_integer+1
            right_integer=shift_integer_plus1+1 if denominator_right==0 else -(-numerator_right//denominator_right)
            while shift_integer_plus1>=right_integer:
                prev_numerator,result_numerator=result_numerator,result_numerator*shift_integer+prev_numerator
                prev_denominator,result_denominator=result_denominator,result_denominator*shift_integer+prev_denominator
                numerator_left,denominator_left,numerator_right,denominator_right=(denominator_right,numerator_right-shift_integer*denominator_right,
                                                                                   denominator_left,numerator_left-shift_integer*denominator_left)
                shift_integer=numerator_left//denominator_left
                shift_integer_plus1=shift_integer+1
                if denominator_right==0: break
                right_integer=-(-numerator_right//denominator_right)
            result_numerator=result_numerator*shift_integer_plus1+prev_numerator
            result_denominator=result_denominator*shift_integer_plus1+prev_denominator
            return result_numerator,result_denominator
        def simplest_rational_in_interval(self,other:Self)->Self:
            cls=type(self)
            root_cls=cls._family_root
            if not isinstance(other,root_cls): raise TypeError(f'other must be an instance of {root_cls.__name__}')
            if self.denominator==0 or other.denominator==0: raise ValueError('Cannot find simplest rational in interval including infinity or NaN')
            cross_product_diff=other.numerator*self.denominator-self.numerator*other.denominator
            if cross_product_diff<=0: raise ValueError('The precondition is not satisfied: self < other')
            left_integer=self.numerator//self.denominator
            right_integer=-(-other.numerator//other.denominator)
            if left_integer+1<right_integer: raise ValueError('The precondition is not satisfied: floor(self) + 1 == floor(other)')
            if not self._is_simplified: self.simplify()
            if not other._is_simplified: other.simplify()
            numerator,denominator=cls._simplest_rational_in_interval(self.numerator,self.denominator,other.numerator,other.denominator)
            return cls._construct_new_object_for_simple(numerator,denominator)
        @classmethod
        def _input_iterator(cls,*args:RationalLike)->Iterator[IntegerRatio]:
            # You should not input one tuple of two int as two integer.
            if len(args)==1:
                arg=args[0]
                try: numerator,denominator,_=cls._analyze_input_for_one_argument(arg); yield numerator,denominator
                except TypeError:
                    for item in arg: numerator,denominator,_=cls._analyze_input_for_one_argument(item); yield numerator,denominator
            else:
                for arg in args: numerator,denominator,_=cls._analyze_input_for_one_argument(arg); yield numerator,denominator
        @classmethod
        def _sum_integer_ratios(cls,iterable_rational_tuples:Iterable[IntegerRatio])->Self:
            numerator_result=0
            denominator_result=1
            iter_loop=iter(iterable_rational_tuples)
            for numerator,denominator in iter_loop:
                if denominator==0:
                    if numerator>0:
                        for re_numerator,re_denominator in iter_loop:
                            if re_denominator==0 and re_numerator<=0: return cls.nan.__copy__()
                        return cls.infty.__copy__()
                    elif numerator<0:
                        for re_numerator,re_denominator in iter_loop:
                            if re_denominator==0 and re_numerator>=0: return cls.nan.__copy__()
                        return cls.minfty.__copy__()
                    return cls.nan.__copy__()
                if numerator==0: continue
                numerator_result=numerator_result*denominator+numerator*denominator_result
                denominator_result*=denominator
            return cls._construct_new_object_for_straight(numerator_result,denominator_result)
        @classmethod
        def sum(cls,*args:RationalLike)->Self: return cls._sum_integer_ratios(cls._input_iterator(*args))
        @classmethod
        def _product_integer_ratios(cls,iterable_rational_tuples:Iterable[IntegerRatio])->Self:
            numerator_result=1
            denominator_result=1
            iter_loop=iter(iterable_rational_tuples)
            for numerator,denominator in iter_loop:
                if denominator==0:
                    numerator_result*=numerator
                    if numerator_result>0: numerator_result=1
                    elif numerator_result<0: numerator_result=-1
                    else: return cls.nan.__copy__()
                    for numerator,_ in iter_loop:
                        if numerator<0: numerator_result=-numerator_result
                        elif numerator==0: return cls.nan.__copy__()
                    if numerator_result==1: return cls.infty.__copy__()
                    return cls.minfty.__copy__()
                if numerator==0:
                    for _,denominator in iter_loop:
                        if denominator==0: return cls.nan.__copy__()
                    return cls.ZERO.__copy__()
                numerator_result*=numerator
                denominator_result*=denominator
            return cls._construct_new_object_for_straight(numerator_result,denominator_result)
        @classmethod
        def product(cls,*args:RationalLike)->Self: return cls._product_integer_ratios(cls._input_iterator(*args))
        @staticmethod
        def _iroot_integer(n:int,degree:int,n_bit_len:int)->tuple[int,bool]:
            degree_minus_1=degree-1
            init_exponent=-(-n_bit_len//degree)
            old_guess=1<<(init_exponent)
            quotient,remainder=divmod(n,old_guess**degree_minus_1)
            new_guess=(degree_minus_1*old_guess+quotient)//degree
            while new_guess<old_guess:
                old_guess=new_guess
                quotient,remainder=divmod(n,old_guess**degree_minus_1)
                new_guess=(degree_minus_1*old_guess+quotient)//degree
            is_exact=quotient==old_guess and remainder==0
            return old_guess,is_exact
        @classmethod
        def iroot_integer(cls,n:int,degree:int)->tuple[int,bool]:
            if not isinstance(n,int): raise TypeError('n must be an integer')
            if n<0: raise ValueError('n must be non-negative')
            if not isinstance(degree,int): raise TypeError('degree must be an integer')
            if degree<=0: raise ValueError('degree must be positive')
            if n<=1: return n,True
            if degree==1: return n,True
            bit_len=n.bit_length()
            if degree>=bit_len: return 1,False
            return cls._iroot_integer(n,degree,bit_len)
        @classmethod
        def _iroot_rational(cls,numerator:int,denominator:int,degree:int)->tuple[IntegerRatio,IntegerRatio,bool]:
            numerator_root,is_numerator_exact=cls._iroot_integer(numerator,degree,numerator.bit_length())
            denominator_root,is_denominator_exact=cls._iroot_integer(denominator,degree,denominator.bit_length())
            is_exact=True
            if not is_numerator_exact:
                is_exact=False
                numerator_right=numerator_root+1
            else: numerator_right=numerator_root
            if not is_denominator_exact:
                is_exact=False
                denominator_right=denominator_root+1
            else: denominator_right=denominator_root
            return (numerator_root,denominator_right),(numerator_right,denominator_root),is_exact
        def iroot(self,degree:int)->tuple[Self|None,bool]:
            '''
            When the nth root is a rational number, return the rational number and True. Otherwise, return None and False.
            '''
            if not isinstance(degree,int): raise TypeError('degree must be an integer')
            if degree<=0: raise ValueError('degree must be positive')
            cls=type(self)
            numerator,denominator=self.as_integer_ratio()
            if numerator<0: raise ValueError('Cannot compute root of negative rational')
            if denominator==0:
                if numerator>0: return cls.infty.__copy__(),True
                return cls.nan.__copy__(),False
            answer_left,answer_right,is_exact=cls._iroot_rational(numerator,denominator,degree)
            if is_exact: return cls._construct_new_object_for_straight(*answer_left),True
            return None,False
        @classmethod
        def _check_input_for_pow(cls,numerator_base:int,denominator_base:int,numerator_exponent:int,denominator_exponent:int)->Self|R|None:
            if denominator_base==0:
                if numerator_base>0:
                    if numerator_exponent>0: return cls.infty.__copy__()
                    elif numerator_exponent<0: return cls.ZERO.__copy__()
                    else: return cls.nan.__copy__()
                elif numerator_base<0: raise ValueError('Base must be non-negative.')
                else: return cls.nan.__copy__()
            elif numerator_base==0:
                if denominator_exponent==0: return cls.nan.__copy__()
                elif numerator_exponent>0: return cls.ZERO.__copy__()
                elif numerator_exponent<0: return cls.nan.__copy__()
                else: return cls.ONE.__copy__()
            elif numerator_base<0: raise ValueError('Base must be non-negative.')
            else: return None
        @classmethod
        def _pow_helper(cls,numerator_base:int,denominator_base:int,numerator_exponent:int,denominator_exponent:int)->Self|R:
            if numerator_exponent<0:
                numerator_base,denominator_base=denominator_base,numerator_base
                numerator_exponent=-numerator_exponent
            if denominator_exponent==0:
                if numerator_exponent==0: return cls.nan.__copy__()
                if numerator_base<denominator_base: return cls.ZERO.__copy__()
                if numerator_base>denominator_base: return cls.infty.__copy__()
                return cls.ONE.__copy__()
            if numerator_exponent==0: return cls.ONE.__copy__()
            if numerator_base==denominator_base: return cls.ONE.__copy__()
            rational_left,rational_right,is_rational=cls._iroot_rational(numerator_base,denominator_base,denominator_exponent)
            if is_rational:
                numerator_result,denominator_result=rational_left
                return cls._construct_new_object_for_simple(numerator_result**numerator_exponent,denominator_result**numerator_exponent)
            left_scalar=denominator_base**numerator_exponent
            right_scalar=numerator_base**numerator_exponent
            def sign_func(numerator,denominator):
                if numerator<=0: return -1
                compare_left=left_scalar*(numerator**denominator_exponent)
                compare_right=right_scalar*(denominator**denominator_exponent)
                if compare_left<compare_right: return -1
                else: return 1
            left_n,left_d=rational_left
            right_n,right_d=rational_right
            interval_left=(left_n**numerator_exponent,left_d**numerator_exponent)
            interval_right=(right_n**numerator_exponent,right_d**numerator_exponent)
            return cls._Real(sign_func,is_possible_rational=False,is_possible_irrational=True,left=interval_left,right=interval_right)
        def __pow__(self,exponent:RationalLike)->Self|R|NotImplementedType:
            cls=type(self)
            numerator_base,denominator_base=self.as_integer_ratio()
            try: numerator_exponent,denominator_exponent,is_simple=cls._analyze_input_for_one_argument(exponent)
            except TypeError: return NotImplemented
            result=cls._check_input_for_pow(numerator_base,denominator_base,numerator_exponent,denominator_exponent)
            if result is not None: return result
            if not is_simple: numerator_exponent,denominator_exponent=cls._simplify(numerator_exponent,denominator_exponent)
            return cls._pow_helper(numerator_base,denominator_base,numerator_exponent,denominator_exponent)
        def __rpow__(self,base:RationalLike)->Self|R|NotImplementedType:
            cls=type(self)
            numerator_exponent,denominator_exponent=self.as_integer_ratio()
            try: numerator_base,denominator_base,is_simple=cls._analyze_input_for_one_argument(base)
            except TypeError: return NotImplemented
            result=cls._check_input_for_pow(numerator_base,denominator_base,numerator_exponent,denominator_exponent)
            if result is not None: return result
            if not is_simple: numerator_base,denominator_base=cls._simplify(numerator_base,denominator_base)
            return cls._pow_helper(numerator_base,denominator_base,numerator_exponent,denominator_exponent)
        __ipow__=__pow__
        @classmethod
        def _get_primitive_integer(cls,n:int)->tuple[int,int]:
            if n<=3: return n,1
            n_bit_len=n.bit_length()
            max_degree=n_bit_len-1
            for degree in range(max_degree,1,-1):
                root,is_exact=cls._iroot_integer(n,degree,n_bit_len)
                if is_exact: return root,degree
            return n,1
        @classmethod
        def _get_primitive_rational(cls,numerator:int,denominator:int)->tuple[IntegerRatio,int]:
            if denominator==1:
                primitive,degree=cls._get_primitive_integer(numerator)
                return (primitive,1),degree
            if numerator==1:
                primitive,degree=cls._get_primitive_integer(denominator)
                return (1,primitive),degree
            numerator_primitive,numerator_degree=cls._get_primitive_integer(numerator)
            denominator_primitive,denominator_degree=cls._get_primitive_integer(denominator)
            common_degree=math.gcd(numerator_degree,denominator_degree)
            return (numerator_primitive**(numerator_degree//common_degree),denominator_primitive**(denominator_degree//common_degree)),common_degree
        @staticmethod
        def log_2_bounds_for_int(integer:int)->tuple[int,int]:
            if integer&(integer-1):
                right=integer.bit_length()
                left=right-1
            else:
                right=integer.bit_length()-1
                left=right
            return left,right
        @classmethod
        def _log_2_bounds_for_rational(cls,numerator:int,denominator:int)->tuple[int,int]:
            if denominator==1:
                left,right=cls.log_2_bounds_for_int(numerator)
                return left,right
            numerator_left,numerator_right=cls.log_2_bounds_for_int(numerator)
            denominator_left,denominator_right=cls.log_2_bounds_for_int(denominator)
            left=numerator_left-denominator_right
            right=left+1
            if (denominator<<right)<=numerator: return right,right+1
            return left,right
        @classmethod
        def logarithm(cls,base:RationalLike,argument:RationalLike)->Self|R:
            numerator_base,denominator_base,base_is_simple=cls._analyze_input_for_one_argument(base)
            numerator_argument,denominator_argument,argument_is_simple=cls._analyze_input_for_one_argument(argument)
            if denominator_base==0 or denominator_argument==0: raise ValueError('base and argument must be finite')
            if numerator_base<=0: raise ValueError('base must be positive')
            if numerator_argument<=0: raise ValueError('argument must be positive')
            if numerator_base==denominator_base: raise ValueError('base must not be 1')
            if numerator_argument==denominator_argument: return cls.ZERO
            if not base_is_simple: numerator_base,denominator_base=cls._simplify(numerator_base,denominator_base)
            if not argument_is_simple: numerator_argument,denominator_argument=cls._simplify(numerator_argument,denominator_argument)
            base_primitive,base_degree=cls._get_primitive_rational(numerator_base,denominator_base)
            argument_primitive,argument_degree=cls._get_primitive_rational(numerator_argument,denominator_argument)
            if base_primitive==argument_primitive: return cls._construct_new_object_for_straight(argument_degree,base_degree)
            if (argument_primitive[1],argument_primitive[0])==base_primitive: return cls._construct_new_object_for_straight(-argument_degree,base_degree)
            if numerator_base<denominator_base:
                outside_sign=-1
                numerator_base,denominator_base=denominator_base,numerator_base
            else:
                outside_sign=1
            if numerator_argument<denominator_argument:
                outside_sign=-outside_sign
                numerator_argument,denominator_argument=denominator_argument,numerator_argument
            def positive_sign_func(numerator:int,denominator:int)->CompareResult:
                if numerator<=0: return -1
                compare_left=(numerator_base**numerator)*(denominator_argument**denominator)
                compare_right=(denominator_base**numerator)*(numerator_argument**denominator)
                if compare_left<compare_right: return -1
                else: return 1
            argument_low,argument_high=cls._log_2_bounds_for_rational(numerator_argument,denominator_argument)
            if numerator_base>=2*denominator_base:
                base_low,base_high=cls._log_2_bounds_for_rational(numerator_base,denominator_base)
                interval_left=(argument_low,base_high)
                interval_right=(argument_high,base_low)
            else:
                interval_left=(argument_low,1)
                interval_right=(argument_high*61*(numerator_base+denominator_base),176*(numerator_base-denominator_base))
            if outside_sign==-1:
                def negative_sign_func(numerator,denominator): return -positive_sign_func(-numerator,denominator)
                new_left=(-interval_right[0],interval_right[1])
                new_right=(-interval_left[0],interval_left[1])
                return cls._Real(negative_sign_func,is_possible_rational=False,is_possible_irrational=True,left=new_left,right=new_right)
            return cls._Real(positive_sign_func,is_possible_rational=False,is_possible_irrational=True,left=interval_left,right=interval_right)
    class RealNumber[Q:Rational](metaclass=ComputableType.RealType):
        """
        Overview:
            ``RealNumber`` represents a computable real value through a rational sign oracle.
            Oracle contract:
            - ``-1``: queried rational is less than the real value
            - ``0``: queried rational equals the real value
            - ``1``: queried rational is greater than the real value

        Basic Usage:
            ``ComputableReal(x, is_possible_rational=True, is_possible_irrational=True, left=None, right=None)``
            supports two input modes:
            - exact rational input (or rational-like input): creates a rational-only object immediately.
            - sign-function input: creates a potentially rational/irrational computable real with optional
              initial interval hints ``left`` and ``right``.

            Typical usage flow:
            1. Create a value from a rational or sign function.
            2. Query/compare it through public APIs.
            3. Request tighter bounds only when needed.

        Data Structure Semantics:
            Number-kind flags:
            ``_is_possible_rational`` and ``_is_possible_irrational`` encode what is still possible:
            - rational-only: ``True, False``
            - irrational-only: ``False, True``
            - undecided: ``True, True``
            ``False, False`` is invalid and rejected at construction.

            Two interval layers are tracked in parallel:
            - dynamic query interval: ``_nearest_left`` / ``_nearest_right`` (latest known global bounds),
            - structural interval: ``_left_rational`` / ``_right_rational`` (regularized bounds used by
              denominator-constrained and structure-driven refinement).

            They are intentionally separate so the class can combine:
            - fast arbitrary updates from sign queries and operator evaluation, and
            - efficient regular refinement when precision constraints are requested.

        Core State Attributes:
            ``_init_sign_func``:
                Internal sign function with an extra ``input_is_regular`` channel.
                Internal refinement paths call this function and may update interval state.
            ``_sign_func``:
                Public-facing wrapper around ``_init_sign_func`` that handles denominator edge cases.
                External queries should use this path (for example via ``sign_func(...)``).
            ``_is_possible_rational``:
                Whether the value may still be rational.
            ``_is_possible_irrational``:
                Whether the value may still be irrational.
            ``_nearest_left``:
                Best known lower rational bound from dynamic sign queries.
            ``_nearest_right``:
                Best known upper rational bound from dynamic sign queries.
            ``_left_answer``:
                Boundary answer when queried rational equals ``_nearest_left``.
                Usually ``-1`` for strict lower endpoint, ``0`` when endpoint is exact.
            ``_right_answer``:
                Boundary answer when queried rational equals ``_nearest_right``.
                Usually ``1`` for strict upper endpoint, ``0`` when endpoint is exact.
            ``_left_rational``:
                Left endpoint of the structural (regularized) interval.
            ``_right_rational``:
                Right endpoint of the structural (regularized) interval.
            ``_is_regular``:
                Whether the structural interval is synchronized with current dynamic history.
                Non-regular updates set this flag to ``False``; ``_regularize()`` restores consistency.

        Public API (Purpose):
            ``sign_func(*args)``:
                Query the sign oracle with rational-like input.
            ``current_bound(depend_on_structure=False)``:
                Return current known interval. Dynamic bounds by default; structural bounds when requested.
            ``current_width(depend_on_structure=False)``:
                Return interval width as ``RationalNumber`` (interned/frozen).
            ``refine_to_width(epsilon)``:
                Tighten the structural interval until width <= epsilon.
            ``rational_bound(max_denominator)``:
                Return best bracketing rationals under denominator constraint.
            ``as_integer_ratio(fallback_max_denominator=None)``:
                Return exact ratio when known rational; otherwise optional bounded fallback approximation.
            ``to_scientific_notation(...)`` and ``float_bound()``:
                Render/convert using interval-safe numeric approximation.
            ``compare(other)`` and rich comparisons:
                Robust ordering/equality through interval refinement and sign evaluation.
            ``keep_away_from_zero()``:
                Force denominator-side safety before division (raises for exact zero).
            ``root_finding(func, interval)``:
                Build a real root object/value from a sign-changing interval.

        Implicit DAG:
            Every ``RealNumber`` created by arithmetic becomes a downstream node whose sign function
            closes over upstream operands. Together, all ``RealNumber`` objects form a directed acyclic
            computation graph.

            This graph is implicit: dependency edges are represented by Python closures, not by an
            explicit adjacency structure. This is a memory optimization.

            Precision propagation is demand-driven:
            - asking a downstream node for tighter bounds/sign may trigger upstream refinement,
            - once an upstream node is refined, other downstream nodes sharing it can run faster,
            - discovered information is reused; known interval knowledge is not discarded.

            ``+``, ``-``, ``*``, ``/`` and reflected/in-place forms are generated by the metaclass and
            executed through a shared refinement framework that realizes this propagation behavior.

        Constants:
            ``PI`` and ``E`` are built-in computable-irrational ``RealNumber`` constants.
        """
        _Rational:ClassVar[type[Q]]
        _family_root:ClassVar[Real]
        _container_class:ClassVar["ComputableNumber"]
        _init_sign_func:SignFunctionWithInfo
        _sign_func:SignFunction
        _is_possible_rational:bool
        _is_possible_irrational:bool
        _nearest_left:Q
        _nearest_right:Q
        _left_answer:CompareResult
        _right_answer:CompareResult
        _left_rational:Q
        _right_rational:Q
        _floor:int
        _ceil:int
        _is_regular:bool
        _exact_rational:Q|None=None
        _exponent_10:int|None=None
        _float_bound:tuple[float,float]|None=None
        _hash:int|None=None

        def _int_bound_for_init(self,left:RationalLike=None,right:RationalLike=None)->tuple[int,int]|Q:
            cls=type(self)
            Rationalclass=cls._Rational
            analyzer=Rationalclass._analyze_input_for_one_argument
            if left is not None:
                numerator_left,denominator_left,_=analyzer(left)
                if denominator_left==0:
                    if numerator_left<0: left=None
                    elif numerator_left>0: raise ValueError('The left endpoint cannot be positive infinity')
                    else: raise ValueError('The left endpoint cannot be NaN')
            if right is not None:
                numerator_right,denominator_right,_=analyzer(right)
                if denominator_right==0:
                    if numerator_right>0: right=None
                    elif numerator_right<0: raise ValueError('The right endpoint cannot be negative infinity')
                    else: raise ValueError('The right endpoint cannot be NaN')
            if left is None:
                if right is None:
                    compare_result=self._init_sign_func(0,1)
                    if compare_result==-1:
                        left_integer=0
                        right_integer=1
                        compare_result=self._init_sign_func(right_integer,1)
                        while compare_result==-1:
                            left_integer=right_integer
                            right_integer<<=1
                            compare_result=self._init_sign_func(right_integer,1)
                        if compare_result==0: return Rationalclass(right_integer,1)
                    elif compare_result==1:
                        right_integer=0
                        left_integer=-1
                        compare_result=self._init_sign_func(left_integer,1)
                        while compare_result==1:
                            right_integer=left_integer
                            left_integer<<=1
                            compare_result=self._init_sign_func(left_integer,1)
                        if compare_result==0: return Rationalclass(left_integer,1)
                    else: return Rationalclass.ZERO
                else:
                    compare_result=self._init_sign_func(numerator_right,denominator_right)
                    if compare_result==1:
                        right_integer=-(-numerator_right//denominator_right)
                        step=1
                        left_integer=right_integer-step
                        compare_result=self._init_sign_func(left_integer,1)
                        while compare_result==1:
                            step<<=1
                            right_integer=left_integer
                            left_integer-=step
                            compare_result=self._init_sign_func(left_integer,1)
                        if compare_result==0: return Rationalclass(left_integer,1)
                    elif compare_result==0: return Rationalclass(numerator_right,denominator_right)
                    else: raise ValueError('The right endpoint must be greater than or equal to the real number')
            else:
                if right is None:
                    compare_result=self._init_sign_func(numerator_left,denominator_left)
                    if compare_result==-1:
                        left_integer=numerator_left//denominator_left
                        step=1
                        right_integer=left_integer+step
                        compare_result=self._init_sign_func(right_integer,1)
                        while compare_result==-1:
                            step<<=1
                            left_integer=right_integer
                            right_integer+=step
                            compare_result=self._init_sign_func(right_integer,1)
                        if compare_result==0: return Rationalclass(right_integer,1)
                    elif compare_result==0: return Rationalclass(numerator_left,denominator_left)
                    else: raise ValueError('The left endpoint must be less than or equal to the real number')
                else:
                    right_diff_left=numerator_right*denominator_left-numerator_left*denominator_right
                    if right_diff_left>0:
                        compare_result_left=self._init_sign_func(numerator_left,denominator_left)
                        if compare_result_left==-1:
                            compare_result_right=self._init_sign_func(numerator_right,denominator_right)
                            if compare_result_right==1: left_integer=numerator_left//denominator_left; right_integer=-(-numerator_right//denominator_right)
                            elif compare_result_right==0: return Rationalclass(numerator_right,denominator_right)
                            else: raise ValueError('The right endpoint must be greater than or equal to the real number')
                        elif compare_result_left==1: raise ValueError('The left endpoint must be less than or equal to the real number')
                        else:
                            compare_result_right=self._init_sign_func(numerator_right,denominator_right)
                            if compare_result_right==1: return Rationalclass(numerator_left,denominator_left)
                            elif compare_result_right==0: raise ValueError('The left and right endpoints are equal to the real number but they are not equal')
                            else: raise ValueError('The right endpoint must be greater than or equal to the real number')
                    elif right_diff_left==0:
                        if self._init_sign_func(numerator_left,denominator_left)==0: return Rationalclass(numerator_left,denominator_left)
                        else: raise ValueError('The left and right endpoints are equal but not equal to the real number')
                    else: raise ValueError('The left endpoint must be less than the right endpoint')
            while left_integer+1<right_integer:
                two_mid=left_integer+right_integer
                mid=two_mid>>1
                if mid<<1!=two_mid and mid&1: mid+=1
                compare_result=self._init_sign_func(mid,1)
                if compare_result==-1: left_integer=mid
                elif compare_result==1: right_integer=mid
                else: return Rationalclass(mid,1)
            return left_integer,right_integer
        @staticmethod
        def _wrapper_for_special_cases(sign_function:SignFunctionWithInfo)->SignFunction:
            def wrapper(numerator:int,denominator:int)->CompareResult:
                if denominator==0:
                    if numerator>0: return 1
                    if numerator<0: return -1
                    raise ValueError('numerator and denominator cannot both be zero')
                return sign_function(numerator,denominator)
            return wrapper
        def _wrapper_for_sign_function(self,sign_function:SignFunction)->tuple[SignFunctionWithInfo,SignFunction]:
            def original_sign_func(numerator:int,denominator:int,input_is_regular:bool=False)->CompareResult:
                left=self._nearest_left
                compare_left=numerator*left.denominator
                compare_right=denominator*left.numerator
                if compare_left<=compare_right: return (-1 if compare_left!=compare_right else self._left_answer)
                right=self._nearest_right
                compare_left=numerator*right.denominator
                compare_right=denominator*right.numerator
                if compare_left>=compare_right: return (1 if compare_left!=compare_right else self._right_answer)
                compare_result=sign_function(numerator,denominator)
                input_rational=type(self)._Rational(numerator,denominator)
                if compare_result==-1:
                    self._nearest_left=input_rational
                    if input_is_regular: self._left_rational=input_rational
                    elif self._is_regular: self._is_regular=False
                elif compare_result==1:
                    self._nearest_right=input_rational
                    if input_is_regular: self._right_rational=input_rational
                    elif self._is_regular: self._is_regular=False
                else: self._rationalized(input_rational)
                return compare_result
            result_func=type(self)._wrapper_for_special_cases(original_sign_func)
            return original_sign_func,result_func
        @classmethod
        def _rational_to_sign_func(cls,numerator_input:int,denominator_input:int)->SignFunctionWithInfo:
            if denominator_input==0: raise ValueError('The input must be a finite number.')
            RaN=cls._Rational
            numerator_input,denominator_input=RaN._simplify(numerator_input,denominator_input)
            if numerator_input>0:
                def sign_func(numerator:int,denominator:int,input_is_regular:bool=False)->CompareResult:
                    if numerator<=0: return -1
                    compare_left=numerator*denominator_input
                    compare_right=denominator*numerator_input
                    if compare_left<compare_right: return -1
                    if compare_left>compare_right: return 1
                    return 0
            elif numerator_input<0:
                def sign_func(numerator:int,denominator:int,input_is_regular:bool=False)->CompareResult:
                    if numerator>=0: return 1
                    compare_left=numerator*denominator_input
                    compare_right=denominator*numerator_input
                    if compare_left<compare_right: return -1
                    if compare_left>compare_right: return 1
                    return 0
            else:
                def sign_func(numerator:int,denominator:int,input_is_regular:bool=False)->CompareResult:
                    if numerator<0: return -1
                    if numerator>0: return 1
                    return 0
            return sign_func
        def _rationalized(self,rational:Q)->None:
            if not self._is_possible_rational: raise ValueError('This number is exactly rational.')
            if self._is_possible_irrational: self._is_possible_irrational=False
            cls=type(self)
            self._exact_rational=rational
            new_sign_func=cls._rational_to_sign_func(rational.numerator,rational.denominator)
            self._init_sign_func=new_sign_func
            self._sign_func=cls._wrapper_for_special_cases(new_sign_func)
            self._nearest_left=rational
            self._nearest_right=rational
            self._left_answer=0
            self._right_answer=0
            self._left_rational=rational
            self._right_rational=rational
            if not self._is_regular: self._is_regular=True
        @classmethod
        def _convert_from_rational(cls,rational:Q)->Self:
            rational=rational.intern()
            numerator,denominator=rational.numerator,rational.denominator
            sign_func=cls._rational_to_sign_func(numerator,denominator)
            instance=cls.__new__(cls)
            instance._init_sign_func=sign_func
            instance._sign_func=cls._wrapper_for_special_cases(sign_func)
            instance._is_possible_rational=True
            instance._is_possible_irrational=False
            instance._nearest_left=rational
            instance._nearest_right=rational
            instance._left_answer=0
            instance._right_answer=0
            instance._left_rational=rational
            instance._right_rational=rational
            instance._floor=numerator//denominator
            instance._ceil=-(-numerator//denominator)
            instance._is_regular=True
            instance._exact_rational=rational
            return instance
        def _regularize(self)->None:
            if self._is_regular: return
            left_rational=self._left_rational
            right_rational=self._right_rational
            left_query=self._nearest_left
            right_query=self._nearest_right
            numerator_left,denominator_left=left_rational.numerator,left_rational.denominator
            numerator_right,denominator_right=right_rational.numerator,right_rational.denominator
            numerator_left_query,denominator_left_query=left_query.numerator,left_query.denominator
            numerator_right_query,denominator_right_query=right_query.numerator,right_query.denominator
            denominator_mid=denominator_left+denominator_right
            numerator_mid=numerator_left+numerator_right
            while True:
                if numerator_mid*denominator_left_query<=denominator_mid*numerator_left_query:
                    left_error=denominator_left*numerator_left_query-numerator_left*denominator_left_query
                    right_error=numerator_right*denominator_left_query-denominator_right*numerator_left_query
                    k=left_error//right_error
                    denominator_left+=k*denominator_right
                    numerator_left+=k*numerator_right
                elif numerator_mid*denominator_right_query>=denominator_mid*numerator_right_query:
                    left_error=denominator_left*numerator_right_query-numerator_left*denominator_right_query
                    right_error=numerator_right*denominator_right_query-denominator_right*numerator_right_query
                    k=right_error//left_error
                    denominator_right+=k*denominator_left
                    numerator_right+=k*numerator_left
                else: break
                denominator_mid=denominator_left+denominator_right
                numerator_mid=numerator_left+numerator_right
            constructor=type(self)._Rational._new_for_simple
            if denominator_left!=left_rational.denominator: self._left_rational=constructor(numerator_left,denominator_left)
            if denominator_right!=right_rational.denominator: self._right_rational=constructor(numerator_right,denominator_right)
            self._is_regular=True
        def _find_rational_for_regular(self)->None:
            left_rational=self._left_rational
            right_rational=self._right_rational
            numerator_left,denominator_left=left_rational.numerator,left_rational.denominator
            numerator_right,denominator_right=right_rational.numerator,right_rational.denominator
            while True:
                denominator_mid=denominator_left+denominator_right
                numerator_mid=numerator_left+numerator_right
                compare_result=self._init_sign_func(numerator_mid,denominator_mid)
                if compare_result==-1:
                    denominator_left=denominator_mid
                    numerator_left=numerator_mid
                elif compare_result==1:
                    denominator_right=denominator_mid
                    numerator_right=numerator_mid
                else: break
        def rational_bound(self,max_denominator:int)->tuple[Q,Q]:
            if not isinstance(max_denominator,int): raise TypeError('max_denominator must be an integer')
            if max_denominator<1: raise ValueError('max_denominator must be positive')
            Rationalclass=type(self)._Rational
            constructor=Rationalclass._new_for_simple
            if max_denominator==1: return constructor(self._floor,1),constructor(self._ceil,1)
            if not self._is_possible_irrational: return self._exact_rational.rational_bound(max_denominator)
            left_rational=self._left_rational
            right_rational=self._right_rational
            numerator_left,denominator_left=left_rational.numerator,left_rational.denominator
            numerator_right,denominator_right=right_rational.numerator,right_rational.denominator
            if denominator_left>max_denominator:
                if denominator_right>max_denominator:
                    if denominator_left<denominator_right:
                        numerator_small=numerator_left
                        denominator_small=denominator_left
                        numerator_large=numerator_right
                        denominator_large=denominator_right
                        small_is_left=True
                    else:
                        numerator_small=numerator_right
                        denominator_small=denominator_right
                        numerator_large=numerator_left
                        denominator_large=denominator_left
                        small_is_left=False
                    while True:
                        k,denominator_small_new=divmod(denominator_large,denominator_small)
                        denominator_large=denominator_small
                        denominator_small=denominator_small_new
                        numerator_small,numerator_large=numerator_large-k*numerator_small,numerator_small
                        small_is_left=not small_is_left
                        if denominator_small<=max_denominator:
                            k=-((max_denominator-denominator_large)//denominator_small)
                            denominator_large-=k*denominator_small
                            numerator_large-=k*numerator_small
                            if small_is_left: return constructor(numerator_small,denominator_small),constructor(numerator_large,denominator_large)
                            else: return constructor(numerator_large,denominator_large),constructor(numerator_small,denominator_small)
                else:
                    k=-((max_denominator-denominator_left)//denominator_right)
                    denominator_left-=k*denominator_right
                    numerator_left-=k*numerator_right
                    return constructor(numerator_left,denominator_left),right_rational
            elif denominator_right>max_denominator:
                k=-((max_denominator-denominator_right)//denominator_left)
                denominator_right-=k*denominator_left
                numerator_right-=k*numerator_left
                return left_rational,constructor(numerator_right,denominator_right)
            else:
                denominator_mid=denominator_left+denominator_right
                if denominator_mid<=max_denominator:
                    numerator_mid=numerator_left+numerator_right
                    left_query=self._nearest_left
                    right_query=self._nearest_right
                    numerator_left_query,denominator_left_query=left_query.numerator,left_query.denominator
                    numerator_right_query,denominator_right_query=right_query.numerator,right_query.denominator
                    while True:
                        if numerator_mid*denominator_left_query<=denominator_mid*numerator_left_query:
                            left_error=denominator_left*numerator_left_query-numerator_left*denominator_left_query
                            right_error=numerator_right*denominator_left_query-denominator_right*numerator_left_query
                            k=left_error//right_error
                            choose_denominator=denominator_left+k*denominator_right
                            if choose_denominator>max_denominator:
                                k=(max_denominator-denominator_left)//denominator_right
                                denominator_left+=k*denominator_right
                                numerator_left+=k*numerator_right
                                result_left=constructor(numerator_left,denominator_left)
                                result_right=constructor(numerator_right,denominator_right)
                                self._left_rational=result_left
                                self._right_rational=result_right
                                return result_left,result_right
                            denominator_left=choose_denominator
                            numerator_left+=k*numerator_right
                        elif numerator_mid*denominator_right_query>=denominator_mid*numerator_right_query:
                            left_error=denominator_left*numerator_right_query-numerator_left*denominator_right_query
                            right_error=numerator_right*denominator_right_query-denominator_right*numerator_right_query
                            k=right_error//left_error
                            choose_denominator=k*denominator_left+denominator_right
                            if choose_denominator>max_denominator:
                                k=(max_denominator-denominator_right)//denominator_left
                                denominator_right+=k*denominator_left
                                numerator_right+=k*numerator_left
                                result_left=constructor(numerator_left,denominator_left)
                                result_right=constructor(numerator_right,denominator_right)
                                self._left_rational=result_left
                                self._right_rational=result_right
                                return result_left,result_right
                            denominator_right=choose_denominator
                            numerator_right+=k*numerator_left
                        else: break
                        denominator_mid=denominator_left+denominator_right
                        if denominator_mid>max_denominator:
                            result_left=constructor(numerator_left,denominator_left)
                            result_right=constructor(numerator_right,denominator_right)
                            self._left_rational=result_left
                            self._right_rational=result_right
                            return result_left,result_right
                        numerator_mid=numerator_left+numerator_right
                    while True:
                        compare_result=self._init_sign_func(numerator_mid,denominator_mid)
                        if compare_result==-1:
                            denominator_left=denominator_mid
                            numerator_left=numerator_mid
                            denominator_mid=denominator_left+denominator_right
                            if denominator_mid>max_denominator:
                                result_left=constructor(numerator_left,denominator_left)
                                result_right=constructor(numerator_right,denominator_right)
                                self._left_rational=result_left
                                self._right_rational=result_right
                                self._is_regular=True
                                return result_left,result_right
                            numerator_mid=numerator_left+numerator_right
                        elif compare_result==1:
                            denominator_right=denominator_mid
                            numerator_right=numerator_mid
                            denominator_mid=denominator_left+denominator_right
                            if denominator_mid>max_denominator:
                                result_left=constructor(numerator_left,denominator_left)
                                result_right=constructor(numerator_right,denominator_right)
                                self._left_rational=result_left
                                self._right_rational=result_right
                                self._is_regular=True
                                return result_left,result_right
                            numerator_mid=numerator_left+numerator_right
                        else: return self._exact_rational,self._exact_rational
                else: return left_rational,right_rational
        def __init__(self,*args):
            cls=type(self)
            Rationalclass=cls._Rational
            constructor=Rationalclass._new_for_simple
            args_length=len(args)
            if args_length==1:
                result_rational=args[0]
                left_integer,right_integer=result_rational.int_bound()
                self._is_regular=True
                self._is_possible_rational=True
                self._is_possible_irrational=False
                self._rationalized(result_rational)
                self._floor=left_integer
                self._ceil=right_integer
            elif args_length==2:
                is_possible_rational,is_possible_irrational=args
                if not is_possible_rational and self._is_possible_rational: self._is_possible_rational=False
                if not is_possible_irrational and self._is_possible_irrational: self._regularize(); self._find_rational_for_regular()
            elif args_length==5:
                left,right,sign_function,is_possible_rational,is_possible_irrational=args
                if not self._is_called and is_possible_rational and is_possible_irrational: warn_undecidable()
                self._is_possible_irrational=True
                self._is_possible_rational=is_possible_rational
                self._nearest_left=Rationalclass.minfty
                self._nearest_right=Rationalclass.infty
                self._left_answer=-1
                self._right_answer=1
                self._is_regular=False
                self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(sign_function)
                integer_bound=self._int_bound_for_init(left,right)
                if isinstance(integer_bound,Rationalclass):
                    left_integer,right_integer=integer_bound.int_bound()
                    self._floor=left_integer
                    self._ceil=right_integer
                else:
                    left_integer,right_integer=integer_bound
                    self._floor=left_integer
                    self._ceil=right_integer
                    self._left_rational=constructor(left_integer,1)
                    self._right_rational=constructor(right_integer,1)
                if self._is_possible_irrational and not is_possible_irrational:
                    self._regularize()
                    self._find_rational_for_regular()
            else: raise TypeError(f'Invalid number of arguments: {args_length}')
            del self._is_called
        def sign_func(self,*args)->CompareResult:
            analyzer=type(self)._Rational._analyze_input
            numerator,denominator,_=analyzer(*args)
            return self._sign_func(numerator,denominator)
        def current_bound(self,depend_on_structure:bool=False)->tuple[Q,Q]:
            if not depend_on_structure: return self._nearest_left,self._nearest_right
            else: return self._left_rational,self._right_rational
        def current_width(self,depend_on_structure:bool=False)->Q:
            if not depend_on_structure: return (self._nearest_right-self._nearest_left).intern()
            else:
                if not self._is_possible_irrational: return type(self)._Rational.ZERO
                else: return type(self)._Rational._new_for_simple(1,self._left_rational.denominator*self._right_rational.denominator)
        def refine_to_width(self,epsilon:RationalLike)->None:
            Rationalclass=type(self)._Rational
            constructor=Rationalclass._new_for_simple
            analyzer=Rationalclass._analyze_input_for_one_argument
            numerator_epsilon,denominator_epsilon,is_simple=analyzer(epsilon)
            if denominator_epsilon==0: raise ValueError('epsilon must be a finite rational number')
            if numerator_epsilon<=0: raise ValueError('epsilon must be positive')
            if not is_simple: numerator_epsilon,denominator_epsilon=Rationalclass._simplify(numerator_epsilon,denominator_epsilon)
            self._regularize()
            left_rational=self._left_rational
            right_rational=self._right_rational
            denominator_left,denominator_right=left_rational.denominator,right_rational.denominator
            if denominator_left*denominator_right*numerator_epsilon>=denominator_epsilon: return
            numerator_left,numerator_right=left_rational.numerator,right_rational.numerator
            while True:
                denominator_mid=denominator_left+denominator_right
                numerator_mid=numerator_left+numerator_right
                compare_result=self._init_sign_func(numerator_mid,denominator_mid)
                if compare_result==-1:
                    denominator_left=denominator_mid
                    numerator_left=numerator_mid
                elif compare_result==1:
                    denominator_right=denominator_mid
                    numerator_right=numerator_mid
                else: return
                if denominator_left*denominator_right*numerator_epsilon>=denominator_epsilon: break
            self._left_rational=constructor(numerator_left,denominator_left)
            self._right_rational=constructor(numerator_right,denominator_right)
        def __bool__(self):
            if self._is_possible_irrational: return True
            if self._exact_rational==type(self)._Rational.ZERO: return False
            return True
        def __str__(self):
            if self._is_possible_irrational: return f"A real number in the rational interval [{str(self._nearest_left)},{str(self._nearest_right)}]"
            return str(self._exact_rational)
        def as_integer_ratio(self,fallback_max_denominator:int=None)->IntegerRatio:
            if fallback_max_denominator is None:
                if not self._is_possible_rational: raise ValueError('This number is exactly irrational.')
                if self._is_possible_irrational: raise ValueError('This number has no rational representation yet.')
                return self._exact_rational.as_integer_ratio()
            if not isinstance(fallback_max_denominator,int): raise TypeError('fallback_max_denominator must be an integer')
            if fallback_max_denominator<1: raise ValueError('fallback_max_denominator must be positive')
            if not self._is_possible_irrational: return self._exact_rational.as_integer_ratio()
            left,right=self.rational_bound(fallback_max_denominator)
            numerator_left,denominator_left=left.numerator,left.denominator
            numerator_right,denominator_right=right.numerator,right.denominator
            numerator_mid=numerator_left*denominator_right+numerator_right*denominator_left
            denominator_mid=2*denominator_left*denominator_right
            compare_result=self._init_sign_func(numerator_mid,denominator_mid)
            if compare_result==-1: return numerator_right,denominator_right
            if compare_result==1: return numerator_left,denominator_left
            return type(self)._Rational._simplify(numerator_mid,denominator_mid)
        def to_scientific_notation(self,precision:int=17)->str:
            if not isinstance(precision,int): raise TypeError('precision must be an integer')
            if precision<0: raise ValueError('precision must be non-negative')
            if not self._is_possible_irrational:
                result=self._exact_rational.to_scientific_notation(precision)
                if self._exponent_10 is None: self._exponent_10=int(result.split('e')[1])
                return result
            left_integer=self._floor
            if left_integer<0:
                left_integer=-(left_integer+1)
                is_positive=False
                sign_str='-'
                abs_sign_func=lambda x,y:-(self._init_sign_func(-x,y))
            else:
                is_positive=True
                sign_str=''
                abs_sign_func=lambda x,y: self._init_sign_func(x,y)
            if self._exponent_10 is not None: exponent=self._exponent_10
            else:
                if left_integer>=1: exponent=len(str(left_integer))-1
                else:
                    if is_positive:
                        numerator_left,denominator_left=self._nearest_left.numerator,self._nearest_left.denominator
                        numerator_right,denominator_right=self._nearest_right.numerator,self._nearest_right.denominator
                    else:
                        numerator_left,denominator_left=-(self._nearest_right.numerator),self._nearest_right.denominator
                        numerator_right,denominator_right=-(self._nearest_left.numerator),self._nearest_left.denominator
                    exponent_right=1-len(str(numerator_right//denominator_right))
                    denominator_e_right=10**(-exponent_right)
                    if numerator_left==0:
                        exponent_left=exponent_right-1
                        denominator_e_left=denominator_e_right*10
                        compare_result=abs_sign_func(1,denominator_e_left)
                        step=1
                        while compare_result==1:
                            exponent_right=exponent_left
                            denominator_e_right=denominator_e_left
                            exponent_left-=step
                            denominator_e_left*=10**step
                            compare_result=abs_sign_func(1,denominator_e_left)
                            step<<=1
                    else:
                        left_invert_ceil=-(-denominator_left//numerator_left)
                        is_ten_power=True
                        exponent_left=0
                        quotient,remainder=divmod(left_invert_ceil,10)
                        while quotient!=0:
                            exponent_left-=1
                            if is_ten_power and remainder!=0: is_ten_power=False
                            quotient,remainder=divmod(quotient,10)
                        if is_ten_power and remainder!=1: is_ten_power=False
                        if not is_ten_power: exponent_left-=1
                    is_determined=False
                    while exponent_left+1!=exponent_right:
                        exponent_total=exponent_left+exponent_right
                        exponent_mid=exponent_total>>1
                        if exponent_mid<<1!=exponent_total and exponent_mid&1: exponent_mid+=1
                        denominator_e_mid=denominator_e_right*(10**(exponent_right-exponent_mid))
                        compare_result=abs_sign_func(1,denominator_e_mid)
                        if compare_result==1: exponent_right=exponent_mid; denominator_e_right=denominator_e_mid
                        elif compare_result==-1: exponent_left=exponent_mid; denominator_e_left=denominator_e_mid
                        else: exponent=exponent_mid; is_determined=True; break
                    if not is_determined: exponent=exponent_left
                self._exponent_10=exponent
            if exponent>=0: exponent_str='e+'+str(exponent)
            else: exponent_str='e'+str(exponent)
            if is_positive:
                numerator_left,denominator_left=self._nearest_left.numerator,self._nearest_left.denominator
                numerator_right,denominator_right=self._nearest_right.numerator,self._nearest_right.denominator
            else:
                numerator_left,denominator_left=-(self._nearest_right.numerator),self._nearest_right.denominator
                numerator_right,denominator_right=-(self._nearest_left.numerator),self._nearest_left.denominator
            exponent-=precision
            if exponent>=0:
                numerator_scalar=10**exponent
                search_left=numerator_left//(numerator_scalar*denominator_left)
                search_right=-(-numerator_right//(numerator_scalar*denominator_right))
                is_found=False
                while search_left+1!=search_right:
                    search_total=search_left+search_right
                    search_mid=search_total>>1
                    if search_mid<<1!=search_total and search_mid&1: search_mid+=1
                    test_numerator=search_mid*numerator_scalar
                    compare_result=abs_sign_func(test_numerator,1)
                    if compare_result==1: search_right=search_mid
                    elif compare_result==-1: search_left=search_mid
                    else: mantissa=search_mid; is_found=True; break
                if not is_found: mantissa=search_left
            else:
                denominator_scalar=10**(-exponent)
                search_left=(numerator_left*denominator_scalar)//denominator_left
                search_right=-(-(numerator_right*denominator_scalar)//denominator_right)
                is_found=False
                while search_left+1!=search_right:
                    search_total=search_left+search_right
                    search_mid=search_total>>1
                    if search_mid<<1!=search_total and search_mid&1: search_mid+=1
                    compare_result=abs_sign_func(search_mid,denominator_scalar)
                    if compare_result==1: search_right=search_mid
                    elif compare_result==-1: search_left=search_mid
                    else: mantissa=search_mid; is_found=True; break
                if not is_found: mantissa=search_left
            if is_found: mantissa_str=str(mantissa).rstrip('0')
            else: mantissa_str=str(mantissa)
            if len(mantissa_str)>1: mantissa_str=mantissa_str[0]+'.'+mantissa_str[1:]
            return sign_str+mantissa_str+exponent_str
        def float_bound(self)->tuple[float,float]:
            if self._float_bound is not None: return self._float_bound
            if not self._is_possible_irrational: self._float_bound=self._exact_rational.float_bound(); return self._float_bound
            left_integer=self._floor
            if left_integer>=0: abs_floor=left_integer; abs_sign_func=lambda x,y:self._init_sign_func(x,y); is_positive=True
            else: abs_floor=-(left_integer+1); abs_sign_func=lambda x,y:-(self._init_sign_func(-x,y)); is_positive=False
            if abs_floor>=1:
                max_int=((1<<53)-1)<<971
                if abs_floor>=max_int: abs_float_bound=(float(max_int),float('inf'))
                else:
                    exponent=abs_floor.bit_length()-53
                    if exponent>=0:
                        numerator_scalar=1<<exponent
                        mantissa=abs_floor//numerator_scalar
                        left_float=mantissa*numerator_scalar
                        right_float=left_float+numerator_scalar
                        abs_float_bound=(float(left_float),float(right_float))
                    else:
                        denominator_scalar=1<<(-exponent)
                        if is_positive:
                            numerator_left,denominator_left=self._nearest_left.numerator,self._nearest_left.denominator
                            numerator_right,denominator_right=self._nearest_right.numerator,self._nearest_right.denominator
                        else:
                            numerator_left,denominator_left=-(self._nearest_right.numerator),self._nearest_right.denominator
                            numerator_right,denominator_right=-(self._nearest_left.numerator),self._nearest_left.denominator
                        search_left=(numerator_left*denominator_scalar)//denominator_left
                        search_right=-(-(numerator_right*denominator_scalar)//denominator_right)
                        is_found=False
                        while search_left+1!=search_right:
                            search_total=search_left+search_right
                            search_mid=search_total>>1
                            if search_mid<<1!=search_total and search_mid&1: search_mid+=1
                            compare_result=abs_sign_func(search_mid,denominator_scalar)
                            if compare_result==1: search_right=search_mid
                            elif compare_result==-1: search_left=search_mid
                            else: result=search_mid/denominator_scalar; abs_float_bound=(result,result); is_found=True; break
                        if not is_found: abs_float_bound=(search_left/denominator_scalar,search_right/denominator_scalar)
            else:
                test_min_denominator=1<<1074
                compare_result=abs_sign_func(1,test_min_denominator)
                if compare_result==1: abs_float_bound=(float(0),1/test_min_denominator)
                elif compare_result==-1:
                    if is_positive:
                        numerator_left,denominator_left=self._nearest_left.numerator,self._nearest_left.denominator
                        numerator_right,denominator_right=self._nearest_right.numerator,self._nearest_right.denominator
                    else:
                        numerator_left,denominator_left=-(self._nearest_right.numerator),self._nearest_right.denominator
                        numerator_right,denominator_right=-(self._nearest_left.numerator),self._nearest_left.denominator
                    left_invert_ceil=-(-denominator_left//numerator_left)
                    if left_invert_ceil&(left_invert_ceil-1)==0: exponent_left=left_invert_ceil.bit_length()-1
                    else: exponent_left=left_invert_ceil.bit_length()
                    exponent_right=(denominator_right//numerator_right).bit_length()-1
                    left_denominator=1<<exponent_left
                    right_denominator=1<<exponent_right
                    is_found=False
                    while exponent_left-1!=exponent_right:
                        exponent_total=exponent_left+exponent_right
                        exponent_mid=exponent_total>>1
                        if exponent_mid<<1!=exponent_total and exponent_mid&1: exponent_mid+=1
                        test_denominator=right_denominator<<(exponent_mid-exponent_right)
                        compare_result=abs_sign_func(1,test_denominator)
                        if compare_result==1: exponent_right=exponent_mid; right_denominator=test_denominator
                        elif compare_result==-1: exponent_left=exponent_mid; left_denominator=test_denominator
                        else: result=1/test_denominator; abs_float_bound=(result,result); is_found=True; break
                    if not is_found:
                        denominator_scalar=(left_denominator<<52 if exponent_left<=1022 else 1<<1074)
                        if is_positive:
                            numerator_left,denominator_left=self._nearest_left.numerator,self._nearest_left.denominator
                            numerator_right,denominator_right=self._nearest_right.numerator,self._nearest_right.denominator
                        else:
                            numerator_left,denominator_left=-(self._nearest_right.numerator),self._nearest_right.denominator
                            numerator_right,denominator_right=-(self._nearest_left.numerator),self._nearest_left.denominator
                        search_left=(numerator_left*denominator_scalar)//denominator_left
                        search_right=-(-(numerator_right*denominator_scalar)//denominator_right)
                        while search_left+1!=search_right:
                            search_total=search_left+search_right
                            search_mid=search_total>>1
                            if search_mid<<1!=search_total and search_mid&1: search_mid+=1
                            compare_result=abs_sign_func(search_mid,denominator_scalar)
                            if compare_result==1: search_right=search_mid
                            elif compare_result==-1: search_left=search_mid
                            else: result=search_mid/denominator_scalar; abs_float_bound=(result,result); is_found=True; break
                        if not is_found: abs_float_bound=(search_left/denominator_scalar,search_right/denominator_scalar)
                else: result=1/test_min_denominator; abs_float_bound=(result,result)
            if is_positive: self._float_bound=abs_float_bound
            else: abs_left,abs_right=abs_float_bound; self._float_bound=(-abs_right,-abs_left)
            return self._float_bound
        def __float__(self):
            if not self._is_possible_irrational: return float(self._exact_rational)
            left_float,right_float=self.float_bound()
            if left_float==right_float: return left_float
            infty=float('inf')
            if right_float==infty: infty_test=((1<<54)-1)<<970; return (infty if self._floor>=infty_test else left_float)
            minfty=-infty
            if left_float==minfty: minfty_test=-(((1<<54)-1)<<970); return (minfty if self._ceil<=minfty_test else right_float)
            numerator_left,denominator_left=left_float.as_integer_ratio()
            numerator_right,denominator_right=right_float.as_integer_ratio()
            numerator_mid=numerator_left*denominator_right+numerator_right*denominator_left
            denominator_mid=2*denominator_left*denominator_right
            compare_result=self._init_sign_func(numerator_mid,denominator_mid)
            if compare_result==1: return left_float
            if compare_result==-1: return right_float
            return numerator_mid/denominator_mid
        def __complex__(self): return complex(float(self),0)
        def __repr__(self):
            cls=type(self)
            cls_name=cls.__name__
            container_class=cls._container_class
            container_class_name=container_class.__name__
            head_str=f'{container_class_name}.{cls_name}'
            return f"{head_str}({self._sign_func},{self._is_possible_rational},{self._is_possible_irrational})"
        def __int__(self): left_int=self._floor; return (self._ceil if left_int<0 else left_int)
        def __floor__(self): return self._floor
        def __ceil__(self): return self._ceil
        def __trunc__(self): return self.__int__()
        set_max_denominator_for_hash=None
        '''
        The class attribute set_max_denominator_for_hash controls the hash precision. This class's hash function ensures that a RealNumber object with a small
        denominator will hash to the same value as the corresponding RationalNumber object. Note that this class attribute can only be set once to ensure hash
        consistency.
        '''
        def __hash__(self):
            if self._hash is not None: return self._hash
            cls=type(self)
            max_denominator=cls.set_max_denominator_for_hash
            if max_denominator is None: raise NotImplementedError('set_max_denominator_for_hash must be set before __hash__ is called for the first time.')
            left,right=self.rational_bound(max_denominator)
            if left==right: self._hash=hash(left); return self._hash
            denominator_left,denominator_right=left.denominator,right.denominator
            numerator_mid=left.numerator*denominator_right+right.numerator*denominator_left
            denominator_mid=2*denominator_left*denominator_right
            compare_result=self._init_sign_func(numerator_mid,denominator_mid)
            if compare_result==1: self._hash=hash(left); return self._hash
            if compare_result==-1: self._hash=hash(right); return self._hash
            if denominator_left<denominator_right: self._hash=hash(left); return self._hash
            if denominator_left>denominator_right: self._hash=hash(right); return self._hash
            self._hash=(hash(right) if left.numerator&1 else hash(left))
            return self._hash
        def __neg__(self):
            cls=type(self)
            if not self._is_possible_irrational: result=self._exact_rational.__neg__(); return cls(result,True,False)
            def new_sign_func(numerator,denominator): return -(self._init_sign_func(-numerator,denominator))
            if not self._is_possible_rational: return cls(new_sign_func,False,True,-(self._nearest_right),-(self._nearest_left))
            result=cls.__new__(cls)
            def result_sign_func(numerator,denominator):
                if not self._is_possible_irrational:
                    result_rational=-(self._exact_rational)
                    result._rationalized(result_rational)
                    return result._init_sign_func(numerator,denominator)
                if not self._is_possible_rational:
                    result._init_sign_func,result._sign_func=result._wrapper_for_sign_function(new_sign_func)
                    result._is_possible_rational=False
                return new_sign_func(numerator,denominator)
            result._is_called=True
            result.__init__(-(self._nearest_right),-(self._nearest_left),result_sign_func,True,True)
            return result
        def __pos__(self): return self
        def __abs__(self):
            cls=type(self)
            if not self._is_possible_irrational:
                result=self._exact_rational.__abs__()
                return cls(result,True,False)
            floor=self._floor
            if floor<0: return self.__neg__()
            return self
        
        #region: Binary operators
        #region: Factories of binary operators
        @classmethod
        def _analyze_input_for_operator(cls,other:RealLike)->tuple[IntegerRatio|Self,bool,bool]:
            if isinstance(other,cls._family_root):
                possible_rational=other._is_possible_rational
                possible_irrational=other._is_possible_irrational
                if not possible_irrational: return other._exact_rational.as_integer_ratio(),possible_rational,possible_irrational
                else: return other,possible_rational,possible_irrational
            sign_function,is_exactly_rational=cls._analyze_input_for_sign_function(other)
            if is_exactly_rational:
                numerator,denominator=sign_function
                rational=cls._Rational._simplify(numerator,denominator)
                return rational,True,False
            else:
                instance=cls.__new__(cls)
                instance._is_called=False
                instance.__init__(None,None,sign_function,True,True)
                return cls._analyze_input_for_operator(instance)
        @classmethod
        def _new_for_operator_ratio(cls,algorithm:UopR[Self],self:Self,other:IntegerRatio,left_init:Q,right_init:Q)->Self:
            result=cls.__new__(cls)
            numerator_other,denominator_other=other
            new_sign_func=algorithm(result,self,numerator_other,denominator_other)
            result._is_called=True
            result.__init__(left_init,right_init,new_sign_func,True,True)
            return result
        @classmethod
        def _new_for_operator_obj(cls,algorithm:OpWithU[Self],self:Self,other:Self,left_init:Q,right_init:Q)->Self:
            result=cls.__new__(cls)
            new_sign_func=algorithm(result,self,other)
            result._is_called=True
            result.__init__(left_init,right_init,new_sign_func,True,True)
            return result
        @classmethod
        def _factory_for_operator(cls,rational_op_rational:RopR[Q],irrational_op_rational:IopR[Self],irrational_rop_rational:IopR[Self],
                                  refine_generator:RefineGenerator[Self])->Factories[Self]:
            factories=[irrational_op_rational,irrational_rop_rational]
            def unknown_op_rational(self:Self,op1:Self,numerator_input:int,denominator_input:int)->SignFunction:
                op_sign_func=irrational_op_rational(op1,numerator_input,denominator_input)
                def new_sign_func(numerator:int,denominator:int)->CompareResult:
                    if not op1._is_possible_irrational:
                        op1_numerator,op1_denominator=op1._exact_rational.as_integer_ratio()
                        op_result=rational_op_rational(op1_numerator,op1_denominator,numerator_input,denominator_input)
                        self._rationalized(op_result)
                        return self._init_sign_func(numerator,denominator)
                    if not op1._is_possible_rational:
                        self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                        self._is_possible_rational=False
                    return op_sign_func(numerator,denominator)
                return new_sign_func
            factories.append(unknown_op_rational)
            def unknown_rop_rational(self:Self,op2:Self,numerator_input:int,denominator_input:int)->SignFunction:
                op_sign_func=irrational_rop_rational(op2,numerator_input,denominator_input)
                def new_sign_func(numerator:int,denominator:int)->CompareResult:
                    if not op2._is_possible_irrational:
                        op2_numerator,op2_denominator=op2._exact_rational.as_integer_ratio()
                        op_result=rational_op_rational(numerator_input,denominator_input,op2_numerator,op2_denominator)
                        self._rationalized(op_result)
                        return self._init_sign_func(numerator,denominator)
                    if not op2._is_possible_rational:
                        self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                        self._is_possible_rational=False
                    return op_sign_func(numerator,denominator)
                return new_sign_func
            factories.append(unknown_rop_rational)
            def next_test_point(instance:Self)->tuple[int,int]:
                instance._regularize()
                left_rational,right_rational=instance._left_rational,instance._right_rational
                numerator,denominator=left_rational.numerator+right_rational.numerator,left_rational.denominator+right_rational.denominator
                return numerator,denominator
            def update(instance:Self)->None:
                numerator,denominator=next_test_point(instance)
                instance._init_sign_func(numerator,denominator,input_is_regular=True)
            def irrational_op_irrational(self:Self,other:Self)->SignFunction:
                def new_sign_func(numerator:int,denominator:int)->CompareResult:
                    op_iterator=refine_generator(self,other)
                    numerator_left,denominator_left=next(op_iterator)
                    if numerator*denominator_left<=denominator*numerator_left: return -1
                    numerator_right,denominator_right=next(op_iterator)
                    if numerator*denominator_right>=denominator*numerator_right: return 1
                    while True:
                        result,result_type=next(op_iterator)
                        if result_type==-1:
                            numerator_left,denominator_left=result
                            if numerator*denominator_left<=denominator*numerator_left: return -1
                        elif result_type==1:
                            numerator_right,denominator_right=result
                            if numerator*denominator_right>=denominator*numerator_right: return 1
                        else:
                            compare_left,compare_right=result
                            if compare_left<compare_right: update(self)
                            elif compare_right<compare_left: update(other)
                            else: update(self); update(other)
                return new_sign_func
            factories.append(irrational_op_irrational)
            def unknown_op_irrational(self:Self,op1:Self,op2:Self)->SignFunction:
                def op1_convert_to_rational(numerator_op1,denominator_op1):
                    op_sign_func=irrational_rop_rational(op2,numerator_op1,denominator_op1)
                    self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                    self._is_possible_rational=False
                def op1_convert_to_irrational():
                    op_sign_func=irrational_op_irrational(op1,op2)
                    self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                def new_sign_func(numerator,denominator):
                    if not op1._is_possible_irrational:
                        numerator_op1,denominator_op1=op1._exact_rational.as_integer_ratio()
                        op1_convert_to_rational(numerator_op1,denominator_op1)
                        return self._init_sign_func(numerator,denominator)
                    if not op1._is_possible_rational:
                        op1_convert_to_irrational()
                        return self._init_sign_func(numerator,denominator)
                    op_iterator=refine_generator(op1,op2)
                    numerator_left,denominator_left=next(op_iterator)
                    if numerator*denominator_left<=denominator*numerator_left: return -1
                    numerator_right,denominator_right=next(op_iterator)
                    if numerator*denominator_right>=denominator*numerator_right: return 1
                    while True:
                        result,result_type=next(op_iterator)
                        if result_type==-1:
                            numerator_left,denominator_left=result
                            if numerator*denominator_left<=denominator*numerator_left: return -1
                        elif result_type==1:
                            numerator_right,denominator_right=result
                            if numerator*denominator_right>=denominator*numerator_right: return 1
                        else:
                            compare_left,compare_right=result
                            if compare_left<compare_right:
                                op1_numerator,op1_denominator=next_test_point(op1)
                                compare_result=op1._init_sign_func(op1_numerator,op1_denominator,input_is_regular=True)
                                if compare_result==0: op1_convert_to_rational(op1_numerator,op1_denominator); return self._init_sign_func(numerator,denominator)
                                if not op1._is_possible_rational: op1_convert_to_irrational(); return self._init_sign_func(numerator,denominator)
                            elif compare_right<compare_left: update(op2)
                            else:
                                op1_numerator,op1_denominator=next_test_point(op1)
                                compare_result=op1._init_sign_func(op1_numerator,op1_denominator,input_is_regular=True)
                                if compare_result==0: op1_convert_to_rational(op1_numerator,op1_denominator); return self._init_sign_func(numerator,denominator)
                                if not op1._is_possible_rational: op1_convert_to_irrational(); return self._init_sign_func(numerator,denominator)
                                update(op2)
                return new_sign_func
            factories.append(unknown_op_irrational)
            def irrational_op_unknown(self:Self,op1:Self,op2:Self)->SignFunction:
                def op2_convert_to_rational(numerator_op2:int,denominator_op2:int)->None:
                    op_sign_func=irrational_op_rational(op1,numerator_op2,denominator_op2)
                    self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                    self._is_possible_rational=False
                def op2_convert_to_irrational()->None:
                    op_sign_func=irrational_op_irrational(op1,op2)
                    self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                def new_sign_func(numerator:int,denominator:int)->CompareResult:
                    if not op2._is_possible_irrational:
                        numerator_op2,denominator_op2=op2._exact_rational.as_integer_ratio()
                        op2_convert_to_rational(numerator_op2,denominator_op2)
                        return self._init_sign_func(numerator,denominator)
                    if not op2._is_possible_rational:
                        op2_convert_to_irrational()
                        return self._init_sign_func(numerator,denominator)
                    op_iterator=refine_generator(op1,op2)
                    numerator_left,denominator_left=next(op_iterator)
                    if numerator*denominator_left<=denominator*numerator_left: return -1
                    numerator_right,denominator_right=next(op_iterator)
                    if numerator*denominator_right>=denominator*numerator_right: return 1
                    while True:
                        result,result_type=next(op_iterator)
                        if result_type==-1:
                            numerator_left,denominator_left=result
                            if numerator*denominator_left<=denominator*numerator_left: return -1
                        elif result_type==1:
                            numerator_right,denominator_right=result
                            if numerator*denominator_right>=denominator*numerator_right: return 1
                        else:
                            compare_left,compare_right=result
                            if compare_left<compare_right: update(op1)
                            elif compare_right<compare_left:
                                op2_numerator,op2_denominator=next_test_point(op2)
                                compare_result=op2._init_sign_func(op2_numerator,op2_denominator,input_is_regular=True)
                                if compare_result==0: op2_convert_to_rational(op2_numerator,op2_denominator); return self._init_sign_func(numerator,denominator)
                                if not op2._is_possible_rational: op2_convert_to_irrational(); return self._init_sign_func(numerator,denominator)
                            else:
                                op2_numerator,op2_denominator=next_test_point(op2)
                                compare_result=op2._init_sign_func(op2_numerator,op2_denominator,input_is_regular=True)
                                if compare_result==0: op2_convert_to_rational(op2_numerator,op2_denominator); return self._init_sign_func(numerator,denominator)
                                if not op2._is_possible_rational: op2_convert_to_irrational(); return self._init_sign_func(numerator,denominator)
                                update(op1)
                return new_sign_func
            factories.append(irrational_op_unknown)
            def unknown_op_unknown(self:Self,op1:Self,op2:Self)->SignFunction:
                def op1_convert_to_rational(numerator_op1:int,denominator_op1:int)->None:
                    op_sign_func=unknown_rop_rational(self,op2,numerator_op1,denominator_op1)
                    self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                def op1_convert_to_irrational()->None:
                    op_sign_func=irrational_op_unknown(self,op1,op2)
                    self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                def op2_convert_to_rational(numerator_op2:int,denominator_op2:int)->None:
                    op_sign_func=unknown_op_rational(self,op1,numerator_op2,denominator_op2)
                    self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                def op2_convert_to_irrational()->None:
                    op_sign_func=unknown_op_irrational(self,op1,op2)
                    self._init_sign_func,self._sign_func=self._wrapper_for_sign_function(op_sign_func)
                def new_sign_func(numerator:int,denominator:int)->CompareResult:
                    if not op1._is_possible_irrational:
                        numerator_op1,denominator_op1=op1._exact_rational.as_integer_ratio()
                        op1_convert_to_rational(numerator_op1,denominator_op1)
                        return self._init_sign_func(numerator,denominator)
                    if not op1._is_possible_rational:
                        op1_convert_to_irrational()
                        return self._init_sign_func(numerator,denominator)
                    if not op2._is_possible_irrational:
                        numerator_op2,denominator_op2=op2._exact_rational.as_integer_ratio()
                        op2_convert_to_rational(numerator_op2,denominator_op2)
                        return self._init_sign_func(numerator,denominator)
                    if not op2._is_possible_rational:
                        op2_convert_to_irrational()
                        return self._init_sign_func(numerator,denominator)
                    op_iterator=refine_generator(op1,op2)
                    numerator_left,denominator_left=next(op_iterator)
                    if numerator*denominator_left<=denominator*numerator_left: return -1
                    numerator_right,denominator_right=next(op_iterator)
                    if numerator*denominator_right>=denominator*numerator_right: return 1
                    while True:
                        result,result_type=next(op_iterator)
                        if result_type==-1:
                            numerator_left,denominator_left=result
                            if numerator*denominator_left<=denominator*numerator_left: return -1
                        elif result_type==1:
                            numerator_right,denominator_right=result
                            if numerator*denominator_right>=denominator*numerator_right: return 1
                        else:
                            compare_left,compare_right=result
                            if compare_left<compare_right:
                                op1_numerator,op1_denominator=next_test_point(op1)
                                compare_result=op1._init_sign_func(op1_numerator,op1_denominator,input_is_regular=True)
                                if compare_result==0:
                                    op1_convert_to_rational(op1_numerator,op1_denominator)
                                    return self._init_sign_func(numerator,denominator)
                                if not op1._is_possible_rational:
                                    op1_convert_to_irrational()
                                    return self._init_sign_func(numerator,denominator)
                            elif compare_right<compare_left:
                                op2_numerator,op2_denominator=next_test_point(op2)
                                compare_result=op2._init_sign_func(op2_numerator,op2_denominator,input_is_regular=True)
                                if compare_result==0:
                                    op2_convert_to_rational(op2_numerator,op2_denominator)
                                    return self._init_sign_func(numerator,denominator)
                                if not op2._is_possible_rational:
                                    op2_convert_to_irrational()
                                    return self._init_sign_func(numerator,denominator)
                            else:
                                op1_numerator,op1_denominator=next_test_point(op1)
                                compare_result=op1._init_sign_func(op1_numerator,op1_denominator,input_is_regular=True)
                                if compare_result==0:
                                    op1_convert_to_rational(op1_numerator,op1_denominator)
                                    return self._init_sign_func(numerator,denominator)
                                if not op1._is_possible_rational:
                                    op1_convert_to_irrational()
                                    return self._init_sign_func(numerator,denominator)
                                op2_numerator,op2_denominator=next_test_point(op2)
                                compare_result=op2._init_sign_func(op2_numerator,op2_denominator,input_is_regular=True)
                                if compare_result==0:
                                    op2_convert_to_rational(op2_numerator,op2_denominator)
                                    return self._init_sign_func(numerator,denominator)
                                if not op2._is_possible_rational:
                                    op2_convert_to_irrational()
                                    return self._init_sign_func(numerator,denominator)
                return new_sign_func
            factories.append(unknown_op_unknown)
            result=tuple(factories)
            return result
        @classmethod
        def _products_for_operator(cls,factories:Factories[Self],interval_op:Interval_op[Q])->Products[Self]:
            unknown_op_rational_method=factories[2]
            unknown_rop_rational_method=factories[3]
            unknown_op_irrational_method=factories[5]
            irrational_op_unknown_method=factories[6]
            unknown_op_unknown_method=factories[7]
            products=[]
            def unknown_op_rational(self:Self,other_obj:IntegerRatio)->Self:
                local_cls=type(self)
                init_left,init_right=interval_op(self._nearest_left,self._nearest_right,other_obj,other_obj)
                return local_cls._new_for_operator_ratio(unknown_op_rational_method,self,other_obj,init_left,init_right)
            products.append(unknown_op_rational)
            def unknown_rop_rational(self:Self,other_obj:IntegerRatio)->Self:
                local_cls=type(self)
                init_left,init_right=interval_op(other_obj,other_obj,self._nearest_left,self._nearest_right)
                return local_cls._new_for_operator_ratio(unknown_rop_rational_method,self,other_obj,init_left,init_right)
            products.append(unknown_rop_rational)
            def core_product(method:OpWithU[Self])->StrictOperation[Self]:
                def new_object(self:Self,other:Self)->Self:
                    local_cls=type(self)
                    self_left=self._nearest_left
                    self_right=self._nearest_right
                    other_left=other._nearest_left
                    other_right=other._nearest_right
                    init_left,init_right=interval_op(self_left,self_right,other_left,other_right)
                    return local_cls._new_for_operator_obj(method,self,other,init_left,init_right)
                return new_object
            products.append(core_product(unknown_op_irrational_method))
            products.append(core_product(irrational_op_unknown_method))
            products.append(core_product(unknown_op_unknown_method))
            result=tuple(products)
            return result
        #endregion

        #region: Addition operation
        @classmethod
        def _rational_add_rational(cls,op1_numerator:int,op1_denominator:int,op2_numerator:int,op2_denominator:int)->Q:
            RaN=cls._Rational
            result=RaN(op1_numerator*op2_denominator+op1_denominator*op2_numerator,op1_denominator*op2_denominator)
            return result
        def _irrational_add_rational(self,numerator_input:int,denominator_input:int)->SignFunction:
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                numerator_sub=numerator*denominator_input-denominator*numerator_input
                denominator_sub=denominator*denominator_input
                return self._init_sign_func(numerator_sub,denominator_sub)
            return new_sign_func
        def _refine_generator_for_add(self,other:Self)->RefineOutput:
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_left=self_L_numerator*other_L_denominator+self_L_denominator*other_L_numerator
            denominator_left=self_L_denominator*other_L_denominator
            yield numerator_left,denominator_left
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_right=self_R_numerator*other_R_denominator+self_R_denominator*other_R_numerator
            denominator_right=self_R_denominator*other_R_denominator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            self_diff_numerator=self_cross_R-self_cross_L
            self_diff_denominator=self_L_denominator*self_R_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            other_diff_numerator=other_cross_R-other_cross_L
            other_diff_denominator=other_L_denominator*other_R_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (other_diff_numerator*self_diff_denominator,self_diff_numerator*other_diff_denominator),0
                new_self_L=self._nearest_left
                new_other_L=other._nearest_left
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_L_is_updated or other_L_is_updated:
                    numerator_left=self_L_numerator*other_L_denominator+self_L_denominator*other_L_numerator
                    denominator_left=self_L_denominator*other_L_denominator
                    yield (numerator_left,denominator_left),-1
                new_self_R=self._nearest_right
                new_other_R=other._nearest_right
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_R_is_updated or other_R_is_updated:
                    numerator_right=self_R_numerator*other_R_denominator+self_R_denominator*other_R_numerator
                    denominator_right=self_R_denominator*other_R_denominator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                    self_diff_numerator=self_cross_R-self_cross_L
                    self_diff_denominator=self_L_denominator*self_R_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                    other_diff_numerator=other_cross_R-other_cross_L
                    other_diff_denominator=other_L_denominator*other_R_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        @staticmethod
        def _interval_add(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_left+op2_left
            init_right=op1_right+op2_right
            return init_left,init_right
        @classmethod
        def _generated_operator_add(cls,RR:RopR[Q],FIR:IopR[Self],G:RefineGenerator[Self],I:Interval_op[Q])->tuple[Operation[Self],Operation[Self]]:
            FRI=FIR
            factories=cls._factory_for_operator(RR,FIR,FRI,G)
            FII=factories[4]
            products=cls._products_for_operator(factories,I)
            UR,RU,UI,IU,UU=products
            def left_operator(self:Self,other:RealLike)->Self:
                if other is self: return self*2
                local_cls=type(self)
                try: other_obj,other_is_possible_rational,other_is_possible_irrational=local_cls._analyze_input_for_operator(other)
                except TypeError: return NotImplemented
                if not other_is_possible_irrational:
                    numerator_other,denominator_other=other_obj
                    if numerator_other==0: return self
                    if not self._is_possible_irrational:
                        numerator_self,denominator_self=self._exact_rational.as_integer_ratio()
                        if numerator_self==0: return local_cls(other_obj,True,False)
                        result=RR(numerator_self,denominator_self,numerator_other,denominator_other)
                        return local_cls(result,True,False)
                    elif not self._is_possible_rational:
                        new_sign_func=FIR(self,numerator_other,denominator_other)
                        left,right=I(self._nearest_left,self._nearest_right,other_obj,other_obj)
                        return local_cls(new_sign_func,False,True,left,right)
                    else: return UR(self,other_obj)
                elif not other_is_possible_rational:
                    if not self._is_possible_irrational:
                        rational_self=self._exact_rational
                        numerator_self,denominator_self=rational_self.as_integer_ratio()
                        if numerator_self==0: return other_obj
                        new_sign_func=FRI(other_obj,numerator_self,denominator_self)
                        left,right=I(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                        return local_cls(new_sign_func,False,True,left,right)
                    elif not self._is_possible_rational:
                        new_sign_func=FII(self,other_obj)
                        left,right=I(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                        return local_cls(new_sign_func,True,True,left,right)
                    else: return UI(self,other_obj)
                else:
                    if not self._is_possible_irrational:
                        self_rational=self._exact_rational.as_integer_ratio()
                        if self_rational[0]==0: return local_cls(other_obj,True,True)
                        return RU(other_obj,self_rational)
                    elif not self._is_possible_rational: return IU(self,other_obj)
                    else: return UU(self,other_obj)
            def right_operator(self:Self,other:RealLike)->Self:
                local_cls=type(self)
                try: init_other_obj,is_exactly_rational=local_cls._analyze_input_for_sign_function(other)
                except TypeError: return NotImplemented
                if is_exactly_rational:
                    numerator_other,denominator_other=init_other_obj
                    if numerator_other==0: return self
                    if not self._is_possible_irrational:
                        numerator_self,denominator_self=self._exact_rational.as_integer_ratio()
                        if numerator_self==0: return local_cls(init_other_obj,True,False)
                        result=RR(numerator_other,denominator_other,numerator_self,denominator_self)
                        return local_cls(result,True,False)
                    elif not self._is_possible_rational:
                        new_sign_func=FRI(self,numerator_other,denominator_other)
                        left,right=I(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                        return local_cls(new_sign_func,False,True,left,right)
                    else: return RU(self,init_other_obj)
                else:
                    other_obj=local_cls.__new__(local_cls)
                    other_obj._is_called=False
                    other_obj.__init__(None,None,init_other_obj,True,True)
                    return left_operator(other_obj,self)
            return left_operator,right_operator
        #endregion

        #region: Subtraction operation
        @classmethod
        def _rational_sub_rational(cls,op1_numerator:int,op1_denominator:int,op2_numerator:int,op2_denominator:int)->Q:
            RaN=cls._Rational
            result=RaN(op1_numerator*op2_denominator-op1_denominator*op2_numerator,op1_denominator*op2_denominator)
            return result
        def _irrational_sub_rational(self,numerator_input:int,denominator_input:int)->SignFunction:
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                numerator_add=numerator*denominator_input+denominator*numerator_input
                denominator_add=denominator*denominator_input
                return self._init_sign_func(numerator_add,denominator_add)
            return new_sign_func
        def _irrational_rsub_rational(self,numerator_input:int,denominator_input:int)->SignFunction:
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                numerator_sub=numerator_input*denominator-denominator_input*numerator
                denominator_sub=denominator*denominator_input
                return -(self._init_sign_func(numerator_sub,denominator_sub))
            return new_sign_func
        def _refine_generator_for_sub(self,other:Self)->RefineOutput:
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_left=self_L_numerator*other_R_denominator-self_L_denominator*other_R_numerator
            denominator_left=self_L_denominator*other_R_denominator
            yield numerator_left,denominator_left
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_right=self_R_numerator*other_L_denominator-self_R_denominator*other_L_numerator
            denominator_right=self_R_denominator*other_L_denominator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            self_diff_numerator=self_cross_R-self_cross_L
            self_diff_denominator=self_L_denominator*self_R_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            other_diff_numerator=other_cross_R-other_cross_L
            other_diff_denominator=other_L_denominator*other_R_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (other_diff_numerator*self_diff_denominator,self_diff_numerator*other_diff_denominator),0
                new_self_L=self._nearest_left
                new_other_R=other._nearest_right
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_L_is_updated or other_R_is_updated:
                    numerator_left=self_L_numerator*other_R_denominator-self_L_denominator*other_R_numerator
                    denominator_left=self_L_denominator*other_R_denominator
                    yield (numerator_left,denominator_left),-1
                new_self_R=self._nearest_right
                new_other_L=other._nearest_left
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_R_is_updated or other_L_is_updated:
                    numerator_right=self_R_numerator*other_L_denominator-self_R_denominator*other_L_numerator
                    denominator_right=self_R_denominator*other_L_denominator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                    self_diff_numerator=self_cross_R-self_cross_L
                    self_diff_denominator=self_L_denominator*self_R_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                    other_diff_numerator=other_cross_R-other_cross_L
                    other_diff_denominator=other_L_denominator*other_R_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        @staticmethod
        def _interval_sub(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_left-op2_right
            init_right=op1_right-op2_left
            return init_left,init_right
        @classmethod
        def _generated_operator_sub(cls,
                                    RR:RopR[Q],FIR:IopR[Self],FRI:IopR[Self],G:RefineGenerator[Self],I:Interval_op[Q])->tuple[Operation[Self],Operation[Self]]:
            factories=cls._factory_for_operator(RR,FIR,FRI,G)
            FII=factories[4]
            products=cls._products_for_operator(factories,I)
            UR,RU,UI,IU,UU=products
            def left_operator(self:Self,other:RealLike)->Self:
                local_cls=type(self)
                if other is self: return local_cls(0)
                try: other_obj,other_is_possible_rational,other_is_possible_irrational=local_cls._analyze_input_for_operator(other)
                except TypeError: return NotImplemented
                if not other_is_possible_irrational:
                    numerator_other,denominator_other=other_obj
                    if numerator_other==0: return self
                    if not self._is_possible_irrational:
                        numerator_self,denominator_self=self._exact_rational.as_integer_ratio()
                        if numerator_self==0: return local_cls((-numerator_other,denominator_other),True,False)
                        result=RR(numerator_self,denominator_self,numerator_other,denominator_other)
                        return local_cls(result,True,False)
                    elif not self._is_possible_rational:
                        new_sign_func=FIR(self,numerator_other,denominator_other)
                        left,right=I(self._nearest_left,self._nearest_right,other_obj,other_obj)
                        return local_cls(new_sign_func,False,True,left,right)
                    else: return UR(self,other_obj)
                elif not other_is_possible_rational:
                    if not self._is_possible_irrational:
                        rational_self=self._exact_rational
                        numerator_self,denominator_self=rational_self.as_integer_ratio()
                        if numerator_self==0: return other_obj.__neg__()
                        new_sign_func=FRI(other_obj,numerator_self,denominator_self)
                        left,right=I(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                        return local_cls(new_sign_func,False,True,left,right)
                    elif not self._is_possible_rational:
                        new_sign_func=FII(self,other_obj)
                        left,right=I(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                        return local_cls(new_sign_func,True,True,left,right)
                    else: return UI(self,other_obj)
                else:
                    if not self._is_possible_irrational:
                        self_rational=self._exact_rational.as_integer_ratio()
                        return RU(other_obj,self_rational)
                    elif not self._is_possible_rational: return IU(self,other_obj)
                    else: return UU(self,other_obj)
            def right_operator(self:Self,other:RealLike)->Self:
                local_cls=type(self)
                if other is self: return local_cls(0)
                try: init_other_obj,is_exactly_rational=local_cls._analyze_input_for_sign_function(other)
                except TypeError: return NotImplemented
                if is_exactly_rational:
                    numerator_other,denominator_other=init_other_obj
                    if numerator_other==0: return self.__neg__()
                    if not self._is_possible_irrational:
                        numerator_self,denominator_self=self._exact_rational.as_integer_ratio()
                        result=RR(numerator_other,denominator_other,numerator_self,denominator_self)
                        return local_cls(result,True,False)
                    elif not self._is_possible_rational:
                        new_sign_func=FRI(self,numerator_other,denominator_other)
                        left,right=I(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                        return local_cls(new_sign_func,False,True,left,right)
                    else: return RU(self,init_other_obj)
                else:
                    other_obj=local_cls.__new__(local_cls)
                    other_obj._is_called=False
                    other_obj.__init__(None,None,init_other_obj,True,True)
                    return left_operator(other_obj,self)
            return left_operator,right_operator
        #endregion
        
        #region: Multiplication operation
        @classmethod
        def _rational_mul_rational(cls,op1_numerator:int,op1_denominator:int,op2_numerator:int,op2_denominator:int)->Q:
            RaN=cls._Rational
            result=RaN(op1_numerator*op2_numerator,op1_denominator*op2_denominator)
            return result
        def _irrational_mul_pos_rational(self,numerator_input:int,denominator_input:int)->SignFunction:
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                numerator_div=numerator*denominator_input
                denominator_div=denominator*numerator_input
                return self._init_sign_func(numerator_div,denominator_div)
            return new_sign_func
        def _irrational_mul_neg_rational(self,numerator_input:int,denominator_input:int)->SignFunction:
            numerator_input=-numerator_input
            denominator_input=-denominator_input
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                numerator_div=numerator*denominator_input
                denominator_div=denominator*numerator_input
                return -(self._init_sign_func(numerator_div,denominator_div))
            return new_sign_func
        def _refine_generator_for_pos_mul_pos(self,other:Self)->RefineOutput:
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_left=self_L_numerator*other_L_numerator
            denominator_left=self_L_denominator*other_L_denominator
            yield numerator_left,denominator_left
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_right=self_R_numerator*other_R_numerator
            denominator_right=self_R_denominator*other_R_denominator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (self_cross_L*other_cross_R,self_cross_R*other_cross_L),0
                new_self_L=self._nearest_left
                new_other_L=other._nearest_left
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_L_is_updated or other_L_is_updated:
                    numerator_left=self_L_numerator*other_L_numerator
                    denominator_left=self_L_denominator*other_L_denominator
                    yield (numerator_left,denominator_left),-1
                new_self_R=self._nearest_right
                new_other_R=other._nearest_right
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_R_is_updated or other_R_is_updated:
                    numerator_right=self_R_numerator*other_R_numerator
                    denominator_right=self_R_denominator*other_R_denominator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        def _refine_generator_for_pos_mul_neg(self,other:Self)->RefineOutput:
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_left=self_R_numerator*other_L_numerator
            denominator_left=self_R_denominator*other_L_denominator
            yield numerator_left,denominator_left
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_right=self_L_numerator*other_R_numerator
            denominator_right=self_L_denominator*other_R_denominator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (self_cross_R*other_cross_R,self_cross_L*other_cross_L),0
                new_self_R=self._nearest_right
                new_other_L=other._nearest_left
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_R_is_updated or other_L_is_updated:
                    numerator_left=self_R_numerator*other_L_numerator
                    denominator_left=self_R_denominator*other_L_denominator
                    yield (numerator_left,denominator_left),-1
                new_self_L=self._nearest_left
                new_other_R=other._nearest_right
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_L_is_updated or other_R_is_updated:
                    numerator_right=self_L_numerator*other_R_numerator
                    denominator_right=self_L_denominator*other_R_denominator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        def _refine_generator_for_neg_mul_pos(self,other:Self)->RefineOutput:
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_left=self_L_numerator*other_R_numerator
            denominator_left=self_L_denominator*other_R_denominator
            yield numerator_left,denominator_left
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_right=self_R_numerator*other_L_numerator
            denominator_right=self_R_denominator*other_L_denominator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (self_cross_L*other_cross_L,self_cross_R*other_cross_R),0
                new_self_L=self._nearest_left
                new_other_R=other._nearest_right
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_L_is_updated or other_R_is_updated:
                    numerator_left=self_L_numerator*other_R_numerator
                    denominator_left=self_L_denominator*other_R_denominator
                    yield (numerator_left,denominator_left),-1
                new_self_R=self._nearest_right
                new_other_L=other._nearest_left
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_R_is_updated or other_L_is_updated:
                    numerator_right=self_R_numerator*other_L_numerator
                    denominator_right=self_R_denominator*other_L_denominator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        def _refine_generator_for_neg_mul_neg(self,other:Self)->RefineOutput:
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_left=self_R_numerator*other_R_numerator
            denominator_left=self_R_denominator*other_R_denominator
            yield numerator_left,denominator_left
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_right=self_L_numerator*other_L_numerator
            denominator_right=self_L_denominator*other_L_denominator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (self_cross_R*other_cross_L,self_cross_L*other_cross_R),0
                new_self_R=self._nearest_right
                new_other_R=other._nearest_right
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_R_is_updated or other_R_is_updated:
                    numerator_left=self_R_numerator*other_R_numerator
                    denominator_left=self_R_denominator*other_R_denominator
                    yield (numerator_left,denominator_left),-1
                new_self_L=self._nearest_left
                new_other_L=other._nearest_left
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_L_is_updated or other_L_is_updated:
                    numerator_right=self_L_numerator*other_L_numerator
                    denominator_right=self_L_denominator*other_L_denominator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        @staticmethod
        def _interval_pos_mul_pos(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_left*op2_left
            init_right=op1_right*op2_right
            return init_left,init_right
        @staticmethod
        def _interval_pos_mul_neg(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_right*op2_left
            init_right=op1_left*op2_right
            return init_left,init_right
        @staticmethod
        def _interval_neg_mul_pos(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_left*op2_right
            init_right=op1_right*op2_left
            return init_left,init_right
        @staticmethod
        def _interval_neg_mul_neg(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_right*op2_right
            init_right=op1_left*op2_left
            return init_left,init_right
        @classmethod
        def _generated_operator_mul(cls,RR:RopR[Q],FIR_pos:IopR[Self],FIR_neg:IopR[Self],
                                    G_pos_pos:RefineGenerator[Self],I_pos_pos:Interval_op[Q],
                                    G_pos_neg:RefineGenerator[Self],I_pos_neg:Interval_op[Q],
                                    G_neg_pos:RefineGenerator[Self],I_neg_pos:Interval_op[Q],
                                    G_neg_neg:RefineGenerator[Self],I_neg_neg:Interval_op[Q])->tuple[Operation[Self],Operation[Self]]:
            FRI_pos=FIR_pos
            FRI_neg=FIR_neg
            factories_pos_pos=cls._factory_for_operator(RR,FIR_pos,FRI_pos,G_pos_pos)
            factories_pos_neg=cls._factory_for_operator(RR,FIR_neg,FRI_pos,G_pos_neg)
            factories_neg_pos=cls._factory_for_operator(RR,FIR_pos,FRI_neg,G_neg_pos)
            factories_neg_neg=cls._factory_for_operator(RR,FIR_neg,FRI_neg,G_neg_neg)
            FII_pos_pos=factories_pos_pos[4]
            FII_pos_neg=factories_pos_neg[4]
            FII_neg_pos=factories_neg_pos[4]
            FII_neg_neg=factories_neg_neg[4]
            products_pos_pos=cls._products_for_operator(factories_pos_pos,I_pos_pos)
            products_pos_neg=cls._products_for_operator(factories_pos_neg,I_pos_neg)
            products_neg_pos=cls._products_for_operator(factories_neg_pos,I_neg_pos)
            products_neg_neg=cls._products_for_operator(factories_neg_neg,I_neg_neg)
            UR_pos_pos,RU_pos_pos,UI_pos_pos,IU_pos_pos,UU_pos_pos=products_pos_pos
            UR_pos_neg,RU_pos_neg,UI_pos_neg,IU_pos_neg,UU_pos_neg=products_pos_neg
            UR_neg_pos,RU_neg_pos,UI_neg_pos,IU_neg_pos,UU_neg_pos=products_neg_pos
            UR_neg_neg,RU_neg_neg,UI_neg_neg,IU_neg_neg,UU_neg_neg=products_neg_neg
            def left_operator(self:Self,other:RealLike)->Self:
                local_cls=type(self)
                try: other_obj,other_is_possible_rational,other_is_possible_irrational=local_cls._analyze_input_for_operator(other)
                except TypeError: return NotImplemented
                if not other_is_possible_irrational:
                    numerator_other,denominator_other=other_obj
                    if numerator_other==0: return local_cls(0)
                    if not self._is_possible_irrational:
                        numerator_self,denominator_self=self._exact_rational.as_integer_ratio()
                        if numerator_self==0: return local_cls(0)
                        result=RR(numerator_self,denominator_self,numerator_other,denominator_other)
                        return local_cls(result,True,False)
                    self_is_positive=self._floor>=0
                    other_is_positive=numerator_other>0
                    if not self._is_possible_rational:
                        if other_is_positive:
                            new_sign_func=FIR_pos(self,numerator_other,denominator_other)
                            if self_is_positive: left,right=I_pos_pos(self._nearest_left,self._nearest_right,other_obj,other_obj)
                            else: left,right=I_neg_pos(self._nearest_left,self._nearest_right,other_obj,other_obj)
                        else:
                            new_sign_func=FIR_neg(self,numerator_other,denominator_other)
                            if self_is_positive: left,right=I_pos_neg(self._nearest_left,self._nearest_right,other_obj,other_obj)
                            else: left,right=I_neg_neg(self._nearest_left,self._nearest_right,other_obj,other_obj)
                        return local_cls(new_sign_func,False,True,left,right)
                    else:
                        if self_is_positive:
                            if other_is_positive: return UR_pos_pos(self,other_obj)
                            else: return UR_pos_neg(self,other_obj)
                        else:
                            if other_is_positive: return UR_neg_pos(self,other_obj)
                            else: return UR_neg_neg(self,other_obj)
                if not self._is_possible_irrational:
                    rational_self=self._exact_rational.as_integer_ratio()
                    numerator_self,denominator_self=rational_self
                    if numerator_self==0: return local_cls(0)
                    self_is_positive=numerator_self>0
                    other_is_positive=other_obj._floor>=0
                    if not other_is_possible_rational:
                        if self_is_positive:
                            new_sign_func=FRI_pos(other_obj,numerator_self,denominator_self)
                            if other_is_positive: left,right=I_pos_pos(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                            else: left,right=I_pos_neg(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                        else:
                            new_sign_func=FRI_neg(other_obj,numerator_self,denominator_self)
                            if other_is_positive: left,right=I_neg_pos(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                            else: left,right=I_neg_neg(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                        return local_cls(new_sign_func,False,True,left,right)
                    else:
                        if self_is_positive:
                            if other_is_positive: return RU_pos_pos(other_obj,rational_self)
                            else: return RU_pos_neg(other_obj,rational_self)
                        else:
                            if other_is_positive: return RU_neg_pos(other_obj,rational_self)
                            else: return RU_neg_neg(other_obj,rational_self)
                self_is_positive=self._floor>=0
                other_is_positive=other_obj._floor>=0
                if not other_is_possible_rational:
                    if not self._is_possible_rational:
                        if self_is_positive:
                            if other_is_positive:
                                new_sign_func=FII_pos_pos(self,other_obj)
                                left,right=I_pos_pos(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                            else:
                                new_sign_func=FII_pos_neg(self,other_obj)
                                left,right=I_pos_neg(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                        else:
                            if other_is_positive:
                                new_sign_func=FII_neg_pos(self,other_obj)
                                left,right=I_neg_pos(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                            else:
                                new_sign_func=FII_neg_neg(self,other_obj)
                                left,right=I_neg_neg(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                        return local_cls(new_sign_func,True,True,left,right)
                    else:
                        if self_is_positive:
                            if other_is_positive: return UI_pos_pos(self,other_obj)
                            else: return UI_pos_neg(self,other_obj)
                        else:
                            if other_is_positive: return UI_neg_pos(self,other_obj)
                            else: return UI_neg_neg(self,other_obj)
                else:
                    if not self._is_possible_rational:
                        if self_is_positive:
                            if other_is_positive: return IU_pos_pos(self,other_obj)
                            else: return IU_pos_neg(self,other_obj)
                        else:
                            if other_is_positive: return IU_neg_pos(self,other_obj)
                            else: return IU_neg_neg(self,other_obj)
                    else:
                        if self_is_positive:
                            if other_is_positive: return UU_pos_pos(self,other_obj)
                            else: return UU_pos_neg(self,other_obj)
                        else:
                            if other_is_positive: return UU_neg_pos(self,other_obj)
                            else: return UU_neg_neg(self,other_obj)
            def right_operator(self:Self,other:RealLike)->Self:
                local_cls=type(self)
                try: init_other_obj,is_exactly_rational=local_cls._analyze_input_for_sign_function(other)
                except TypeError: return NotImplemented
                if is_exactly_rational:
                    numerator_other,denominator_other=init_other_obj
                    if numerator_other==0: return local_cls(0)
                    if not self._is_possible_irrational:
                        numerator_self,denominator_self=self._exact_rational.as_integer_ratio()
                        result=RR(numerator_other,denominator_other,numerator_self,denominator_self)
                        return local_cls(result,True,False)
                    self_is_positive=self._floor>=0
                    other_is_positive=numerator_other>0
                    if not self._is_possible_rational:
                        if other_is_positive:
                            new_sign_func=FRI_pos(self,numerator_other,denominator_other)
                            if self_is_positive: left,right=I_pos_pos(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                            else: left,right=I_pos_neg(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                        else:
                            new_sign_func=FRI_neg(self,numerator_other,denominator_other)
                            if self_is_positive: left,right=I_neg_pos(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                            else: left,right=I_neg_neg(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                        return local_cls(new_sign_func,False,True,left,right)
                    else:
                        if other_is_positive:
                            if self_is_positive: return RU_pos_pos(self,init_other_obj)
                            else: return RU_pos_neg(self,init_other_obj)
                        else:
                            if self_is_positive: return RU_neg_pos(self,init_other_obj)
                            else: return RU_neg_neg(self,init_other_obj)
                else:
                    other_obj=local_cls.__new__(local_cls)
                    other_obj._is_called=False
                    other_obj.__init__(None,None,init_other_obj,True,True)
                    return left_operator(other_obj,self)
            return left_operator,right_operator
        #endregion

        #region: Division operation
        def keep_away_from_zero(self)->None:
            if not self._is_possible_irrational:
                if self._exact_rational==0: raise ValueError("Cannot keep away from zero for zero.")
                else: return
            else:
                left_integer=self._floor
                right_integer=self._ceil
                if left_integer==0 or right_integer==0:
                    self_is_positive=(left_integer==0)
                    if self_is_positive:
                        abs_sign_function=lambda n,d: self._init_sign_func(n,d)
                        abs_left=self._nearest_left
                        abs_right=self._nearest_right
                    else:
                        abs_sign_function=lambda n,d: -(self._init_sign_func(-n,d))
                        abs_left=-(self._nearest_right)
                        abs_right=-(self._nearest_left)
                    if abs_left.numerator==0:
                        right_denominator=abs_right.denominator//abs_right.numerator
                        left_denominator=right_denominator<<1
                    else:
                        left_denominator=-(-abs_left.denominator//abs_left.numerator)
                        right_denominator=abs_right.denominator//abs_right.numerator
                        temp_left_denominator=right_denominator<<1
                        if left_denominator<=temp_left_denominator: return
                        left_denominator=temp_left_denominator
                    compare_result=abs_sign_function(1,left_denominator)
                    while compare_result==1:
                        left_denominator=right_denominator
                        right_denominator=right_denominator<<1
                        compare_result=abs_sign_function(1,right_denominator)
        @classmethod
        def _rational_div_rational(cls,op1_numerator:int,op1_denominator:int,op2_numerator:int,op2_denominator:int)->Q:
            RaN=cls._Rational
            if op2_numerator>=0: result=RaN(op1_numerator*op2_denominator,op1_denominator*op2_numerator)
            else: result=RaN(-op1_numerator*op2_denominator,-op1_denominator*op2_numerator)
            return result
        def _irrational_div_pos_rational(self,numerator_input:int,denominator_input:int)->SignFunction:
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                numerator_mul=numerator*numerator_input
                denominator_mul=denominator*denominator_input
                return self._init_sign_func(numerator_mul,denominator_mul)
            return new_sign_func
        def _irrational_div_neg_rational(self,numerator_input:int,denominator_input:int)->SignFunction:
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                numerator_mul=numerator*numerator_input
                denominator_mul=denominator*denominator_input
                return -(self._init_sign_func(numerator_mul,denominator_mul))
            return new_sign_func
        def _pos_rational_div_pos_irrational(self,numerator_input:int,denominator_input:int)->SignFunction:
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                if numerator<=0: return -1
                else:
                    numerator_div=numerator_input*denominator
                    denominator_div=denominator_input*numerator
                    return -(self._init_sign_func(numerator_div,denominator_div))
            return new_sign_func
        def _neg_rational_div_pos_irrational(self,numerator_input:int,denominator_input:int)->SignFunction:
            numerator_input=-numerator_input
            denominator_input=-denominator_input
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                if numerator>=0: return 1
                else:
                    numerator_div=numerator_input*denominator
                    denominator_div=denominator_input*numerator
                    return self._init_sign_func(numerator_div,denominator_div)
            return new_sign_func
        def _pos_rational_div_neg_irrational(self,numerator_input:int,denominator_input:int)->SignFunction:
            numerator_input=-numerator_input
            denominator_input=-denominator_input
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                if numerator>=0: return 1
                else:
                    numerator_div=numerator_input*denominator
                    denominator_div=denominator_input*numerator
                    return -(self._init_sign_func(numerator_div,denominator_div))
            return new_sign_func
        def _neg_rational_div_neg_irrational(self,numerator_input:int,denominator_input:int)->SignFunction:
            def new_sign_func(numerator:int,denominator:int)->CompareResult:
                if numerator<=0: return -1
                else:
                    numerator_div=numerator_input*denominator
                    denominator_div=denominator_input*numerator
                    return self._init_sign_func(numerator_div,denominator_div)
            return new_sign_func
        def _refine_generator_for_pos_div_pos(self,other:Self)->RefineOutput:
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_left=self_L_numerator*other_R_denominator
            denominator_left=self_L_denominator*other_R_numerator
            yield numerator_left,denominator_left
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_right=self_R_numerator*other_L_denominator
            denominator_right=self_R_denominator*other_L_numerator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (self_cross_L*other_cross_R,self_cross_R*other_cross_L),0
                new_self_L=self._nearest_left
                new_other_R=other._nearest_right
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_L_is_updated or other_R_is_updated:
                    numerator_left=self_L_numerator*other_R_denominator
                    denominator_left=self_L_denominator*other_R_numerator
                    yield (numerator_left,denominator_left),-1
                new_self_R=self._nearest_right
                new_other_L=other._nearest_left
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_R_is_updated or other_L_is_updated:
                    numerator_right=self_R_numerator*other_L_denominator
                    denominator_right=self_R_denominator*other_L_numerator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        def _refine_generator_for_pos_div_neg(self,other:Self)->RefineOutput:
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_left=-self_R_numerator*other_R_denominator
            denominator_left=-self_R_denominator*other_R_numerator
            yield numerator_left,denominator_left
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_right=-self_L_numerator*other_L_denominator
            denominator_right=-self_L_denominator*other_L_numerator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (self_cross_R*other_cross_R,self_cross_L*other_cross_L),0
                new_self_R=self._nearest_right
                new_other_R=other._nearest_right
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_R_is_updated or other_R_is_updated:
                    numerator_left=-self_R_numerator*other_R_denominator
                    denominator_left=-self_R_denominator*other_R_numerator
                    yield (numerator_left,denominator_left),-1
                new_self_L=self._nearest_left
                new_other_L=other._nearest_left
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_L_is_updated or other_L_is_updated:
                    numerator_right=-self_L_numerator*other_L_denominator
                    denominator_right=-self_L_denominator*other_L_numerator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        def _refine_generator_for_neg_div_pos(self,other:Self)->RefineOutput:
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_left=self_L_numerator*other_L_denominator
            denominator_left=self_L_denominator*other_L_numerator
            yield numerator_left,denominator_left
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_right=self_R_numerator*other_R_denominator
            denominator_right=self_R_denominator*other_R_numerator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (self_cross_L*other_cross_L,self_cross_R*other_cross_R),0
                new_self_L=self._nearest_left
                new_other_L=other._nearest_left
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_L_is_updated or other_L_is_updated:
                    numerator_left=self_L_numerator*other_L_denominator
                    denominator_left=self_L_denominator*other_L_numerator
                    yield (numerator_left,denominator_left),-1
                new_self_R=self._nearest_right
                new_other_R=other._nearest_right
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_R_is_updated or other_R_is_updated:
                    numerator_right=self_R_numerator*other_R_denominator
                    denominator_right=self_R_denominator*other_R_numerator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        def _refine_generator_for_neg_div_neg(self,other:Self)->RefineOutput:
            self_R=self._nearest_right
            self_R_numerator=self_R.numerator
            self_R_denominator=self_R.denominator
            other_L=other._nearest_left
            other_L_numerator=other_L.numerator
            other_L_denominator=other_L.denominator
            numerator_left=-self_R_numerator*other_L_denominator
            denominator_left=-self_R_denominator*other_L_numerator
            yield numerator_left,denominator_left
            self_L=self._nearest_left
            self_L_numerator=self_L.numerator
            self_L_denominator=self_L.denominator
            other_R=other._nearest_right
            other_R_numerator=other_R.numerator
            other_R_denominator=other_R.denominator
            numerator_right=-self_L_numerator*other_R_denominator
            denominator_right=-self_L_denominator*other_R_numerator
            yield numerator_right,denominator_right
            self_cross_L=self_L_numerator*self_R_denominator
            self_cross_R=self_R_numerator*self_L_denominator
            other_cross_L=other_L_numerator*other_R_denominator
            other_cross_R=other_R_numerator*other_L_denominator
            self_L_is_updated=False
            self_R_is_updated=False
            other_L_is_updated=False
            other_R_is_updated=False
            while True:
                yield (self_cross_R*other_cross_L,self_cross_L*other_cross_R),0
                new_self_R=self._nearest_right
                new_other_L=other._nearest_left
                if new_self_R is not self_R:
                    self_R=new_self_R
                    self_R_numerator=self_R.numerator
                    self_R_denominator=self_R.denominator
                    self_R_is_updated=True
                if new_other_L is not other_L:
                    other_L=new_other_L
                    other_L_numerator=other_L.numerator
                    other_L_denominator=other_L.denominator
                    other_L_is_updated=True
                if self_R_is_updated or other_L_is_updated:
                    numerator_left=-self_R_numerator*other_L_denominator
                    denominator_left=-self_R_denominator*other_L_numerator
                    yield (numerator_left,denominator_left),-1
                new_self_L=self._nearest_left
                new_other_R=other._nearest_right
                if new_self_L is not self_L:
                    self_L=new_self_L
                    self_L_numerator=self_L.numerator
                    self_L_denominator=self_L.denominator
                    self_L_is_updated=True
                if new_other_R is not other_R:
                    other_R=new_other_R
                    other_R_numerator=other_R.numerator
                    other_R_denominator=other_R.denominator
                    other_R_is_updated=True
                if self_L_is_updated or other_R_is_updated:
                    numerator_right=-self_L_numerator*other_R_denominator
                    denominator_right=-self_L_denominator*other_R_numerator
                    yield (numerator_right,denominator_right),1
                if self_L_is_updated or self_R_is_updated:
                    self_cross_L=self_L_numerator*self_R_denominator
                    self_cross_R=self_R_numerator*self_L_denominator
                if other_L_is_updated or other_R_is_updated:
                    other_cross_L=other_L_numerator*other_R_denominator
                    other_cross_R=other_R_numerator*other_L_denominator
                if self_L_is_updated: self_L_is_updated=False
                if self_R_is_updated: self_R_is_updated=False
                if other_L_is_updated: other_L_is_updated=False
                if other_R_is_updated: other_R_is_updated=False
        @staticmethod
        def _interval_pos_div_pos(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_left/op2_right
            init_right=op1_right/op2_left
            return init_left,init_right
        @staticmethod
        def _interval_pos_div_neg(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_right/op2_right
            init_right=op1_left/op2_left
            return init_left,init_right
        @staticmethod
        def _interval_neg_div_pos(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_left/op2_left
            init_right=op1_right/op2_right
            return init_left,init_right
        @staticmethod
        def _interval_neg_div_neg(op1_left:Q|IntegerRatio,op1_right:Q|IntegerRatio,op2_left:Q|IntegerRatio,op2_right:Q|IntegerRatio)->tuple[Q,Q]:
            init_left=op1_right/op2_left
            init_right=op1_left/op2_right
            return init_left,init_right
        @classmethod
        def _generated_operator_div(cls,RR:RopR[Q],FIR_pos:IopR[Self],FIR_neg:IopR[Self],
                                    FRI_pos_pos:IopR[Self],G_pos_pos:RefineGenerator[Self],I_pos_pos:Interval_op[Q],
                                    FRI_pos_neg:IopR[Self],G_pos_neg:RefineGenerator[Self],I_pos_neg:Interval_op[Q],
                                    FRI_neg_pos:IopR[Self],G_neg_pos:RefineGenerator[Self],I_neg_pos:Interval_op[Q],
                                    FRI_neg_neg:IopR[Self],G_neg_neg:RefineGenerator[Self],I_neg_neg:Interval_op[Q])->tuple[Operation[Self],Operation[Self]]:
            factories_pos_pos=cls._factory_for_operator(RR,FIR_pos,FRI_pos_pos,G_pos_pos)
            factories_pos_neg=cls._factory_for_operator(RR,FIR_neg,FRI_pos_neg,G_pos_neg)
            factories_neg_pos=cls._factory_for_operator(RR,FIR_pos,FRI_neg_pos,G_neg_pos)
            factories_neg_neg=cls._factory_for_operator(RR,FIR_neg,FRI_neg_neg,G_neg_neg)
            FII_pos_pos=factories_pos_pos[4]
            FII_pos_neg=factories_pos_neg[4]
            FII_neg_pos=factories_neg_pos[4]
            FII_neg_neg=factories_neg_neg[4]
            products_pos_pos=cls._products_for_operator(factories_pos_pos,I_pos_pos)
            products_pos_neg=cls._products_for_operator(factories_pos_neg,I_pos_neg)
            products_neg_pos=cls._products_for_operator(factories_neg_pos,I_neg_pos)
            products_neg_neg=cls._products_for_operator(factories_neg_neg,I_neg_neg)
            UR_pos_pos,RU_pos_pos,UI_pos_pos,IU_pos_pos,UU_pos_pos=products_pos_pos
            UR_pos_neg,RU_pos_neg,UI_pos_neg,IU_pos_neg,UU_pos_neg=products_pos_neg
            UR_neg_pos,RU_neg_pos,UI_neg_pos,IU_neg_pos,UU_neg_pos=products_neg_pos
            UR_neg_neg,RU_neg_neg,UI_neg_neg,IU_neg_neg,UU_neg_neg=products_neg_neg
            def left_operator(self:Self,other:RealLike)->Self:
                local_cls=type(self)
                try: other_obj,other_is_possible_rational,other_is_possible_irrational=local_cls._analyze_input_for_operator(other)
                except TypeError: return NotImplemented
                if other_obj is self: return local_cls(1)
                if other_is_possible_irrational:
                    try: other_obj.keep_away_from_zero()
                    except ValueError: raise ZeroDivisionError("division by zero")
                    if not other_obj._is_possible_irrational:
                        other_obj=other_obj._exact_rational.as_integer_ratio()
                        other_is_possible_irrational=False
                    else: other_is_possible_rational=other_obj._is_possible_rational
                if not other_is_possible_irrational:
                    numerator_other,denominator_other=other_obj
                    if numerator_other==0: raise ZeroDivisionError("division by zero")
                    if not self._is_possible_irrational:
                        numerator_self,denominator_self=self._exact_rational.as_integer_ratio()
                        result=RR(numerator_self,denominator_self,numerator_other,denominator_other)
                        return local_cls(result,True,False)
                    self_is_positive=self._floor>=0
                    other_is_positive=numerator_other>0
                    if not self._is_possible_rational:
                        if other_is_positive:
                            new_sign_func=FIR_pos(self,numerator_other,denominator_other)
                            if self_is_positive: left,right=I_pos_pos(self._nearest_left,self._nearest_right,other_obj,other_obj)
                            else: left,right=I_neg_pos(self._nearest_left,self._nearest_right,other_obj,other_obj)
                        else:
                            new_sign_func=FIR_neg(self,numerator_other,denominator_other)
                            if self_is_positive: left,right=I_pos_neg(self._nearest_left,self._nearest_right,other_obj,other_obj)
                            else: left,right=I_neg_neg(self._nearest_left,self._nearest_right,other_obj,other_obj)
                        return local_cls(new_sign_func,False,True,left,right)
                    else:
                        if self_is_positive:
                            if other_is_positive: return UR_pos_pos(self,other_obj)
                            else: return UR_pos_neg(self,other_obj)
                        else:
                            if other_is_positive: return UR_neg_pos(self,other_obj)
                            else: return UR_neg_neg(self,other_obj)
                if not self._is_possible_irrational:
                    rational_self=self._exact_rational.as_integer_ratio()
                    numerator_self,denominator_self=rational_self
                    if numerator_self==0: return local_cls(0)
                    self_is_positive=numerator_self>0
                    other_is_positive=other_obj._floor>=0
                    if not other_is_possible_rational:
                        if self_is_positive:
                            if other_is_positive:
                                new_sign_func=FRI_pos_pos(other_obj,numerator_self,denominator_self)
                                left,right=I_pos_pos(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                            else:
                                new_sign_func=FRI_pos_neg(other_obj,numerator_self,denominator_self)
                                left,right=I_pos_neg(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                        else:
                            if other_is_positive:
                                new_sign_func=FRI_neg_pos(other_obj,numerator_self,denominator_self)
                                left,right=I_neg_pos(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                            else:
                                new_sign_func=FRI_neg_neg(other_obj,numerator_self,denominator_self)
                                left,right=I_neg_neg(rational_self,rational_self,other_obj._nearest_left,other_obj._nearest_right)
                        return local_cls(new_sign_func,False,True,left,right)
                    else:
                        if self_is_positive:
                            if other_is_positive: return RU_pos_pos(other_obj,rational_self)
                            else: return RU_pos_neg(other_obj,rational_self)
                        else:
                            if other_is_positive: return RU_neg_pos(other_obj,rational_self)
                            else: return RU_neg_neg(other_obj,rational_self)
                self_is_positive=self._floor>=0
                other_is_positive=other_obj._floor>=0
                if not other_is_possible_rational:
                    if not self._is_possible_rational:
                        if self_is_positive:
                            if other_is_positive:
                                new_sign_func=FII_pos_pos(self,other_obj)
                                left,right=I_pos_pos(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                            else:
                                new_sign_func=FII_pos_neg(self,other_obj)
                                left,right=I_pos_neg(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                        else:
                            if other_is_positive:
                                new_sign_func=FII_neg_pos(self,other_obj)
                                left,right=I_neg_pos(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                            else:
                                new_sign_func=FII_neg_neg(self,other_obj)
                                left,right=I_neg_neg(self._nearest_left,self._nearest_right,other_obj._nearest_left,other_obj._nearest_right)
                        return local_cls(new_sign_func,True,True,left,right)
                    else:
                        if self_is_positive:
                            if other_is_positive: return UI_pos_pos(self,other_obj)
                            else: return UI_pos_neg(self,other_obj)
                        else:
                            if other_is_positive: return UI_neg_pos(self,other_obj)
                            else: return UI_neg_neg(self,other_obj)
                else:
                    if not self._is_possible_rational:
                        if self_is_positive:
                            if other_is_positive: return IU_pos_pos(self,other_obj)
                            else: return IU_pos_neg(self,other_obj)
                        else:
                            if other_is_positive: return IU_neg_pos(self,other_obj)
                            else: return IU_neg_neg(self,other_obj)
                    else:
                        if self_is_positive:
                            if other_is_positive: return UU_pos_pos(self,other_obj)
                            else: return UU_pos_neg(self,other_obj)
                        else:
                            if other_is_positive: return UU_neg_pos(self,other_obj)
                            else: return UU_neg_neg(self,other_obj)
            def right_operator(self:Self,other:RealLike)->Self:
                local_cls=type(self)
                try: init_other_obj,is_exactly_rational=local_cls._analyze_input_for_sign_function(other)
                except TypeError: return NotImplemented
                if is_exactly_rational:
                    numerator_other,denominator_other=init_other_obj
                    try: self.keep_away_from_zero()
                    except ValueError: raise ZeroDivisionError("division by zero")
                    if not self._is_possible_irrational:
                        numerator_self,denominator_self=self._exact_rational.as_integer_ratio()
                        if numerator_self==0: raise ZeroDivisionError("division by zero")
                        result=RR(numerator_other,denominator_other,numerator_self,denominator_self)
                        return local_cls(result,True,False)
                    if numerator_other==0: return local_cls(0)
                    self_is_positive=self._floor>=0
                    other_is_positive=numerator_other>0
                    if not self._is_possible_rational:
                        if other_is_positive:
                            if self_is_positive:
                                new_sign_func=FRI_pos_pos(self,numerator_other,denominator_other)
                                left,right=I_pos_pos(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                            else:
                                new_sign_func=FRI_pos_neg(self,numerator_other,denominator_other)
                                left,right=I_pos_neg(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                        else:
                            if self_is_positive:
                                new_sign_func=FRI_neg_pos(self,numerator_other,denominator_other)
                                left,right=I_neg_pos(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                            else:
                                new_sign_func=FRI_neg_neg(self,numerator_other,denominator_other)
                                left,right=I_neg_neg(init_other_obj,init_other_obj,self._nearest_left,self._nearest_right)
                        return local_cls(new_sign_func,False,True,left,right)
                    else:
                        if other_is_positive:
                            if self_is_positive: return RU_pos_pos(self,init_other_obj)
                            else: return RU_pos_neg(self,init_other_obj)
                        else:
                            if self_is_positive: return RU_neg_pos(self,init_other_obj)
                            else: return RU_neg_neg(self,init_other_obj)
                else:
                    other_obj=local_cls.__new__(local_cls)
                    other_obj._is_called=False
                    other_obj.__init__(None,None,init_other_obj,True,True)
                    return left_operator(other_obj,self)
            return left_operator,right_operator
        #endregion
        #endregion
        
        def compare(self,other:RealLike)->CompareResult:
            cls=type(self)
            try: other_obj,_,other_is_possible_irrational=cls._analyze_input_for_operator(other)
            except TypeError: return NotImplemented
            if not other_is_possible_irrational:
                numerator_other,denominator_other=other_obj
                return self._sign_func(numerator_other,denominator_other)
            elif not self._is_possible_irrational:
                rational_self=self._exact_rational.as_integer_ratio()
                numerator_self,denominator_self=rational_self
                sign_other=other_obj._init_sign_func(numerator_self,denominator_self)
                return -sign_other
            else:
                self_L=self._nearest_left
                self_R=self._nearest_right
                other_L=other_obj._nearest_left
                other_R=other_obj._nearest_right
                if self_R.numerator*other_L.denominator<=self_R.denominator*other_L.numerator: return 1
                elif self_L.numerator*other_R.denominator>=self_L.denominator*other_R.numerator: return -1
                else:
                    if other_obj is self: return 0
                    self._regularize()
                    other_obj._regularize()
                    self_width=self.current_width(depend_on_structure=True)
                    other_width=other_obj.current_width(depend_on_structure=True)
                    cross_product_left=self_width.numerator*other_width.denominator
                    cross_product_right=self_width.denominator*other_width.numerator
                    if cross_product_left<cross_product_right:
                        left,right=self.current_bound(depend_on_structure=True)
                        numerator_left,denominator_left=left.numerator,left.denominator
                        compare_left=other_obj._init_sign_func(numerator_left,denominator_left)
                        if compare_left>=0: return -1
                        numerator_right,denominator_right=right.numerator,right.denominator
                        compare_right=other_obj._init_sign_func(numerator_right,denominator_right)
                        if compare_right<=0: return 1
                        other_obj._left_rational=left
                        other_obj._right_rational=right
                        other_obj._is_regular=True
                    elif cross_product_left>cross_product_right:
                        left,right=other_obj.current_bound(depend_on_structure=True)
                        numerator_left,denominator_left=left.numerator,left.denominator
                        compare_left=self._init_sign_func(numerator_left,denominator_left)
                        if compare_left>=0: return 1
                        numerator_right,denominator_right=right.numerator,right.denominator
                        compare_right=self._init_sign_func(numerator_right,denominator_right)
                        if compare_right<=0: return -1
                        self._left_rational=left
                        self._right_rational=right
                        self._is_regular=True
                    else:
                        left,right=self.current_bound(depend_on_structure=True)
                        numerator_left,denominator_left=left.numerator,left.denominator
                        numerator_right,denominator_right=right.numerator,right.denominator
                    while True:
                        numerator_mid=numerator_left+numerator_right
                        denominator_mid=denominator_left+denominator_right
                        compare_mid_self=self._init_sign_func(numerator_mid,denominator_mid,input_is_regular=True)
                        compare_mid_other=other_obj._init_sign_func(numerator_mid,denominator_mid,input_is_regular=True)
                        if compare_mid_self==-1:
                            if compare_mid_other==-1: 
                                numerator_left=numerator_mid
                                denominator_left=denominator_mid
                            else: return -1
                        elif compare_mid_self==1:
                            if compare_mid_other==1:
                                numerator_right=numerator_mid
                                denominator_right=denominator_mid
                            else: return 1
                        else: return -compare_mid_other
        def __eq__(self,other:RealLike)->bool|NotImplementedType:
            result=self.compare(other)
            if result is NotImplemented: return NotImplemented
            return result==0
        def __ne__(self,other:RealLike)->bool|NotImplementedType:
            result=self.compare(other)
            if result is NotImplemented: return NotImplemented
            return result!=0
        def __lt__(self,other:RealLike)->bool|NotImplementedType:
            result=self.compare(other)
            if result is NotImplemented: return NotImplemented
            return result==1
        def __le__(self,other:RealLike)->bool|NotImplementedType:
            result=self.compare(other)
            if result is NotImplemented: return NotImplemented
            return result!=-1
        def __gt__(self,other:RealLike)->bool|NotImplementedType:
            result=self.compare(other)
            if result is NotImplemented: return NotImplemented
            return result==-1
        def __ge__(self,other:RealLike)->bool|NotImplementedType:
            result=self.compare(other)
            if result is NotImplemented: return NotImplemented
            return result!=1

        @classmethod
        def root_finding(cls,func:Callable[[int,int],RealLike],interval:tuple[RationalLike,RationalLike])->Self:
            '''
            Please ensure that the input function is continuous and there is exactly one root in the input finite rational interval and has opposite signs at
            endpoints. Note that the input function must accept two integer numerator/denominator as input
            '''
            Rationalclass=cls._Rational
            init_left,init_right=interval
            init_left,init_right=Rationalclass(init_left),Rationalclass(init_right)
            if init_left.denominator==0 or init_right.denominator==0: raise ValueError('interval must be finite')
            if init_left>init_right: init_left,init_right=init_right,init_left
            if init_left==init_right: return cls._convert_from_rational(init_left)
            analyzer=Rationalclass._analyze_input_for_one_argument
            def value_sign_func(numerator:int,denominator:int)->CompareResult:
                value=func(numerator,denominator)
                try:
                    numerator_value,denominator_value,_=analyzer(value)
                    if numerator_value>0: return 1
                    if numerator_value<0: return -1
                    if denominator_value==0: raise ValueError('The function output cannot be \'Not a Number\'')
                    return 0
                except TypeError:
                    if isinstance(value,cls._family_root): compare=value._sign_func(0,1); return -compare
                    else: compare=value(0,1); return -compare
            left_sign=value_sign_func(init_left.numerator,init_left.denominator)
            if left_sign==0: return cls._convert_from_rational(init_left)
            right_sign=value_sign_func(init_right.numerator,init_right.denominator)
            if right_sign==0: return cls._convert_from_rational(init_right)
            if left_sign*right_sign==1: raise ValueError('The function must have opposite signs at the endpoints of the interval')
            if left_sign>0:
                def compare_func(numerator,denominator): return -value_sign_func(numerator,denominator)
                return cls(compare_func,is_possible_rational=True,is_possible_irrational=True,left=init_left,right=init_right)
            else: return cls(value_sign_func,is_possible_rational=True,is_possible_irrational=True,left=init_left,right=init_right)


ComputableRational=ComputableNumber.RationalNumber
ComputableReal=ComputableNumber.RealNumber



#
# func.py: general function objects
# Author: Johann Hibschman <johann@physics.berkeley.edu>
#
# Copyright (C) Johann Hibschman 1997
#
# Upgraded to numpy Lisa Tauxe 2/6/07
#
# Enhanced for use with numpy functions (ufuncs)

# All of the functions are combined with numpy ufuncs; this loses
# some performance when the functions are used on scalar arguments,
# but should give a big win on vectors.
# 

from builtins import range
from builtins import object
import numpy
from numpy import *
import operator
import math
from types import *

ArrayType = type(asarray(1.0))
UfuncType = type(numpy.add)

# unary function objects (maybe rename to UN_FUNC?)

class FuncOps(object):
    """
    Common mix-in operations for function objects.
    Normal function classes are assumed to implement a call routine,
    which will be chained to in the __call__ method.
    """
    def compose(self, f):
        return UnCompose(self, f)

    def __add__(self, f):
        return BinCompose(numpy.add, self, f)

    def __sub__(self, f):
        return BinCompose(numpy.subtract, self, f)

    def __mul__(self, f):
        return BinCompose(numpy.multiply, self, f)

    def __div__(self, f):
        return BinCompose(numpy.divide, self, f)

    def __neg__(self):
        return UnCompose(numpy.negative, self)

    def __pow__(self, f):
        return BinCompose(numpy.power, self, f)

    def __coerce__(self, x):
        if type(x) in [IntType, FloatType, LongType, ComplexType]:
            return (self, UnConstant(x))
        else:
            return (self, x)

    def __call__(self, arg):
        "Default call routine, used for ordinary functions."
        if type(arg) == ArrayType:
            return array_map(self.call, arg)
        else:
            return self.call(arg)

    def exp(self):
        return UnCompose(numpy.exp, self)

    def log(self):
        return UnCompose(numpy.log, self)



# Bind a normal function
# Should check if the argument is a function.
class FuncBinder(FuncOps):
    def __init__(self, a_f):
        if ((type(a_f) == UfuncType)
            or
            (type(a_f) == InstanceType and
             FuncOps in a_f.__class__.__bases__)):
            self.__call__ = a_f        # overwrite the existing call method
        self.call = a_f


# wrap a constant in a Function class
class UnConstant(FuncOps):
    def __init__(self, x):
        self.constant = x
    def __call__(self, x):
        return self.constant

# just return the argument: f(x) = x
# This is used to build up more complex expressions.
class Identity(FuncOps):
    def __init__(self):
        pass
    def __call__(self, arg):
        return arg


# compose two unary functions
class UnCompose(FuncOps):
   def __init__(self, a_f, a_g):
      self.f = a_f
      self.g = a_g
   def __call__(self, arg):
      return self.f(self.g(arg))


# -------------------------------------------------
# binary function objects

# classes of composition:
#    a,b,c,d: binary functions m,n,o: unary functions
#    d=c.compose(a,b) - c(a(x,y),b(x,y)) - used for a/b, a*b, etc.
#    m=c.compose(n,o) - c(n(x), o(x))
#    d=c.compose(n,o) - c(n(x), o(y))
#    d=m.compose(c)   - m(c(x,y))


class BinFuncOps(object):
    # returns self(f(x), g(x)), a unary function
    def compose(self, f, g):
        return BinCompose(self, f, g)

    # returns self(f(x), g(y)), a binary function
    def compose2(self, f, g):
        return BinUnCompose(self, f, g)

    # returns f(self(x,y)), a binary function
    def compose_by(self, f):
        return UnBinCompose(f, self)

    def __add__(self, f):
        return BinBinCompose(operator.add, self, f)

    def __sub__(self, f):
        return BinBinCompose(operator.sub, self, f)

    def __mul__(self, f):
        return BinBinCompose(operator.mul, self, f)

    def __div__(self, f):
        return BinBinCompose(operator.div, self, f)

    def __pow__(self, f):
        return BinBinCompose(pow, self, f)

    def __neg__(self):
        return UnBinCompose(operator.neg, self)

    def reduce(self, a, axis=0):
        result = take(a, [0], axis)
        for i in range(1, a.shape[axis]):
            result = self(result, take(a, [i], axis))
        return result

    def accumulate(self, a, axis=0):
        n = len(a.shape)
        sum = take(a, [0], axis)
        out = zeros(a.shape, a.typecode())
        for i in range(1, a.shape[axis]):
            out[all_but_axis(i, axis, n)] = self(sum, take(a, [i], axis))
        return out

    def outer(self, a, b):
        n_a = len(a.shape)
        n_b = len(b.shape)
        a2  = reshape(a, a.shape + (1,)*n_b)
        b2  = reshape(b, (1,)*n_a + b.shape)

        # duplicate each array in the appropriate directions
        a3  = a2
        for i in range(n_b):
            a3 = repeat(a3, (b.shape[i],), n_a+i)
        b3 = b2
        for i in range(n_a):
            b3 = repeat(b3, (a.shape[i],), i)

        answer = array_map_2(self, a3, b3)
        return answer


def all_but_axis(i, axis, num_axes):
    """
    Return a slice covering all combinations with coordinate i along
    axis.  (Effectively the hyperplane perpendicular to axis at i.)
    """
    the_slice  = ()
    for j in range(num_axes):
        if j == axis:
            the_slice = the_slice + (i,)
        else:
            the_slice = the_slice + (slice(None),)
    return the_slice


# bind a binary function
class BinFuncBinder(BinFuncOps):
   def __init__(self, a_f):
      self.f = a_f

   def __call__(self, arg1, arg2):
      return self.f(arg1, arg2)


# bind single variables
class BinVar1(BinFuncOps):
    def __init__(self):
        pass
    def __call__(self, arg1, arg2):
        return arg1

class BinVar2(BinFuncOps):
    def __init__(self):
        pass
    def __call__(self, arg1, arg2):
        return arg2

# bind individual variables within a binary function
class Bind1st(FuncOps):
    def __init__(self, a_f, an_arg1):
        self.f = a_f
        self.arg1 = an_arg1
    def __call__(self, x):
        return self.f(self.arg1, x)

class Bind2nd(FuncOps):
    def __init__(self, a_f, an_arg2):
        self.f = a_f
        self.arg2 = an_arg2
    def __call__(self, x):
        return self.f(x, self.arg2)

# compose binary function with two unary functions (=> unary fcn)
# i.e. given a(x,y), b(x), c(x), : d(x) = a(b(x),c(x))
# (what about e(x,y) = a(b(x), c(y)?)

class BinCompose(FuncOps):
    def __init__(self, a_binop, a_f, a_g):
        self.binop = a_binop
        self.f     = a_f
        self.g     = a_g
        self.temp  = lambda x, op=a_binop, f=a_f, g=a_g: op(f(x),g(x))

    def __call__(self, arg):
        # return self.binop(self.f(arg), self.g(arg))
        return self.temp(arg)


# compose a unary function with a binary function to get a binary
# function: f(g(x,y))

class UnBinCompose(BinFuncOps):
   def __init__(self, a_f, a_g):
       self.f = a_f
       self.g = a_g

   def __call__(self, arg1, arg2):
       return self.f(self.g(arg1, arg2))


# compose a two unary functions with a binary function to get a binary
# function: f(g(x), h(y))
class BinUnCompose(BinFuncOps):
    def __init__(self, a_f, a_g, a_h):
        self.f = a_f
        self.g = a_g
        self.h = a_h

    def __call__(self, arg1, arg2):
        return self.f(self.g(arg1), self.h(arg2))



# compose two binary functions together, using a third binary function
# to make the composition: h(f(x,y), g(x,y))
class BinBinCompose(BinFuncOps):
    def __init__(self, a_h, a_f, a_g):
        self.f = a_f
        self.g = a_g
        self.h = a_h

    def __call__(self, arg1, arg2):
        return self.h(self.f(arg1, arg2), self.g(arg1, arg2))

# ----------------------------------------------------
# Array mapping routines

def array_map(f, ar):
    "Apply an ordinary function to all values in an array."
    flat_ar = ravel(ar)
    out = zeros(len(flat_ar), flat_ar.typecode())
    for i in range(len(flat_ar)):
        out[i] = f(flat_ar[i])
    out.shape = ar.shape
    return out

def array_map_2(f, a, b):
    if a.shape != b.shape:
        raise ShapeError
    flat_a = ravel(a)
    flat_b = ravel(b)
    out    = zeros(len(flat_a), a.typecode())
    for i in range(len(flat_a)):
        out[i] = f(flat_a[i], flat_b[i])
    return reshape(out, a.shape)

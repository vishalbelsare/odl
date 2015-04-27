# -*- coding: utf-8 -*-
"""
simple_test_astra.py -- a simple test script

Copyright 2014, 2015 Holger Kohr

This file is part of RL.

RL is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RL is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with RL.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import division, print_function, unicode_literals, absolute_import
from future import standard_library
standard_library.install_aliases()
import unittest

import numpy as np
import RL.operator.operator as op
import RL.space.space as space
from RL.space.euclidean import EuclidianSpace

from RL.utility.testutils import RLTestCase


class MultiplyOp(op.LinearOperator):
    """Multiply with matrix
    """

    def __init__(self, matrix, domain = None, range = None):
        self._domain = EuclidianSpace(matrix.shape[1]) if domain is None else domain
        self._range = EuclidianSpace(matrix.shape[0]) if range is None else range
        self.matrix = matrix

    def applyImpl(self, rhs, out):
        np.dot(self.matrix, rhs.values, out=out.values)

    def applyAdjointImpl(self, rhs, out):
        np.dot(self.matrix.T, rhs.values, out=out.values)

    @property
    def domain(self):           
        return self._domain

    @property
    def range(self):            
        return self._range

class TestRN(RLTestCase):   
    def testSquareMultiplyOp(self):
        #Verify that the multiply op does indeed work as expected

        A = np.random.rand(3, 3)
        x = np.random.rand(3)
        out = np.random.rand(3)

        Aop = MultiplyOp(A)
        xvec = Aop.domain.makeVector(x)
        outvec = Aop.range.empty()

        #Using apply
        Aop.apply(xvec,outvec)
        np.dot(A,x,out)
        self.assertAllAlmostEquals(out, outvec)

        #Using __call__
        self.assertAllAlmostEquals(Aop(xvec), np.dot(A,x))


    def testNonSquareMultiplyOp(self):
        #Verify that the multiply op does indeed work as expected
        A = np.random.rand(4, 3)
        x = np.random.rand(3)
        out = np.random.rand(4)

        Aop = MultiplyOp(A)
        xvec = Aop.domain.makeVector(x)
        outvec = Aop.range.empty()

        #Using apply
        Aop.apply(xvec,outvec)
        np.dot(A,x,out)
        self.assertAllAlmostEquals(out, outvec)

        #Using __call__
        self.assertAllAlmostEquals(Aop(xvec), np.dot(A,x))


    def testAdjoint(self):
        A = np.random.rand(4, 3)
        x = np.random.rand(4)
        out = np.random.rand(3)

        Aop = MultiplyOp(A)
        xvec = Aop.range.makeVector(x)
        outvec = Aop.domain.empty()

        #Using applyAdjoint
        Aop.applyAdjoint(xvec,outvec)
        np.dot(A.T,x,out)
        self.assertAllAlmostEquals(out, outvec)

        #By creating an OperatorAdjoint object
        self.assertAllAlmostEquals(op.OperatorAdjoint(Aop)(xvec), np.dot(A.T,x))

        #Using T method and __call__
        self.assertAllAlmostEquals(Aop.T(xvec), np.dot(A.T,x))


    def testAdd(self):
        A = np.random.rand(4, 3)
        B = np.random.rand(4, 3)
        x = np.random.rand(3)
        y = np.random.rand(4)

        Aop = MultiplyOp(A)
        Bop = MultiplyOp(B)
        xvec = Aop.domain.makeVector(x)
        yvec = Aop.range.makeVector(y)

        #Explicit instantiation
        C = op.LinearOperatorSum(Aop, Bop)
        
        self.assertAllAlmostEquals(C(xvec), np.dot(A,x) + np.dot(B,x))
        self.assertAllAlmostEquals(C.T(yvec), np.dot(A.T,y) + np.dot(B.T,y))

        #Using operator overloading        
        self.assertAllAlmostEquals((Aop + Bop)(xvec), np.dot(A,x) + np.dot(B,x))
        self.assertAllAlmostEquals((Aop + Bop).T(yvec), np.dot(A.T,y) + np.dot(B.T,y))

    def testScale(self):
        A = np.random.rand(4, 3)
        B = np.random.rand(4, 3)
        x = np.random.rand(3)
        y = np.random.rand(4)

        Aop = MultiplyOp(A)
        xvec = Aop.domain.makeVector(x)
        yvec = Aop.range.makeVector(y)

        #Test a range of scalars (scalar multiplication could implement optimizations for (-1, 0, 1).
        scalars = [-1.432, -1, 0, 1, 3.14]
        for scale in scalars:
            C = op.LinearOperatorScalarMultiplication(Aop, scale)
        
            self.assertAllAlmostEquals(C(xvec), scale * np.dot(A,x))
            self.assertAllAlmostEquals(C.T(yvec), scale * np.dot(A.T, y))

            #Using operator overloading        
            self.assertAllAlmostEquals((scale * Aop)(xvec), scale * np.dot(A, x))
            self.assertAllAlmostEquals((Aop * scale)(xvec), np.dot(A, scale * x))
            self.assertAllAlmostEquals((scale * Aop).T(yvec), scale * np.dot(A.T, y))
            self.assertAllAlmostEquals((Aop * scale).T(yvec), np.dot(A.T, scale * y))


    def testCompose(self):
        A = np.random.rand(5, 4)
        B = np.random.rand(4, 3)
        x = np.random.rand(3)
        y = np.random.rand(5)

        Aop = MultiplyOp(A)
        Bop = MultiplyOp(B)
        xvec = Bop.domain.makeVector(x)
        yvec = Aop.range.makeVector(y)

        C = op.LinearOperatorComposition(Aop, Bop)

        self.assertAllAlmostEquals(C(xvec), np.dot(A, np.dot(B, x)))
        self.assertAllAlmostEquals(C.T(yvec), np.dot(B.T, np.dot(A.T, y)))

    def testTypechecking(self):
        r3 = EuclidianSpace(3)
        r4 = EuclidianSpace(4)

        Aop = MultiplyOp(np.random.rand(3, 3))
        r3Vec1 = r3.zero()        
        r3Vec2 = r3.zero()
        r4Vec1 = r4.zero()
        r4Vec2 = r4.zero()
        
        #Verify that correct usage works
        Aop.apply(r3Vec1, r3Vec2)
        Aop.applyAdjoint(r3Vec1, r3Vec2)

        #Test that erroneous usage raises TypeError
        with self.assertRaises(TypeError):  
            Aop(r4Vec1)

        with self.assertRaises(TypeError):  
            Aop.T(r4Vec1)

        with self.assertRaises(TypeError):  
            Aop.apply(r3Vec1, r4Vec1)

        with self.assertRaises(TypeError):  
            Aop.applyAdjoint(r3Vec1, r4Vec1)

        with self.assertRaises(TypeError):  
            Aop.apply(r4Vec1, r3Vec1)

        with self.assertRaises(TypeError):  
            Aop.applyAdjoint(r4Vec1, r3Vec1)

        with self.assertRaises(TypeError):  
            Aop.apply(r4Vec1, r4Vec2)

        with self.assertRaises(TypeError):  
            Aop.applyAdjoint(r4Vec1, r4Vec2)

        #Check test against aliased values
        with self.assertRaises(ValueError):  
            Aop.apply(r3Vec1, r3Vec1)
            
        with self.assertRaises(ValueError):  
            Aop.applyAdjoint(r3Vec1, r3Vec1)


if __name__ == '__main__':
    unittest.main(exit=False)

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


class MultiplyAndSquareOp(op.Operator):
    """ Example of a nonlinear operator, Calculates (A*x)**2
    """

    def __init__(self, matrix, domain = None, range = None):
        self._domain = EuclidianSpace(matrix.shape[1]) if domain is None else domain
        self._range = EuclidianSpace(matrix.shape[0]) if range is None else range
        self.matrix = matrix

    def applyImpl(self, rhs, out):
        np.dot(self.matrix, rhs.values, out=out.values)
        out.values **= 2

    def applyAdjointImpl(self, rhs, out):
        np.dot(self.matrix.T, rhs.values, out=out.values)
        out.values **= 2

    @property
    def domain(self):           
        return self._domain

    @property
    def range(self):            
        return self._range

    def __str__(self):
        return "MaS: " + str(self.matrix) + "**2"

def opNumpy(A, x):
    #The same as MultiplyAndSquareOp but only using numpy
    return np.dot(A,x)**2

class TestRN(RLTestCase):   
    def testMultiplyAndSquareOp(self):
        #Verify that the operator does indeed work as expected
        A = np.random.rand(4, 3)
        x = np.random.rand(3)
        Aop = MultiplyAndSquareOp(A)
        xvec = Aop.domain.makeVector(x)

        self.assertAllAlmostEquals(Aop(xvec), opNumpy(A, x))

    def testAdd(self):
        #Test operator addition
        A = np.random.rand(4, 3)
        B = np.random.rand(4, 3)
        x = np.random.rand(3)

        Aop = MultiplyAndSquareOp(A)
        Bop = MultiplyAndSquareOp(B)
        xvec = Aop.domain.makeVector(x)

        #Explicit instantiation
        C = op.OperatorSum(Aop, Bop)
        self.assertAllAlmostEquals(C(xvec), opNumpy(A,x) + opNumpy(B,x))

        #Using operator overloading        
        self.assertAllAlmostEquals((Aop + Bop)(xvec), opNumpy(A,x) + opNumpy(B,x))

        #Verify that unmatched operators domains fail
        C = np.random.rand(4, 4)
        Cop = MultiplyAndSquareOp(C)

        with self.assertRaises(TypeError):
            C = op.OperatorSum(Aop, Cop)

    def testScale(self):
        A = np.random.rand(4, 3)
        x = np.random.rand(3)

        Aop = MultiplyAndSquareOp(A)
        xvec = Aop.domain.makeVector(x)

        #Test a range of scalars (scalar multiplication could implement optimizations for (-1, 0, 1)).
        scalars = [-1.432, -1, 0, 1, 3.14]
        for scale in scalars:
            LeftScaled = op.OperatorLeftScalarMultiplication(Aop, scale)
            RightScaled = op.OperatorRightScalarMultiplication(Aop, scale)
        
            self.assertAllAlmostEquals(LeftScaled(xvec), scale * opNumpy(A,x))
            self.assertAllAlmostEquals(RightScaled(xvec), opNumpy(A, scale * x))

            #Using operator overloading
            self.assertAllAlmostEquals((scale * Aop)(xvec), scale*opNumpy(A,x))
            self.assertAllAlmostEquals((Aop * scale)(xvec), opNumpy(A, scale*x))

        #Fail when scaling by wrong scalar type (A complex number)
        NonScalars = [1j, [1,2], Aop] #Define some objects that are not scalars
        for nonscalar in NonScalars: 
            with self.assertRaises(TypeError):
                C = op.OperatorLeftScalarMultiplication(Aop, nonscalar)

            with self.assertRaises(TypeError):
                C = op.OperatorRightScalarMultiplication(Aop, nonscalar)

            with self.assertRaises(TypeError):
                C = Aop * nonscalar

            with self.assertRaises(TypeError):
                C = nonscalar * Aop

           


    def testCompose(self):
        A = np.random.rand(5, 4)
        B = np.random.rand(4, 3)
        x = np.random.rand(3)

        Aop = MultiplyAndSquareOp(A)
        Bop = MultiplyAndSquareOp(B)
        xvec = Bop.domain.makeVector(x)

        C = op.OperatorComposition(Aop, Bop)

        self.assertAllAlmostEquals(C(xvec), opNumpy(A,opNumpy(B,x)))

        #Verify that incorrect order fails
        with self.assertRaises(TypeError):
            C = op.OperatorComposition(Bop, Aop)


if __name__ == '__main__':
    unittest.main(exit=False)

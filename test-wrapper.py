#!/usr/bin/env python
# test-f.py

import numpy as np
import scipy as scp
import scipy.sparse as sp
import wrapper  # loads f.so from cc-lib: f.pyx -> f.c + fc.o -> f.so


# Testing Cython code with a function and a coo_Matrix.
# passing data row and col numpy arrays to c++ and executing function

A = sp.coo_matrix([[1,2,4,5],[4,5,6,7],[7,8,9,10]])
N = 3
a = A.data.round(6).astype(np.double)
b = A.row.astype(np.int_)
c = A.col.astype(np.int_)
y = np.ascontiguousarray(np.zeros((a.size,1) , dtype=np.double).flatten())
print y 
result = wrapper.fpy(N, a, b, c, y)

#print Results of In and Output

print "DataInput a: ",a
print "DataInput b: ",b
print "DataInput c: ",c
print "DataOutput in Python function : ",result

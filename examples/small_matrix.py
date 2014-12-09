from scipy.io import mmread
import scipy.sparse as sp
import wrapper
import numpy as np


M = mmread("../data/graphs/grid_2x2.mtx")
M = sp.coo_matrix(M.todense() + np.eye(4))
evid = np.array([1,0,0,2]) #evidence: var 1 is observed
colors = wrapper.epSaucy(M.data.round(6).astype(np.float), M.row.astype(np.uintp), M.col.astype(np.uintp), evid.astype(np.uintp), np.int32(0), np.int32(1));
print "var colors: ", colors[0:4]
print "edge colors: ", colors[4:]
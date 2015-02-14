import reloop.utils.saucywrapper as saucywrapper
import scipy.sparse as sp
import numpy as np
import time

def epBipartite(A, b, c, orb):
	_, cmod = np.unique(np.array(c.todense()), return_inverse=True)
	_, bmod = np.unique(np.array(b.todense()), return_inverse=True)
	_, data = np.unique(A.data.round(6), return_inverse=True)
	colors = saucywrapper.epSaucyBipartite(
            data.astype(np.uintp), A.row.astype(np.uintp),
            A.col.astype(np.uintp), bmod.astype(np.uintp),
            cmod.astype(np.uintp), np.int32(0), np.int32(orb))
	n = c.shape[0]
	m = b.shape[0]
	_, bcols2 = np.unique(colors[m:n + m], return_inverse=True)
	_, rcols2 = np.unique(colors[0:m], return_inverse=True)
	return [rcols2, bcols2]


def liftAbc(Ar, br, cr, sparse=True, orbits=False, sumrefine=False):
	"""
	TODO

	:param Ar:
	:type Ar:
	:param br:
	:type br:
	:param cr:
	:type cr:
	:param sparse:
	:type sparse:
	:param orbits:
	:type orbits:
	:param sumrefine:
	:type sumrefine:

	:returns:
	"""
	if sparse:
	    AC = Ar.tocoo()
	else:
	    AC = sp.coo_matrix(Ar)
	starttime = time.clock()
	co = sp.lil_matrix(cr)
	bo = sp.lil_matrix(br)
	_, data = np.unique(AC.data.round(6), return_inverse=True)
	o = 1
	if orbits:
	    o = 0
	if sumrefine and not orbits:
	    saucycolors = sumRefinement(AA, cc)
	else:
	    [rcols2, bcols2] = epBipartite(Ar, br, cr, o)
	    
	print "refinement took: ", time.clock() - starttime, "seconds."

	n = cr.shape[0]
	m = br.shape[0]
	brows = np.array(range(n))
	bdata = np.ones(n, dtype=np.int)
	Bcc2 = sp.csr_matrix((bdata, np.vstack((brows, bcols2))), dtype=np.int).tocsr()

	_, rowfilter2 = np.unique(rcols2, return_index=True)

	LA2 = AC.tocsr()[rowfilter2, :] * Bcc2

	Lc = (co.T * Bcc2).T
	Lb = bo[rowfilter2].todense()
	compresstime = time.clock() - starttime
	LA2 = LA2.tocoo()
	Lc = Lc.todense()

	return LA2, Lb, Lc, compresstime, Bcc2
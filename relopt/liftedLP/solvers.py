#!/usr/bin/python
## @package liftedLP_glpk
#TODO
#
#

'''
Created on Dec 28, 2010

@author: Martin Mladenov
'''
import glob
import scipy.io
from cvxopt import matrix,spmatrix
from cvxopt import solvers
from cvxopt import printing
import time
import sys
from sys import argv
from math import fabs, log, exp
import numpy as np
import scipy.sparse as sp
import picos as pic
import relopt.liftedLP.saucywrap as saucy


def rowUnique(a):
    """
    TODO

    :param a:
    :type a:

    :returns:
    """

    b = np.ascontiguousarray(a).view(np.dtype((np.void, a.dtype.itemsize * a.shape[1])))
    _, idx = np.unique(b, return_inverse=True)
    return idx

def col2matrix(c):
    """
    TODO

    :param c:
    :type c:

    :returns:
    """

    brows = np.array(range(len(c)))
    bdata = np.ones(len(c),dtype=np.int)
    Bcc = sp.csr_matrix((bdata,np.vstack((brows,c))),dtype=np.int).tocsr()
    return Bcc

def sumRefinement(A, b):
    """
    TODO

    :param A:
    :type A:
    :param b:
    :type b:

    :returns:
    """

    print "SumRef starting"
    czero = b
    ncols = np.max(b) + 1
    ncolsold = 0
    while ncols != ncolsold:
        B = col2matrix(czero)
        czero = rowUnique((A*B).todense())
        ncolsold = ncols
        ncols = np.max(czero) + 1
    return czero

def lift(Ar, br, cr, sparse=True, orbits=False, sumRefine=False):
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
    :param sumRefine:
    :type sumRefine:

    :returns:
    """
    if sparse:
        AC = Ar.tocoo()
    else:
        AC = sp.coo_matrix(Ar)
    starttime = time.clock()
    if (not sparse):

        _, cmod = np.unique(np.array(cr), return_inverse=True)
        _, bmod = np.unique(np.array(br), return_inverse=True)

    else:
        _, cmod = np.unique(np.array(cr.todense()), return_inverse=True)
        _, bmod = np.unique(np.array(br.todense()), return_inverse=True)

    # cmod = cmod + np.max(bmod) + 1
    # b = sp.lil_matrix(bmod)
    # c = sp.lil_matrix(cmod)

    co = sp.lil_matrix(cr)
    bo = sp.lil_matrix(br)
    _, data =  np.unique(AC.data.round(6), return_inverse=True)
    o = 1
    if orbits: o = 0 
    if sumRefine and not orbits: 
        bcolsSaucy2 = sumRefinement(AA,cc)
    else: 
        # bcolsSaucy = wrapper.epSaucy(T.data.round(6).astype(np.float), T.row.astype(np.uintp), T.col.astype(np.uintp), cc.astype(np.uintp), np.int32(0), np.int32(o));
        bcolsSaucy2 = saucy.epSaucyBipartite(data.astype(np.uintp), AC.row.astype(np.uintp), AC.col.astype(np.uintp), bmod.astype(np.uintp), cmod.astype(np.uintp), np.int32(0), np.int32(o));
    print "refinement took: ", time.clock() - starttime, "seconds."
    # print bcolsSaucy2
    n =  cmod.shape[0]
    m = bmod.shape[0]
    # _, bcols = np.unique(bcolsSaucy[0:n], return_inverse=True)
    _, bcols2 = np.unique(bcolsSaucy2[m:n+m], return_inverse=True)
    # print bcols
    # print bcols2
    # if (len( (bcolsSaucy-bcolsSaucy2).nonzero()[0] ) > 0 ): exit("wrappers don't agree")
    
    brows = np.array(range(n))

    bdata = np.ones(n,dtype=np.int)
    # Bcc = sp.csr_matrix((bdata,np.vstack((brows,bcols))),dtype=np.int).tocsr()
    Bcc2 = sp.csr_matrix((bdata,np.vstack((brows,bcols2))),dtype=np.int).tocsr()
    # _, rcols = np.unique(bcolsSaucy[n:n+m], return_inverse=True)
    _, rcols2 = np.unique(bcolsSaucy2[0:m], return_inverse=True)

    _, rowfilter2 = np.unique(rcols2, return_index=True)

    LA2 = AC.tocsr()[rowfilter2,:]*Bcc2

    Lc = (co.T * Bcc2).T
    Lb = bo[rowfilter2].todense()
    compresstime = time.clock()-starttime
    LA2 = LA2.tocoo()
    Lc = Lc.todense()

    return LA2, Lb, Lc, compresstime, Bcc2




def sp_saveProblem(fname, A,b,c):
    """
    TODO

    :param fname:
    :type fname:
    :param A:
    :type A:
    :param b:
    :type b:
    :param c:
    :type c:

    :returns:
    """
    
    prob = pic.Problem()
    x = prob.add_variable('x',A.size[1], vtype='continuous')
    prob.add_constraint(A*x < b.T)
    prob.set_objective('min',c.T*x)
    prob.write_to_file(fname,writer='gurobi')

                             
def sparse(A,b,c,debug=False,optiter=200,plot=False, save=False, orbits=False, sumRefine=False, solver='cvxopt', tol=1e-7):
    """
    TODO
    :param A:
    :type A:
    :param b:
    :type b:
    :param c:
    :type c:
    :param optiter:
    :type optiter:
    :param plot:
    :type plot:
    :param save:
    :type save:
    :param orbits:
    :type orbits:
    :param sumRefine:
    :type sumRefine:

    :returns:
    """

    #print "================Original================"
    # print  "objsum: ", np.sum(c.todense())
    solvers.options['abstol'] = tol
    if debug or (save != False):
        mc = -matrix(c.todense())
        # print np.max(A.tocoo().row)
        # exit()
        mA = spmatrix(A.tocoo().data,A.tocoo().row.tolist(),A.tocoo().col.tolist())
        mb = matrix(b.todense())
        # sp_saveProblem("asdf.mps", mA, mb, mc)
        
        probground = pic.Problem()
        x = probground.add_variable('x',mA.size[1], vtype='continuous')
        probground.add_constraint(mA*x < mb.T)
        probground.set_objective('min',mc.T*x)
        # probground.write_to_file(fname,writer='gurobi')


        # if glpk:     
        solinfognd = probground.solve(solver=solver,verbose=True)
        #     sol = solvers.lp(mc, mA, mb, solver="glpk")
        # else: 
        #     sol = solvers.lp(mc, mA, mb)

        xground = x.value
        xground = np.array(xground).ravel()
        timeground = solinfognd['time']  
        objground = solinfognd['obj']  

    LA, Lb, Lc, compresstime, Bcc = lift(A,b,c, sparse = True, orbits=orbits)
    starttime = time.clock()

    problifted = pic.Problem()
    lx =  problifted.add_variable('lx',LA.shape[1], vtype='continuous')
    problifted.add_constraint(spmatrix(LA.data,LA.row.tolist(),LA.col.tolist())*lx < matrix(Lb).T)
    problifted.set_objective('min',-matrix(Lc).T*lx)
    solinfolifted = problifted.solve(solver=solver,verbose=True)
    xopt = lx.value
    # if glpk:
    #     sol = solvers.lp(-matrix(Lc),,matrix(Lb), solver="glpk")
    # else:
    #     sol = solvers.lp(-matrix(Lc),spmatrix(LA.data,LA.row.tolist(),LA.col.tolist()),matrix(Lb))
    r = sp.csr_matrix(np.array(xopt).ravel())
    xopt = np.array((Bcc * r.T).todense()).ravel()
    timelift = solinfolifted['time'] + compresstime  
    objlift = solinfolifted['obj']  
    # timelift = time.clock() - starttime + compresstime
    # objlift = problifted.obj_value() 
    print "lifting cols: ", A.shape[1], " -> ", LA.shape[1]
    print "lifting rows: ", A.shape[0], " -> ", LA.shape[0]
    if debug: 
        report(objlift, objground, xopt, xground, timelift, timeground)
        return [xopt, timeground, timelift, compresstime, Bcc.shape[0], Bcc.shape[1], A.shape[0], LA.shape[0]]
    else:
        print "tlift: ", timelift, "timecomp: ", compresstime 
        return [xopt, timelift, compresstime, Bcc.shape[0], Bcc.shape[1], A.shape[0], LA.shape[0]]
    
def report(objlift, objground, xopt, xground, timelift, timeground):
    """
    TODO

    :param xopt:
    :type xopt:
    :param xground:
    :type xground:
    :param timelift:
    :type timelift:
    :param timeground:
    :type timeground:

    :returns:
    """
    print "================================="
    print "objective values of lifted: ", objlift, ", ground: ", objground, "\n\n"
    if (np.abs(objlift-objground) > 0.0001): exit("ERROR: Objective values of lifted and ground do not agree!")
    print "difference with ground solution: "
    g = np.max(np.abs(xopt - xground))
    i = np.argmax(np.abs(xopt - xground))
    print "abs: ", g, " at xground: ",xground[i], " xlift: ", xopt[i]
    # gg =  np.max(np.abs(xopt/xground))
    # hh =  np.max(np.abs(xground/xopt))
    # if gg>hh:
    #     m = gg
    #     i = np.argmax(np.abs(xopt/xground))
    # else:
    #     m = hh
    #     i = np.argmax(np.abs(xground/xopt))
    # print "rel: ", m, " at xground: ",xground[i], " xlift: ", xopt[i]
    print "ground time: ", timeground, " lifted time: ", timelift
    print "================================="
               
def liftedLPCVXOPT(A,b,c,debug=False,optiter=200,plot=False,save=False, orbits=False, sumRefine=False):
    """
    liftedLPCVXOPT: takes as input an LP in the form

        max   c'x \n
        s.t.  Ax <= b

    where A, b, x are numpy arrays of size (m,n), (m,1), (n,1) respectively and returns a vector solving
    the linear program. 
    By default, the linear program is preprocessed by color-passing, the smaller LP is solved in 
    CVXOPT and then the solution vector is recovered.

    :param A: Numpy Array of size (m,n)
    :type A: double.
    :param b: Numpy Array of size (m,1) - the row vector
    :type b: int.
    :param c: Numpy Array of size (n,1) - the column vector
    :type c: int.
    :param debug: when set to true, an uncompressed version of the LP is solved before solving the lifted one in order to measure time gains and potentially differences between ground and lifted solutions. (Optional - Default = FALSE)
    :type debug: bool.
    :param optiter: limits CVXOPT iterations. (Optional - Default = 200)
    :type optiter: int.
    :param plot: produces matrix plots similar to those in the thesis (see the plot() function definition). (Optional - Default = FALSE)
    :type plot: bool.
    :param save: saves the lifted LP in CVS (see the save() function definition). (Optional - Default = FALSE)
    :type save: bool.
    :param orbits:
    :type orbits:
    :param sumRefine:
    :type sumRefine:

    :returns: The solution vector as tuple : [xopt, (timeground), timelift, compresstime, Bcc.shape[0], Bcc.shape[1], A.shape[0], LA.shape[0]]
    """
    A = np.matrix(A)
    b = np.matrix(b)
    c = np.matrix(c)
    b.shape = (b.size,1)
    c.shape = (c.size,1)
    print "shapes: ", A.shape, b.shape, c.shape
    solvers.options["maxiters"]=optiter
    if debug:    
        starttime = time.clock()
        sol = solvers.lp(-matrix(c),matrix(A),matrix(b))
        xground = np.array(sol["x"]).ravel()
        timeground = time.clock() - starttime
        objground = sol['primal objective']
        # print timeground
        # return
    
    LA, Lb, Lc, compresstime, Bcc = lift(A,b,c, sparse = False, orbits=orbits)
    if save: save(np.array(LA),Lb,Lc)
    if plot:
        plotLP(np.array(A),b,c)
        plotLP(np.array(LA),Lb,Lc)
    
    starttime = time.clock()
    print "lshapes: ", LA.shape, Lb.shape, Lc.shape
    # sol = solvers.lp(-matrix(Lc),spmatrix(LA.data,LA.row.tolist(),LA.col.tolist()),matrix(Lb))
    sol = solvers.lp(-matrix(Lc),matrix(LA.todense()),matrix(Lb))
    r = np.array(sol['x']).ravel()
    xopt = np.array(np.dot(Bcc.todense(),r)).ravel()
    timelift = time.clock() - starttime + compresstime
    objlift = sol['primal objective']
    print "lifting cols: ", A.shape[1], " -> ", LA.shape[1]
    print "lifting rows: ", A.shape[0], " -> ", LA.shape[0]
    if debug: 
        report(objlift, objground, xopt, xground, timelift, timeground)
        return [xopt, timeground, timelift, compresstime, Bcc.shape[0], Bcc.shape[1], A.shape[0], LA.shape[0]]
    else:
        print "tlift: ", timelift, "timecomp: ", compresstime 
        return [xopt, timelift, compresstime, Bcc.shape[0], Bcc.shape[1], A.shape[0], LA.shape[0]]

if __name__ == '__main__':
    N = 3
    times = np.zeros((N,2))
    countz = np.zeros((N,2))
    vars = np.zeros(N,dtype=np.int)    
    A = np.array([[0, 1], [0.2, 1], [0.4, 1], [0.6, 1], [0.8, 1], [1.0, 1], [1.2, 1], [1.4, 1], [1.6, 1], [1.8, 1], [ 2, 1]])    
    zero = np.zeros(A.shape, dtype=np.float)
    b = np.array([1, 1.01, 1.04, 1.09, 1.16, 1.25, 1.36, 1.49, 1.64, 1.81, 2]).transpose()
    c = np.array([1., 1.]).transpose()
    b.shape = (b.size,1)
    c.shape = (c.size,1)
    vec = np.ones((5,), dtype=np.float)

    for j in range(N):
        zero = np.zeros(A.shape, dtype=np.float)
        A = np.hstack((np.vstack((A,zero)),np.vstack((zero,A))))
        b = np.vstack((b,b))
        c = np.vstack((c,c))

    print A
    print sp_liftedLPCVXOPT(sp.coo_matrix(A),sp.coo_matrix(b),sp.coo_matrix(c), debug=True)

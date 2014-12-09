#!/usr/bin/python
## @package liftedLP_glpk
#TODO
#
#

'''
Created on Dec 28, 2010

@author: Martin Mladenov
'''
# import glpk
import glob
import scipy.io
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import *
import matplotlib.cm as cm
from cvxopt import matrix,spmatrix
from cvxopt import solvers
from cvxopt import printing
import time
import sys
from sys import argv
from math import fabs, log, exp
import numpy as np
import scipy as scp
import scipy.sparse as sp
import scipy.linalg as lg
import wrapper
from cvxopt.modeling import variable, op, dot
import picos as pic

# import LiftedLPWrapper

## TODO
#
#
#@param A 
#@param b
#@param c
def save(A,b,c):
    np.savetxt('A.csv', A, delimiter=',')
    np.savetxt('b.csv', b, delimiter=',')
    np.savetxt('c.csv', c, delimiter=',')

## TODO
#
#
#@param N 
#@param b
#@param c
def plotLP(N,b,c):
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    rcParams['backend'] = "ps"
    rcParams['axes.labelsize'] = 20
    rcParams['font.size'] = 20
    rcParams['legend.fontsize'] = 20
    rcParams['legend.numpoints']=1
    rcParams['xtick.labelsize'] = 20
    rcParams['ytick.labelsize'] = 20
    rcParams['lines.linewidth'] = 3
    rcParams['lines.markersize'] = 8   
    # to mirror the plot
    N_m = np.array(N)
    print N.shape
    print N_m.shape
    b_m = b.copy()
    for i in range(N.shape[0]):
        b_m[i] = b[N.shape[0]-i-1]
        for j in range(N.shape[1]):
            N_m[i][j] = N[N.shape[0]-i-1][j]
    print N_m.shape
    axScatter = plt.subplot(111)
    axScatter.pcolor(N_m)#, cmap=plt.get_cmap('Accent'))
    divider = make_axes_locatable(axScatter)
    axHistx = divider.append_axes("top", 1.2, pad=0.1, sharex=axScatter)
    axHisty = divider.append_axes("right", 1.2, pad=0.1, sharey=axScatter)
    plt.setp(axHistx.get_xticklabels() + axHisty.get_yticklabels(),
         visible=False)
    plt.setp(axHistx.get_yticklabels() + axHisty.get_xticklabels(),
         visible=False)
    axHistx.pcolor(np.array(c).T)#, cmap=plt.get_cmap('Accent'))
    axHisty.pcolor(np.array(b_m))#, cmap=plt.get_cmap('Accent'))
    plt.draw()
    plt.show()

## TODO
#
#@param a
def rowUnique(a):
    b = np.ascontiguousarray(a).view(np.dtype((np.void, a.dtype.itemsize * a.shape[1])))
    _, idx = np.unique(b, return_inverse=True)
    return idx

## TODO
#
#@param c
def col2matrix(c):
    brows = np.array(range(len(c)))
    bdata = np.ones(len(c),dtype=np.int)
    Bcc = sp.csr_matrix((bdata,np.vstack((brows,c))),dtype=np.int).tocsr()
    return Bcc

## TODO
#
#@param A 
#@param b
def sumRefinement(A, b):
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


## TODO
#
#
#@param Ar
#@param br
#@param cr
#@param sparse
#@param orbits
#@param sumRefine
def lift(Ar, br, cr, sparse=True, orbits=False, sumRefine=False):
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
    	# print "refinement 1: ", time.clock() - starttime, "seconds."
    	# t1 = time.clock()
    	# print AC.shape
        bcolsSaucy2 = wrapper.epSaucyBipartite(data.astype(np.uintp), AC.row.astype(np.uintp), AC.col.astype(np.uintp), bmod.astype(np.uintp), cmod.astype(np.uintp), np.int32(0), np.int32(o));
        # print "refinement 2: ", time.clock() - t1, "seconds."
        # bcolsSaucy2 = LiftedLPWrapper.equitablePartitionSaucy(T.data.round(6).astype(np.float), T.row.astype(np.int32), T.col.astype(np.int32), cc.astype(np.int32), np.int32(0), np.int32(o));
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
    # print rcols
    # print rcols2
    # _, rowfilter = np.unique(rcols, return_index=True)
    # print rcols2
    _, rowfilter2 = np.unique(rcols2, return_index=True)
    # print rowfilter
    # print rowfilter2
    # LA = A.tocsr()[rowfilter,:]*Bcc
    LA2 = AC.tocsr()[rowfilter2,:]*Bcc2
    # print LB.todense()
    # k = rowfilter.size
    # l = A.shape[0]
    # rfrows = np.array(range(k))
    # Scc = sp.csr_matrix( (np.ones(k,dtype=np.int),np.vstack((rfrows,rowfilter))),
    #                    dtype=np.int, shape=(k,l))
    # LA = Scc*A.tocsr()*Bcc
    Lc = (co.T * Bcc2).T
    Lb = bo[rowfilter2].todense()
    compresstime = time.clock()-starttime
    LA2 = LA2.tocoo()
    Lc = Lc.todense()

    return LA2, Lb, Lc, compresstime, Bcc2




def sp_saveProblem(fname, A,b,c):
    print pic.tools.available_solvers()
    prob = pic.Problem()
    x = prob.add_variable('x',A.size[1], vtype='continuous')
    print A.size
    print x.size
    print b.size
    prob.add_constraint(A*x < b.T)
    prob.set_objective('min',c.T*x)
    print prob
    prob.write_to_file(fname,writer='gurobi')
    prob.solve(solver='gurobi',verbose=True)







<<<<<<< HEAD
                               
def sp_liftedLPCVXOPT(A,b,c,debug=False,optiter=200,plot=False, save=False, orbits=False, sumRefine=False, solver='cvxopt', tol=1e-7):
=======
## TODO
#
#
#@param A
#@param b
#@param c
#@param debug
#@param optiter
#@param plot
#@param save  
#@param orbits
#@param sumRefine                             
def sp_liftedLPCVXOPT(A,b,c,debug=False,optiter=200,plot=False,save=False, orbits=False, sumRefine=False):
>>>>>>> recover
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
<<<<<<< HEAD
    
def report(objlift, objground, xopt, xground, timelift, timeground):
=======
## TODO
#
#
#@param xopt
#@param xground
#@param timelift
#@param timeground    
def report(xopt, xground, timelift, timeground):
>>>>>>> recover
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


## TODO
#
#
#@param A
#@param b
#@param c
#@param debug    
#@param optiter
#@param plot
#@param save  
#@param orbits
#@param sumRefine                
def liftedLPCVXOPT(A,b,c,debug=False,optiter=200,plot=False,save=False, orbits=False, sumRefine=False):
    # liftedLPCVXOPT: takes as input an LP in the form
    #     max   c'x
    #     s.t.  Ax <= b
    # where A, b, x are numpy arrays of size (m,n), (m,1), (n,1) respectively and returns a vector solving
    # the linear program. 
    # By default, the linear program is preprocessed by color-passing, the smaller LP is solved in 
    # CVXOPT and then the solution vector is recovered.
    # One may additionally use the following optional arguments:
    #   debug: when set to true, an uncompressed version of the LP is solved before solving the lifted one
    #          in order to measure time gains and potentially differences between ground and lifted solutions.
    #   optiter: limits CVXOPT iterations.
    #   plot: produces matrix plots similar to those in the thesis (see the plot() function definition).
    #   save: saves the lifted LP in CVS (see the save() function definition).  
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

# colsSaucy = LiftedLPWrapper.equitablePartitionSaucy(np.array([1.,2.,3.,4.], dtype=np.float), np.array([1,2,3,4],dtype=np.int32), np.array([1,2,3,4], dtype=np.int32), np.array([1,2,3,4], dtype=np.int32), np.uint64(0), np.int32(1));
# matr = sp.coo_matrix(scipy.io.mmread("/home/mladenov/workspace/soda/sparsematrices/pltexpa/pltexpa.mtx"))
# matr = sp.coo_matrix(scipy.io.mmread("/home/mladenov/workspace/soda/sparsematrices/ca-AstroPh.mtx"))



# if __name__ == '__main__':

    # files = glob.glob("/home/mladenov/workspace/soda/sparsematrices/grid*.mat")
    # for f in files:
    #     print f
    # 	dictmat = scipy.io.loadmat(f)
    #     print dictmat
    #     #----- uncomment
    #     # for i in [1,2,7]:
    #     # 	print type(dictmat["Problem"][0][0][i])
    #     # 	if type(dictmat["Problem"][0][0][i]) is sp.csc.csc_matrix: break
    #     # print i	
    #     # #print dictmat["Problem"][0][0]	
    #     # #print type(dictmat["Problem"][0][0][i])
    #     # matr = dictmat["Problem"][0][0][i]
    #     #----- uncomment
    #     matr = dictmat["A"]

    #     # exit()
    #     # matr = dictmat["Problem"][0][0][7]
    # 	sym = False
    # 	if matr.shape[0] == matr.shape[1]: 
    #  		matr = matr + matr.T
    #  		sym = True   
    # 	if (sym):
    #  		matr = sp.coo_matrix(sp.triu(matr,k=1))
    #  		size = matr.shape[0]
    #  		off = 0
    #  		a = numpy.asarray([ matr.col, matr.row ])
    # 	else:    
    # 		matr = sp.coo_matrix(matr)
    #  		size = matr.shape[0] + matr.shape[1]
    #  		off = matr.shape[1]
    #  # print np.max(matr.col)
    #  # print np.max(matr.row)
    #  	a = numpy.asarray([ matr.col, matr.row + off ])

    #     # f_handle = file('/home/mladenov/workspace/saucy-3.0/foo.graph', 'w')
    #     # # f_handle.write("%d %d %d\n\n"%(size, matr.col.shape[0], 1))
    #     # # np.savetxt(f_handle, a.T, fmt="%d", delimiter=" ")
    #     # # f_handle.close()
    #     print matr.shape
    #     print matr.col.shape
    #     cols = LiftedLPWrapper.equitablePartitionSaucyUnlabeled(matr.col, matr.row + off, np.zeros(size, dtype=np.int32), np.int32(0), np.int32(1));
    #     print "======"
    #     print "before: ", size
    #     print "after:", np.max(cols)

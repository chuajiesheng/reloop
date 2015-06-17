#!/usr/bin/python
# @package reloop.solvers
# TODO
#
#

'''
Created on Dec 28, 2010

@author: Martin Mladenov
'''
from cvxopt import matrix, spmatrix
from cvxopt import solvers
import time
import numpy as np
import scipy.sparse as sp
import picos as pic
import reloop.utils.saucy as saucy


def rowUnique(a):
    """
    TODO

    :param a:
    :type a:

    :returns:
    """

    b = np.ascontiguousarray(a).view(
        np.dtype(
            (np.void, a.dtype.itemsize * a.shape[1])))
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
    bdata = np.ones(len(c), dtype=np.int)
    Bcc = sp.csr_matrix((bdata, np.vstack((brows, c))), dtype=np.int).tocsr()
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
        czero = rowUnique((A * B).todense())
        ncolsold = ncols
        ncols = np.max(czero) + 1
    return czero

def sp_saveProblem(fname, A, b, c):
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
    x = prob.add_variable('x', A.size[1], vtype='continuous')
    prob.add_constraint(A * x < b.T)
    prob.set_objective('min', c.T * x)
    prob.write_to_file(fname, writer='gurobi')


def sparse(A, b, c=None, G=None, h=None, debug=False, optiter=200, plot=False, save=False, orbits=False,
           sumrefine=False, solver='cvxopt', tol=1e-7, faildiff=1e-2):
    """
    TODO
    :param A:
    :type A:
    :param b:
    :type b:
    :param c:
    :type c:
    :param G:
    :type g:
    :param h:
    :type h:
    :param optiter:
    :type optiter:
    :param plot:
    :type plot:
    :param save:
    :type save:
    :param orbits:
    :type orbits:
    :param sumrefine:
    :type sumrefine:

    :returns:
    """


    solvers.options['abstol'] = tol
    if debug or (save != False):
        mc = -matrix(c.todense())
        mA = spmatrix(
            A.tocoo().data,
            A.tocoo().row.tolist(),
            A.tocoo().col.tolist())
        mb = matrix(b.todense())


        probground = pic.Problem()
        x = probground.add_variable('x', mA.size[1], vtype='continuous')
        probground.add_constraint(mA * x < mb.T)
        probground.set_objective('min', mc.T * x)
        if (G!=None and h!=None):
            mG = spmatrix(
                G.tocoo().data,
                G.tocoo().row.tolist(),
                G.tocoo().col.tolist())
            mh = matrix(h.todense())
            probground.add_constraint(mG * x == mh.T)
            
        # probground.write_to_file(fname,writer='gurobi')

        # if glpk:
        solinfognd = probground.solve(solver=solver, verbose=True)
        #     sol = solvers.lp(mc, mA, mb, solver="glpk")
        # else:
        #     sol = solvers.lp(mc, mA, mb)
        try:
            xground = x.value
        except:
            xground = np.array([0])
        else:
            xground = np.array(xground).ravel()
        timeground = solinfognd['time']
        objground = solinfognd['obj']

    if (G!=None and h!=None):
        LA, Lb, Lc, LG, Lh, compresstime, Bcc = saucy.liftAbc(A, b, c, G=G, h=h, sparse=True, orbits=orbits)
    else:
        LA, Lb, Lc, compresstime, Bcc = saucy.liftAbc(A, b, c, sparse=True, orbits=orbits)

    starttime = time.clock()
    print "Solving lifted LP:"
    print "LA: ", LA.shape, " LG: ", LG.shape
    problifted = pic.Problem()
    lx = problifted.add_variable('lx', LA.shape[1], vtype='continuous')
    problifted.add_constraint(
        spmatrix(LA.data, LA.row.tolist(), LA.col.tolist()) * lx < matrix(Lb).T)
    if (G!=None and h!=None):
        problifted.add_constraint(
            spmatrix(LG.data, LG.row.tolist(), LG.col.tolist()) * lx == matrix(Lh).T)

    problifted.set_objective('min', -matrix(Lc).T * lx)
    solinfolifted = problifted.solve(solver=solver, verbose=True)
    try:
        xopt = lx.value
    except:
        xopt = np.array([0])
    else:
        r = sp.csr_matrix(np.array(xopt).ravel())
        xopt = np.array((Bcc * r.T).todense()).ravel()
    timelift = solinfolifted['time'] + compresstime
    objlift = solinfolifted['obj']
    if debug:
        report(objlift, objground, xopt, xground, timelift, timeground,
                LA.shape[0], A.shape[0], LA.shape[1], A.shape[1],faildiff)
        return [xopt, timeground, timelift, compresstime,
                Bcc.shape[0], Bcc.shape[1], A.shape[0], LA.shape[0]]
    else:
        print "tlift: ", timelift, "timecomp: ", compresstime
        return [xopt, timelift, compresstime, Bcc.shape[
            0], Bcc.shape[1], A.shape[0], LA.shape[0]]


def report(objlift, objground, xopt, xground, timelift,
           timeground, rlift, rground, clift, cground, faildiff):
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
    print "========= LIFTING REPORT ========="
    print "column reduction: ", cground, " -> ", clift
    print "row reduction: ", rground, " -> ", rlift
    print "objective values lifted: ", objlift, " ground: ", objground
    if np.abs(objError(objlift, objground)) > faildiff:
        exit("ERROR: Objective values of lifted and ground do not agree!")
    g = np.max(np.abs(xopt - xground))
    i = np.argmax(np.abs(xopt - xground))
    print "absolute difference: ", g, " at xground_" + str(i), "=", xground[i], "xlift_" + str(i), "=", xopt[i]
    print "ground time: ", timeground, " lifted time: ", timelift
    print "=================================="


def objError(objlift, objground):
    """
    objError : calculates the error of the objective lifted and ground values

    :param objlift: The objective value of lifted
    :type objlift: double.
    :param objground: The objective value of ground
    :type ground: double.

    :returns: The error of lifted and ground value as double.
    """

    # Is there any possible way that either one of the lift and ground values
    # is negative while the other one is positive or vice versa?
    if np.sign(objlift) * np.sign(objground) < 0:
        print "objective signs do not agree!"
        if np.abs(objlift) < 1e-5 and np.abs(objground) < 1e-5:
            return 1e-5
        else:
            return 1
    else:
        objlift = np.abs(objlift)
        objground = np.abs(objground)
        print "objective values disagree by", \
              (max(objlift, objground) / min(objlift, objground) - 1) * 100, "%"
        return max(objlift, objground) / min(objlift, objground) - 1


def liftedLPCVXOPT(A, b, c, debug=False, optiter=200, plot=False,
                   save=False, orbits=False, sumRefine=False):
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
    b.shape = (b.size, 1)
    c.shape = (c.size, 1)
    print "shapes: ", A.shape, b.shape, c.shape
    solvers.options["maxiters"] = optiter
    if debug:
        starttime = time.clock()
        sol = solvers.lp(-matrix(c), matrix(A), matrix(b))
        xground = np.array(sol["x"]).ravel()
        timeground = time.clock() - starttime
        objground = sol['primal objective']
        # print timeground
        # return

    LA, Lb, Lc, compresstime, Bcc = lift(A, b, c, sparse=False, orbits=orbits)
    if save:
        save(np.array(LA), Lb, Lc)
    if plot:
        plotLP(np.array(A), b, c)
        plotLP(np.array(LA), Lb, Lc)

    starttime = time.clock()
    print "lshapes: ", LA.shape, Lb.shape, Lc.shape
    # sol = solvers.lp(-matrix(Lc),spmatrix(LA.data,LA.row.tolist(),LA.col.tolist()),matrix(Lb))
    sol = solvers.lp(-matrix(Lc), matrix(LA.todense()), matrix(Lb))
    r = np.array(sol['x']).ravel()
    xopt = np.array(np.dot(Bcc.todense(), r)).ravel()
    timelift = time.clock() - starttime + compresstime
    objlift = sol['primal objective']
    print "lifting cols: ", A.shape[1], " -> ", LA.shape[1]
    print "lifting rows: ", A.shape[0], " -> ", LA.shape[0]
    if debug:
        report(objlift, objground, xopt, xground, timelift, timeground)
        return [xopt, timeground, timelift, compresstime,
                Bcc.shape[0], Bcc.shape[1], A.shape[0], LA.shape[0]]
    else:
        print "tlift: ", timelift, "timecomp: ", compresstime
        return [xopt, timelift, compresstime, Bcc.shape[0],
                Bcc.shape[1], A.shape[0], LA.shape[0]]

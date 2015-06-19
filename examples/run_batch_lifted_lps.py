## @package symLPExperiments
#Module, which acts as a framework for the actual lifting.
#This module retrieves LPs from specified files and provides the necessary interface to solve given LPs.
#Calculation and Computation is done in the C/C++ core, where most of the work is done. 

import reloop.utils.io.read as lpread
import reloop.solvers.llp as llpsolve
import glob
import pickle
import scipy.sparse as sp
import numpy as np

def loadNsolve(fname, scaled, ftype):
    """
     Loads and solves a given LP by lifting the data and then solving it with the GNU linear programming kit solver.

    :param fname: The name of a given file, which contains the LP
    :type fname: str.
    :param scaled: scaled An integeftype The type of the given problem (mostly LPs)r value, which indicates a scaling/scaled LP (?)
    :type scaled: int.
    :param ftype: ftype The type of the given problem (mostly LPs)
    :type ftype: str.
    :returns:  The n-tuple  [xopt, timeground, timelift, compresstime, shapeR0, shapeR1,shapeC0, shapeC1]:: 

            xopt --
            timeground -- 
            timelift --
            compresstime --
            shapeR0 --
            shapeR1 --
            shapeC0 --
            shapeC1 --

     >>> print loadNsolve('aircraft.gz.mts.lp',0,'LP')
     aircraft.gz.mts.lp :  [4.140719000000001, 0.393192, 0.37750799999999973, 7517, 57, 15025, 105]


    """  
    A = sp.coo_matrix((1,1))
    b = np.zeros((0,0))
    G = None
    h = None
    e = False
    lpread.openLP(fname,np.int32(ftype))

    if scaled == 1: lpread.doScaling(EQUILIB)
    lpmatrix = lpread.getMatrix_Upper(scaled) 
    nelms = np.int(lpmatrix[2,0])
    if nelms > 0:
        [A, b] = lpread.extract_matrix(lpmatrix)
        e = True
    lpmatrix = lpread.getMatrix_Lower(scaled)
    nelms = np.int(lpmatrix[2,0])
    if nelms > 0:
        [AA, bb] = lpread.extract_matrix(lpmatrix)
        if e:
            A = sp.vstack((A,-AA))
            b = np.hstack((b,-bb))
        else:
            A = -AA
            b = -bb
            e = True
    lpmatrix = lpread.getMatrix_Equal(scaled)
    nelms = np.int(lpmatrix[2,0])
    if nelms > 0:
        [G, h] = lpread.extract_matrix(lpmatrix)
    print "after eq: ", A.shape
    b = np.matrix(b)
    b.shape = (b.shape[1],1)
    b = sp.coo_matrix(b)
    if not (h is None):
        h = np.matrix(h)
        h.shape = (h.shape[1],1)
        h = sp.coo_matrix(h)
        print G.shape
        print h.shape
    # done with A
    c = lpread.getObjective(scaled)
    print c
    c.shape = (len(c),1)
    c = sp.coo_matrix(c)
    # glpk2py_wrapper.solve()
    # exit()
    lpread.closeLP()
    # return liftedLPCVXOPT(A.todense(),b.todense(),c.todense(),debug=True,plot=False,orbits=False, sumRefine=False)
    res = llpsolve.sparse(A, b, c, G=G, h=h, debug=True,orbits=False, sumrefine=False, solver='cvxopt')
    try:
        return res
    except: 
	   return ["failed", "failed", "failed", "failed", "failed", "failed", "failed", "failed"]

def runbatch(path, output, type):
    """
    Solves all given LP problems by iteratint over every specified file from the given path.

    :param path: The path, which contains the LPs to solve. 
    :type path: str.
    :param output: The output file
    :type output: str.
    :param type: The type of given problem (Here always type = LP = 1)
    :type type: int.
    """

    scaled = 0;
    resdict = {}
    fnames = glob.glob(path)
    for fname in fnames:
        # try:
        [xopt, timeground, timelift, compresstime, shapeR0, shapeR1,shapeC0, shapeC1] = loadNsolve(fname,scaled, type)
        resdict[fname] = [timeground, timelift, compresstime, shapeR0, shapeR1,shapeC0, shapeC1] 
        # except Exception as e:
        #     error_handle.write("problem in "+fname+" exception "+ str(e))
    output = open(output, 'wb')
    pickle.dump(resdict, output)
    output.close()

    for i in resdict.keys():
        print i, ": ", resdict[i]


if __name__ == '__main__':
    LP = 1
    MTS = 0
    runbatch("../data/*.lp","results.pkl",LP)

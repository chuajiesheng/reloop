## @package symLPExperiments
#Module, which acts as a framework for the actual lifting.
#This module retrieves LPs from specified files and provides the necessary interface to solve given LPs.
#Calculation and Computation is done in the C/C++ core, where most of the work is done. 
import relopt.liftedLP.solvers as llpsolve
import relopt.liftedLP.utils.read as lpread
import glob
import pickle
import scipy.sparse as sp
import numpy as np




## Loads and solves a given LP by lifting the data and then solving it-
#
#@param fname The name of a given file, which contains the LP
#@param scaled An integer value, which indicates a scaling/scaled LP (?)
#@param ftype The type of the given problem (mostly LPs)
def loadNsolve(fname, scaled, ftype):
    A = sp.coo_matrix((1,1))
    b = np.zeros((0,0))
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
        [AA, bb] = lpread.extract_matrix(lpmatrix)
        if e:
            A = sp.vstack((A,-AA))
            b = np.hstack((b,-bb))
        else:
            A = -AA
            b = -bb 
        A = sp.vstack((A,AA))
        b = np.hstack((b,bb))
    print "after eq: ", A.shape
    b = np.matrix(b)
    b.shape = (b.shape[1],1)
    b = sp.coo_matrix(b)
    # done with A
    c = lpread.getObjective(scaled)
    c.shape = (len(c),1)
    c = sp.coo_matrix(c)
    # glpk2py_wrapper.solve()
    # exit()
    lpread.closeLP()
    # return liftedLPCVXOPT(A.todense(),b.todense(),c.todense(),debug=True,plot=False,orbits=False, sumRefine=False)
    return llpsolve.sparse(A,b,c,debug=True,orbits=False, sumRefine=False, solver='gurobi')

## Solves a given LP file by using cvxopt as a method to generate the matrix and glpk to solve it.
#
#@param fname The name of a given file, which contains the LP
#@param scaled An integer value, which indicates a scaling/scaled LP (?)
#@param ftype The type of the given problem (mostly LPs)
def loadNsolveCVX(fname, scaled, ftype):
    print fname
    prob = cvxopt.modeling.op()
    prob.fromfile(fname)
    A = prob.inequalities()
    print A
    prob.solve(format='sparse',solver='glpk')
    exit()
    # glpk2py-wrapper.solve()
    # exit()
    # return liftedLPCVXOPT(A.todense(),b.todense(),c.todense(),debug=True,plot=False,orbits=False, sumRefine=False)
    return sp_liftedLPCVXOPT(A,b,c,debug=True,orbits=False, sumRefine=False)


##
#Iterates over every file specified in the main method.    
#@param path  The path to *.LP files
#@param output A specified file where the output is going to be saved
#@param type The type of given problem (Here always type = LP = 1)
def runbatch(path, output, type):
    error_handle = file('error.log', 'w')


    scaled = 0;
    resdict = {}
    fnames = glob.glob(path)
    for fname in fnames:
        # try:
        [xopt, timeground, timelift, compresstime, shapeR0, shapeR1,shapeC0, shapeC1] = loadNsolve(fname,scaled, type)
        resdict[fname] = [timeground, timelift, compresstime, shapeR0, shapeR1,shapeC0, shapeC1] 
        # except Exception as e:
        #     error_handle.write("problem in "+fname+" exception "+ str(e))
    error_handle.close()
    output = open(output, 'wb')
    pickle.dump(resdict, output)
    output.close()

    for i in resdict.keys():
        print i, ": ", resdict[i]


if __name__ == '__main__':
    LP = 1
    MTS = 0
    runbatch("saucywrapper/data/*.lp","results_ep_Meszaros_counting_ref.pkl",LP)

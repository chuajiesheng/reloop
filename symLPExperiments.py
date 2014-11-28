## @package symLPExperiments
#Documentation for this module.
#This module retrieves LPs from specified files and provides the necessary interface to solve given LPs.
#Calculation and Computation is done in the C/C++ core, where most of the work is done. 

from liftedLP_glpk import *
import glob
import pickle
import cvxopt.modeling
import wrapper
import numpy as np



UPPER = 3
LOWER = 2
EQUAL = 5
UNBOUND = 1
GEOMMEAN = 6
EQUILIB = 7

## Extracts a coordinate matrix from a given n-dimensional array
#Creates a coordinate matrix for the given lpmatrix, by extracting necessary values from the given lpmatrix
#
#@param lpmatrix The four dimensional array with column and row coordinates in the first two rows and data in the third row
#
def extract_matrix(lpmatrix):


    ncols = np.int(lpmatrix[0,0])
    nrows = np.int(lpmatrix[1,0])
    nelms = np.int(lpmatrix[2,0])
    print nelms, ncols, nrows    
    i = np.array(lpmatrix[1,1:(nelms+1)], dtype = np.int) 
    j = np.array(lpmatrix[0,1:(nelms+1)], dtype = np.int) - 1
    d = lpmatrix[2,1:(nelms+1)]
    lb = np.int(lpmatrix[3,0]) + 1
    b = lpmatrix[3,1:lb]
    A = sp.coo_matrix((d, (i,j)), shape=(nrows, ncols))
    return [A, b]

## Loads and solves a given LP by lifting the data and then solving it-
#
#@param fname The name of a given file, which contains the LP
#@param scaled An integer value, which indicates a scaling/scaled LP (?)
#@param ftype The type of the given problem (mostly LPs)
def loadNsolve(fname, scaled, ftype):
    A = sp.coo_matrix((1,1))
    b = np.zeros((0,0))
    e = False
    openLP(fname,np.int32(ftype))

    if scaled == 1: doScaling(EQUILIB)
    lpmatrix = getMatrix_Upper(scaled) 
    nelms = np.int(lpmatrix[2,0])
    print "nelms"
    if nelms > 0:
        print"if statement"
        [A, b] = extract_matrix(lpmatrix)
        e = True
    print "after up: ", A.shape
    lpmatrix = getMatrix_Lower(scaled)
    nelms = np.int(lpmatrix[2,0])
    if nelms > 0:
        [AA, bb] = extract_matrix(lpmatrix)
        if e:
            A = sp.vstack((A,-AA))
            b = np.hstack((b,-bb))
        else:
            A = -AA
            b = -bb
            e = True
    print "after low: ", A.shape
    lpmatrix = getMatrix_Equal(scaled)
    nelms = np.int(lpmatrix[2,0])
    if nelms > 0:
        [AA, bb] = extract_matrix(lpmatrix)
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
    c = getObjective(scaled)
    c.shape = (len(c),1)
    c = sp.coo_matrix(c)
    # glpk2py_wrapper.solve()
    # exit()
    closeLP()
    print A
    # return liftedLPCVXOPT(A.todense(),b.todense(),c.todense(),debug=True,plot=False,orbits=False, sumRefine=False)
    return sp_liftedLPCVXOPT(A,b,c,debug=True,orbits=False, sumRefine=False)

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

##Calls C++ code which opens a linear Program to solve given problem in specified file
#
#@param fname The path of a specified file, which is subject to solving
#@param format A specified format as how to solve the given LP ?
def openLP(fname,ftype):
    wrapper.openLP_Py(fname,ftype)

##Computes the Upper Bounds for a given LP and returns it as a multi-dimensional array
#@param scaled  Flag, which indicates a scaled matrix    
def getMatrix_Upper(scaled):
    return wrapper.getMatrix_Upper(scaled)

##Computes the Lower Bounds for a given LP and returns it as a multi-dimensional array
#
#@param scaled Flag, which indicates a scaled matrix
def getMatrix_Lower(scaled):
    return wrapper.getMatrix_Lower(scaled)

##Computes the Equality constraints of given LP and returns it as a multi-dimensional array
#
#@param scaled Flag, which indicates a scaled matrix 
def getMatrix_Equal(scaled):
    return wrapper.getMatrix_Equal(scaled)

##Computes Unbound variables of given LP
#
#@param scaled Flag, which indicates a scaled matrix 
def getMatrix_Unbound(scaled):
    return wrapper.getMatrix_Unbound(scaled)

##Calls the function getObjective from glpk2py.cpp and returns the objectives as one-dimensional array (see getObjective.cpp)
#
#@param scaled Flag, which indicates a scaled matrix
def getObjective(scaled):
    return wrapper.getObjective_Py(scaled)
def solve():
    wrapper.solve_Py()
def doScaling(sctype):
     wrapper.doScaling_Py(sctype)
def closeLP():
    wrapper.closeLP_Py()

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
        try:
            [xopt, timeground, timelift, compresstime, shapeR0, shapeR1,shapeC0, shapeC1] = loadNsolve(fname,scaled, type)
            resdict[fname] = [timeground, timelift, compresstime, shapeR0, shapeR1,shapeC0, shapeC1] 
        except Exception as e:
            error_handle.write("problem in "+fname+" exception "+ str(e))
    error_handle.close()
    output = open(output, 'wb')
    pickle.dump(resdict, output)
    output.close()

    for i in resdict.keys():
        print i, ": ", resdict[i]


if __name__ == '__main__':
    LP = 1
    MTS = 0
    runbatch("data/*.lp","results_ep_Meszaros_counting_ref.pkl",LP)

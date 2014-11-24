from liftedLP_glpk import *
import glob
import pickle
import cvxopt.modeling
import wrapper as glpk
import numpy as np



UPPER = 3
LOWER = 2
EQUAL = 5
UNBOUND = 1
GEOMMEAN = 6
EQUILIB = 7
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

def loadNsolve(fname, scaled, ftype):
    A = sp.coo_matrix((1,1))
    b = np.zeros((0,0))
    e = False
    glpk.openLP_Py(fname,np.int32(ftype))

    if scaled == 1: glpk.doScaling_Py(EQUILIB)
    lpmatrix = glpk.getMatrix_Py(UPPER, scaled) 
    nelms = np.int(lpmatrix[2,0])
    print "nelms"
    if nelms > 0:
        print"if statement"
        [A, b] = extract_matrix(lpmatrix)
        e = True
    print "after up: ", A.shape
    lpmatrix = glpk.getMatrix_Py(LOWER, scaled)
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
    lpmatrix = glpk.getMatrix_Py(EQUAL, scaled)
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
    c = glpk.getObjective_Py(scaled)
    c.shape = (len(c),1)
    c = sp.coo_matrix(c)
    # glpk2py_wrapper.solve()
    # exit()
    glpk.closeLP_Py()
    print A
    # return liftedLPCVXOPT(A.todense(),b.todense(),c.todense(),debug=True,plot=False,orbits=False, sumRefine=False)
    return sp_liftedLPCVXOPT(A,b,c,debug=True,orbits=False, sumRefine=False)

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
    runbatch("*.lp","results_ep_Meszaros_counting_ref.pkl",LP)

from .. import glpkwrap
UPPER = 3
LOWER = 2
EQUAL = 5
UNBOUND = 1
GEOMMEAN = 6
EQUILIB = 7

def openLP(fname,ftype):
    glpkwrap.openLP_Py(fname,ftype)

##Computes the Upper Bounds for a given LP and returns it as a multi-dimensional array
#@param scaled  Flag, which indicates a scaled matrix    
def getMatrix_Upper(scaled):
    return glpkwrap.getMatrix_Upper(scaled)

##Computes the Lower Bounds for a given LP and returns it as a multi-dimensional array
#
#@param scaled Flag, which indicates a scaled matrix
def getMatrix_Lower(scaled):
    return glpkwrap.getMatrix_Lower(scaled)

##Computes the Equality constraints of given LP and returns it as a multi-dimensional array
#
#@param scaled Flag, which indicates a scaled matrix 
def getMatrix_Equal(scaled):
    return glpkwrap.getMatrix_Equal(scaled)

##Computes Unbound variables of given LP
#
#@param scaled Flag, which indicates a scaled matrix 
def getMatrix_Unbound(scaled):
    return glpkwrap.getMatrix_Unbound(scaled)

##Calls the function getObjective from glpk2py.cpp and returns the objectives as one-dimensional array (see getObjective.cpp)
#
#@param scaled Flag, which indicates a scaled matrix
def getObjective(scaled):
    return glpkwrap.getObjective_Py(scaled)
def solve():
    glpkwrap.solve_Py()
def doScaling(sctype):
     glpkwrap.doScaling_Py(sctype)
def closeLP():
    glpkwrap.closeLP_Py()

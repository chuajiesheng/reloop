from reloop.languages.rlp2.lpsolver import LpSolver
from collections import OrderedDict
import reloop.utils.saucy as saucy
import numpy as np
import scipy.sparse as sp
import sys

#
# LIFTING ANALYSIS
# Methods to calculate the size of the LP before and after lifting.
# Also an alternative method to build and lift the block LP, 

# 
def dense(m):
  """
  Force a matrix to be in dense representation.
  """
  if hasattr(m,"todense"):
    return m.todense()
  else:
    return m


def nonzeroCount(m):
  """
  Count the number of nonzero elements on sparse or dense matrices.
  """
  if hasattr(m,"nnz"):
    return m.nnz
  else:
    return  np.count_nonzero(m)

def mdict(a,b,c,g,h,bcc=np.matrix([])):
  """
  Collect all matrices and vectors of a LP as well as Bcc in a dictionary for convenience.
  """
  return {"a":a,"b":b,"c":c,"g":g,"h":h,"bcc":bcc}


def reportLP(report,matrices):
  """
  Given a file to report to and a LP matrix dictionary created by mdict, report the size
  statistics of the LP.
  """
  s = matrices["g"].shape
  dvars = matrices["c"].shape[0]
  eqcons = matrices["a"].shape[0]
  ineqcons = matrices["g"].shape[0]

  elems = 0
  nonzero = 0

  for k in matrices:
    if k is not "bcc":
      m = matrices[k]
      elems = elems + m.shape[0] * m.shape[1]
      nonzero = nonzero + nonzeroCount(m)
      
  print >> report, "dvars: {0}, eqcons: {1}, ineqcons: {2}, elems: {3}, nonzero: {4}".format(dvars,eqcons,ineqcons,elems,nonzero)

def dumpMatrices(report,matrices):
  """
  Given a file to report to and a LP matrix dictionary created by mdict, dump the
  matrix/vector data of the LP in dense representation.
  """
  for key in matrices:
    print >> report, key
    print >> report, dense(matrices[key])

def lift(ground, sparse = True, orbits = False):
  """
  Given a matrix dictionary return a dictionary with the lifted LP.
  """
  coo_a = sp.coo_matrix(ground["a"])
  coo_b = sp.coo_matrix(ground["b"])
  coo_c = sp.coo_matrix(ground["c"])
  coo_g = sp.coo_matrix(ground["g"])
  coo_h = sp.coo_matrix(ground["h"])
  la, lb, lc, lg, lh, compresstime, bcc = saucy.liftAbc(coo_a,coo_b,coo_c,coo_g,coo_h, sparse, orbits)
  return mdict(la,lb,lc,lg,lh,bcc)


def reportToFile(report,ground,lifted,matrices = False):
  """
  Write full statistics of the LP "ground" and the LP "lifted" to a file.
  Dump matrices only if matrices flag is true.
  """
  print >> report, "BEGIN LP REPORT"
  print >> report, "GROUND"
  print >> report, reportLP(report,ground)
  print >> report, "LIFTED"
  print >> report, reportLP(report,lifted)

  if matrices:
    print >> report, "MATRICES GROUND"
    dumpMatrices(report,ground)
    print >> report, "MATRICES LIFTED"
    dumpMatrices(report,lifted)
  print >> report, "END LP REPORT"


class LiftingAnalysis(LpSolver):
  """
  LPSolver implementation which will not solve, but lift and report lifting statistics to a given file.
  If an instance of LiftingAnalysis is reused between models it will collect the LP generated by each model, so
  that a sequence of LPs can be lifted per subproblem or in block matrix form.
  """
  def __init__(self,report=sys.stdout, sparse = True, orbits = False, dumpSingleMatrices = False, dumpBlockMatrix = False):
    self.report = report
    self.ground    = []
    self.dumpSingleMatrices = dumpSingleMatrices
    self.dumpBlockMatrix = dumpBlockMatrix
    self.sparse = sparse
    self.orbits = orbits
  
  def solve(self, c, g, h, a, b):
    """
    Implementation of LPSolver interface.
    Collects matrices.
    """
    self.ground.append(mdict(a,b,c,g,h))

  def status(self):
    """
    Implementation of LPSolver interface.
    No-Op in this implementation.
    """
    return ()
    
  def liftingAnalysis(self):
    """
    Perform a lifting analysis both on individual subproblems and on block matrix form.
    """
    self.subproblemLiftingAnalysis()
    self.blockLiftingAnalysis()
    
  def subproblemLiftingAnalysis(self):
    """
    Lifting analysis per subproblem.
    """
    print >> self.report, "PER SUBPROBLEM LIFTING"
    for lp in self.ground:
      # lift each ground LP
      lifted = lift(lp, self.sparse, self.orbits)
      # and report.
      reportToFile(self.report,lp,lifted,self.dumpSingleMatrices)

  def blockLiftingAnalysis(self):
    """
    Build, lift and analyze block matrix form of the collected LPs.
    """
      
    # Extract lists of matrices for each LP element from the collected LPs.
    # The coo_matrix calls are needed because vectors are delivered in dense format
    # by the (block) grounder and the stacking below needs a sparse representation.
    am = [ x["a"] for x in self.ground]
    bm = [ sp.coo_matrix(x["b"]) for x in self.ground]
    cm = [ sp.coo_matrix(x["c"]) for x in self.ground]
    gm = [ x["g"] for x in self.ground]
    hm = [ sp.coo_matrix(x["h"]) for x in self.ground]

    # stack it
    block_a = sp.block_diag(am)
    block_b = sp.vstack(bm)
    block_c = sp.vstack(cm)
    block_g = sp.block_diag(gm)
    block_h = sp.vstack(hm)

    # lift it
    ground = mdict(block_a,block_b,block_c,block_g,block_h)
    lifted = lift(ground, self.sparse, self.orbits)

    # say it
    print >> self.report, "BLOCK LP LIFTING"
    reportToFile(self.report,ground,lifted, self.dumpBlockMatrix)

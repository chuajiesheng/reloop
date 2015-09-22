import maxflow_example
from reloop.languages.rlp2.grounding.block import *
from reloop.solvers.lpsolver import CvxoptSolver

'''
Example File for the Problog Knowledge Base
Dependencies :

    Problog
'''

logkb = ProbLogKB("maxflow_prolog.pl")
grounder = BlockGrounder(logkb)

solver = CvxoptSolver()
model = maxflow_example.maxflow(grounder, solver)

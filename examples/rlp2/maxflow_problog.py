
import maxflow_example
from reloop.languages.rlp2.logkb import ProbLogKB
from reloop.languages.rlp2.grounding.block import *
from reloop.solvers.lpsolver import CvxoptSolver
from reloop.languages.rlp2.grounding.recursive import RecursiveGrounder

'''
Example File for the Problog Knowledge Base
Dependencies :

    Problog
'''


logkb = ProbLogKB("maxflow_problog.pl")
grounder = BlockGrounder(logkb)

model = maxflow_example.maxflow(grounder, CvxoptSolver)

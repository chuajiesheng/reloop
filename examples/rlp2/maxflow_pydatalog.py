from reloop.languages.rlp2 import *
import maxflow_example
from reloop.languages.rlp2.grounding.recursive import RecursiveGrounder
from reloop.languages.rlp2.grounding.block import BlockGrounder
from reloop.solvers.lpsolver import CvxoptSolver
from reloop.languages.rlp2.logkb import PyDatalogLogKb
from pyDatalog import pyDatalog

"""
A static example for the maxflow problem contained in maxflow_example.max using pyDatalog
"""

pyDatalog.assert_fact('node', 'a')
pyDatalog.assert_fact('node', 'b')
pyDatalog.assert_fact('node', 'c')
pyDatalog.assert_fact('node', 'd')
pyDatalog.assert_fact('node', 'e')
pyDatalog.assert_fact('node', 'f')
pyDatalog.assert_fact('node', 'g')

pyDatalog.assert_fact('edge', 'a', 'b')
pyDatalog.assert_fact('edge', 'a', 'c')
pyDatalog.assert_fact('edge', 'b', 'd')
pyDatalog.assert_fact('edge', 'b', 'e')
pyDatalog.assert_fact('edge', 'c', 'd')
pyDatalog.assert_fact('edge', 'c', 'f')
pyDatalog.assert_fact('edge', 'd', 'e')
pyDatalog.assert_fact('edge', 'd', 'f')
pyDatalog.assert_fact('edge', 'e', 'g')
pyDatalog.assert_fact('edge', 'f', 'g')

pyDatalog.assert_fact('source','a')
pyDatalog.assert_fact('target', 'g')

pyDatalog.assert_fact('cost', 'a', 'b', 50 )
pyDatalog.assert_fact('cost', 'a', 'c', 100)
pyDatalog.assert_fact('cost', 'b', 'd', 40 )
pyDatalog.assert_fact('cost', 'b', 'e', 20 )
pyDatalog.assert_fact('cost', 'c', 'd', 60 )
pyDatalog.assert_fact('cost', 'c', 'f', 20 )
pyDatalog.assert_fact('cost', 'd', 'e', 50 )
pyDatalog.assert_fact('cost', 'd', 'f', 60 )
pyDatalog.assert_fact('cost', 'e', 'g', 70 )
pyDatalog.assert_fact('cost', 'f', 'g', 70 )


logkb = PyDatalogLogKb()
grounder = BlockGrounder(logkb)


model = maxflow_example.maxflow(grounder, CvxoptSolver)

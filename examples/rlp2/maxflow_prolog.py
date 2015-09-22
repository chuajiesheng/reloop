from pyswip import Prolog
import maxflow_example
from reloop.languages.rlp2.logkb import PrologKB
from reloop.languages.rlp2.grounding.block import *
from reloop.solvers.lpsolver import CvxoptSolver
from reloop.languages.rlp2.grounding.recursive import RecursiveGrounder

'''
Example File for the Prolog Knowledge Base
Dependencies :
    PySwip 0.23 (pip only installs 0.22)
    Ctypes Version > 1.0
    libpl.so in /usr/lib shared library of swi prolog (to install compile prolog from source and set the shared libary flag
'''


prolog = Prolog()


###############################################################################################################
# Directly inserts the predicates into the PrologKB via the prolog object.

nodes = ["a","b","c","d","e","f","g"]
edges = ["a,b","a,c","b,d","b,e","c,d","c,f","d,e","d,f","e,g","f,g"]
costs = ["a,b,'50'","a,c,'100'","b,d,'40'","b,e,'20'","c,d,'60'","c,f,'20'","d,e,'50'","d,f,'60'","e,g,'70'","f,g,'70'"]
source = ["a"]
target = ["g"]
prolog.assertz("source(" + source[0] + ")")
prolog.assertz("target(" + target[0] + ")")
#print list(prolog.query("test(A,B,C,D,E,F,G)"))
for node in nodes:
    prolog.assertz("node(" + node + ")")
for edge in edges:
    insert = "edge(" + edge + ")"
#    print insert
    prolog.assertz(insert)
for cost in costs:
    insert = "cost(" + cost + ")"
#    print insert
    prolog.assertz(insert)


#prolog.consult("maxflow_swipl.pl")
logkb = PrologKB(prolog)
grounder = RecursiveGrounder(logkb)

model = maxflow_example.maxflow(grounder, CvxoptSolver)

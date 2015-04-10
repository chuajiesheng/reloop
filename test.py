
from reloop2 import *
from pyDatalog import pyDatalog

# Relational Program tests start here


@pyDatalog.predicate()
def attribute3(index, axis, value):
    # (x,y) ->z
    yield("1", "1", "2")
    yield("1", "2", "2")
    yield("2", "1", "2")
    yield("2", "2", "1")
    yield("3", "1", "3")
    yield("3", "2", "4")
    yield("4", "1", "4")
    yield("4", "2", "3")
    yield("7", "2", "3")
    yield("7", "2", "5")

# define symbols
x = SubstitutionSymbol('x')
y = SubstitutionSymbol('y')
X = SubstitutionSymbol('X')
A = SubstitutionSymbol('A')


attribute = rlp_function("attribute", 2)
print(attribute)
print(type(attribute))

print(attribute("1", "2"))

simpleSum = RlpSum([X, ], "attribute(X,'1',Y)", attribute(X, 1)*y*y)
print(srepr(simpleSum))
simpleSum.subs(y, 1)

model = RlpProblem("LP-SVM", lp.LpMinimize)
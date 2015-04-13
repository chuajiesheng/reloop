from reloop2 import *

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

attribute = rlp_predicate("attribute", 2)
label = rlp_predicate("label", 1)

slack = rlp_predicate("slack", 1)
weight = rlp_predicate("weight", 1)
b = rlp_predicate("b", 0)
r = rlp_predicate("r", 0)

# print(attribute)
# print(type(attribute))
#
# print(attribute("1", "2"))
#
# simpleSum = RlpSum([X, ], "attribute(X,'1',Y)", attribute(X, 1)*y*y)
# print(srepr(simpleSum))
# simpleSum.subs(y, 1)

model = RlpProblem("LP-SVM", lp.LpMinimize)
model.add_variable(slack)
model.add_variable(weight)
model.add_variable(b)
model.add_variable(r)

print(model.get_variables())
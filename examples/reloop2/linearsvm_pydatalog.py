from reloop.languages.reloop2.logkb import *
from reloop.languages.reloop2.lp import *

@pyDatalog.predicate()
def attribute3(x, y, z):
    yield("1", "x1", 2)
    yield("1", "x2", 2)
    yield("2", "x1", 2)
    yield("2", "x2", 1)
    yield("3", "x1", 3)
    yield("3", "x2", 4)
    yield("4", "x1", 4)
    yield("4", "x2", 3)

@pyDatalog.predicate()
def label2(x, y):
    yield('1', -1)
    yield("2", -1)
    yield("3", 1)
    yield("4", 1)


# Linear Program definition

model = RlpProblem("LP-SVM", LpMinimize, PyDatalogLogKb(), Pulp)
print("\nBuilding a relational variant of the " + model.name)

# const
c = 1.0

# declarations
X, Z, J, I = sub_symbols('X', 'Z', 'J', 'I')

attribute = numeric_predicate("attribute", 2)

slack = numeric_predicate("slack", 1)
weight = numeric_predicate("weight", 1)
b = numeric_predicate("b", 0)
r = numeric_predicate("r", 0)
label = numeric_predicate("label", 1)

model.add_reloop_variable(slack, weight, b, r)

b_attribute = boolean_predicate("attribute", 3)
b_label = boolean_predicate("label", 2)

slacks = RlpSum([I, ], b_label(I, Z), slack(I))
innerProd = RlpSum([J, ], b_attribute(X, J, Z), weight(J) * attribute(I, J))

# objective
model += -r() + c * slacks

# constraints
model += ForAll([I, ], b_label(I, Z), label(I) * (innerProd + b()) + slack(I) >= r())

model += ForAll([I, ], b_attribute(X, I, Z), weight(I) <= 1)
model += ForAll([I, ], b_attribute(X, I, Z), -weight(I) <= 1)
model += r() >= 0
model += ForAll([I, ], b_label(I, Z), slack(I) >= 0)

print("The model has been built.")
print model

model.solve()

print("The model has been solved: " + model.status() + ".")

sol = model.get_solution()
print(sol)

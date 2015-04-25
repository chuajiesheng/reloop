from reloop2 import *
from logkb import *
from lp import *

# Relational Program tests start here


# @pyDatalog.predicate()
# def attribute3(index, axis, value):
#     # (x,y) ->z
#     yield("1", "1", "2")
#     yield("1", "2", "2")
#     yield("2", "1", "2")
#     yield("2", "2", "1")
#     yield("3", "1", "3")
#     yield("3", "2", "4")
#     yield("4", "1", "4")
#     yield("4", "2", "3")
#     yield("7", "2", "3")
#     yield("7", "2", "5")

# # define symbols
# x = SubstitutionSymbol('x')
# y = SubstitutionSymbol('y')
# X = SubstitutionSymbol('X')
# A = SubstitutionSymbol('A')
#
# attribute = rlp_predicate("attribute", 2)
# label = rlp_predicate("label", 1)
#
# slack = rlp_predicate("slack", 1)
# weight = rlp_predicate("weight", 1)
# b = rlp_predicate("b", 0)
# r = rlp_predicate("r", 0)
# booltest = rlp_predicate("booltest", 1, true)
#
# # print(attribute)
# # print(type(attribute))
# #
# # print(attribute("1", "2"))
# #
# # simpleSum = RlpSum([X, ], "attribute(X,'1',Y)", attribute(X, 1)*y*y)
# # print(srepr(simpleSum))
# # simpleSum.subs(y, 1)
#
# model = RlpProblem("LP-SVM", lp.LpMinimize)
# model.add_variable(slack)
# model.add_variable(weight)
# model.add_variable(b)
# model.add_variable(r)
#
# print(model.reloop_variables)
# print(b)
# print(r)
# print(booltest)
#
# z = booltest(x) & booltest(y)
# print(srepr(z))
# z = slack(1) * 4
# print(srepr(z))
# #z = r() * 4
# #print(srepr(z))
#
# model.add_constraint(5 >= slack('1'))

@pyDatalog.predicate()
def node1(X):
    yield('a')
    yield('b')
    yield('c')
    yield('d')
    yield('e')
    yield('f')
    yield('g')


@pyDatalog.predicate()
def edge2(X, Y):
    yield('a', 'b')
    yield('a', 'c')
    yield('b', 'd')
    yield('b', 'e')
    yield('c', 'd')
    yield('c', 'f')
    yield('d', 'e')
    yield('d', 'f')
    yield('e', 'g')
    yield('f', 'g')



@pyDatalog.predicate()
def source1(X):
    yield('a')

@pyDatalog.predicate()
def target1(X):
    yield('g')


@pyDatalog.predicate()
def cost3(X, Y, Z):
    yield('a', 'b', 50) # cost(a,b) = 50
    yield('a', 'c', 100)
    yield('b', 'd', 40)
    yield('b', 'e', 20)
    yield('c', 'd', 60)
    yield('c', 'f', 20)
    yield('d', 'e', 50)
    yield('d', 'f', 60)
    yield('e', 'g', 70)
    yield('f', 'g', 70)



#----------------------------------------------------------
# Linear Program definition

model = RlpProblem("traffic flow LP in the spirit of page 329 in http://ampl.com/BOOK/CHAPTERS/18-network.pdf",
                   LpMaximize, PyDatalogLogKb(), Pulp)

print "\nBuilding a relational variant of the " + model.name

# declarations
X = SubSymbol('X')
Y = SubSymbol('Y')
Z = SubSymbol('Z')

flow = numeric_predicate("flow", 2)
cost = numeric_predicate("cost", 2)

model.add_reloop_variable(flow)

source = boolean_predicate("source", 1)
target = boolean_predicate("target", 1)
edge = boolean_predicate("edge", 2)
node = boolean_predicate("node", 1)

# objective
model += Sum([X, Y], source(X) & edge(X, Y), flow(X, Y))

# constraints for flow preservation
# model += ForAllConstraint([Z, ], node(Z) & ~source(Z) & ~target(Z), inFlow(Z) == outFlow(Z))
outFlow = Sum([X, ], edge(X, Z), flow(X, Z))
inFlow = Sum([Y, ], edge(Z, Y), flow(Z, Y))

model += ForAll([Z, ], node(Z) & ~source(Z) & ~target(Z), Eq(inFlow, outFlow))

# upper and lower bound constraints
model += ForAll([X, Y], edge(X, Y), flow(X, Y) >= 0)
model += ForAll([X, Y], edge(X, Y), flow(X, Y) <= cost(X, Y))


print "The model has been built:"
print(model)
model.solve()

print "\nThe model has been solved: " + model.status() + "."

sol = model.get_solution()

print "The solutions for the flow variables are:\n"
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        print key+" = "+str(value)

total = 0
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        total += value

print "\nThus, the maximum flow entering the traffic network at node a is "+str(sol["flow\\2(Symbol('a'), Symbol('b'))"]+sol["flow\\2(Symbol('a'), Symbol('c'))"])+" cars per hour."
print "\nThe total flow in the traffic network is "+str(total)+" cars per hour."
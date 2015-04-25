from reloop2 import *
from logkb import *
from lp import *

@pyDatalog.predicate()
def node1(x):
    yield('a')
    yield('b')
    yield('c')
    yield('d')
    yield('e')
    yield('f')
    yield('g')

@pyDatalog.predicate()
def edge2(x, y):
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
def source1(x):
    yield('a')

@pyDatalog.predicate()
def target1(x):
    yield('g')

@pyDatalog.predicate()
def cost3(x, y, z):
    # cost(a,b) = 50
    yield('a', 'b', 50)
    yield('a', 'c', 100)
    yield('b', 'd', 40)
    yield('b', 'e', 20)
    yield('c', 'd', 60)
    yield('c', 'f', 20)
    yield('d', 'e', 50)
    yield('d', 'f', 60)
    yield('e', 'g', 70)
    yield('f', 'g', 70)

# Linear Program definition

model = RlpProblem("traffic flow LP in the spirit of page 329 in http://ampl.com/BOOK/CHAPTERS/18-network.pdf",
                   LpMaximize, PyDatalogLogKb(), Pulp)

print "\nBuilding a relational variant of the " + model.name

# declarations
X, Y, Z = sub_symbols('X', 'Y', 'Z')

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
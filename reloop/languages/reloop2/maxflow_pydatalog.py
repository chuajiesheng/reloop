from logkb import *
from lp import *
import time

@pyDatalog.predicate()
def node1(x):
    yield('a')
    yield('b')
    yield('c')
    yield('d')
    yield('e')
    yield('f')
    yield('g')
    yield('b1')
    yield('b2')
    yield('b3')
    yield('b4')
    yield('b5')
    yield('b6')
    yield('b7')
    yield('b8')
    yield('c1')
    yield('c2')
    yield('c3')
    yield('c4')
    yield('c5')
    yield('c6')
    yield('c7')
    yield('c8')


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
    yield('b', 'b1')
    yield('b', 'b2')
    yield('b', 'b3')
    yield('b', 'b4')
    yield('b', 'b5')
    yield('b', 'b6')
    yield('b', 'b7')
    yield('b', 'b8')
    yield('b1', 'd')
    yield('b2', 'd')
    yield('b3', 'd')
    yield('b4', 'd')
    yield('b5', 'd')
    yield('b6', 'd')
    yield('b7', 'd')
    yield('b8', 'd')
    yield('c', 'c1')
    yield('c', 'c2')
    yield('c', 'c3')
    yield('c', 'c4')
    yield('c', 'c5')
    yield('c', 'c6')
    yield('c', 'c7')
    yield('c', 'c8')
    yield('c1', 'f')
    yield('c2', 'f')
    yield('c3', 'f')
    yield('c4', 'f')
    yield('c5', 'f')
    yield('c6', 'f')
    yield('c7', 'f')
    yield('c8', 'f')

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
    yield('b', 'b1', 5)
    yield('b', 'b2', 5)
    yield('b', 'b3', 5)
    yield('b', 'b4', 5)
    yield('b', 'b5', 5)
    yield('b', 'b6', 5)
    yield('b', 'b7', 5)
    yield('b', 'b8', 5)
    yield('b1', 'd', 1)
    yield('b2', 'd', 1)
    yield('b3', 'd', 1)
    yield('b4', 'd', 1)
    yield('b5', 'd', 1)
    yield('b6', 'd', 1)
    yield('b7', 'd', 1)
    yield('b8', 'd', 1)
    yield('c', 'c1', 5)
    yield('c', 'c2', 5)
    yield('c', 'c3', 5)
    yield('c', 'c4', 5)
    yield('c', 'c5', 5)
    yield('c', 'c6', 5)
    yield('c', 'c7', 5)
    yield('c', 'c8', 5)
    yield('c1', 'f', 1)
    yield('c2', 'f', 1)
    yield('c3', 'f', 1)
    yield('c4', 'f', 1)
    yield('c5', 'f', 1)
    yield('c6', 'f', 1)
    yield('c7', 'f', 1)
    yield('c8', 'f', 1)

# Linear Program definition
start = time.time()
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
model += RlpSum([X, Y], source(X) & edge(X, Y), flow(X, Y))

# constraints for flow preservation
outFlow = RlpSum([X, ], edge(X, Z), flow(X, Z))
inFlow = RlpSum([Y, ], edge(Z, Y), flow(Z, Y))

model += ForAll([Z, ], node(Z) & ~source(Z) & ~target(Z), inFlow |eq| outFlow)

# upper and lower bound constraints
model += ForAll([X, Y], edge(X, Y), flow(X, Y) |ge| 0)
model += ForAll([X, Y], edge(X, Y), flow(X, Y) |le| cost(X, Y))

print "The model has been built:"
print(model)

model.solve()

print "\nThe model has been solved: " + model.status() + "."

sol = model.get_solution()

end = time.time()

print "The solutions for the flow variables are:\n"
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        print key+" = "+str(value)

total = 0
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        total += value

print "\n Time needed for the grounding and solving: " + str(end - start) + " s."
print "\nThus, the maximum flow entering the traffic network at node a is "+str(sol["flow(a, b)"]+sol["flow(a, c)"])+" cars per hour."
print "\nThe total flow in the traffic network is "+str(total)+" cars per hour."



from logkb import *
from lp import *
import time

def maxflow(logKb, solver, predicate_prefix=""):
    start = time.time()
    model = RlpProblem("traffic flow LP in the spirit of page 329 in http://ampl.com/BOOK/CHAPTERS/18-network.pdf",
                       LpMaximize, logKb, solver)

    print "\nBuilding a relational variant of the " + model.name

    # declarations
    X, Y, Z = sub_symbols('X', 'Y', 'Z')

    flow = numeric_predicate(predicate_prefix + "flow", 2)
    cost = numeric_predicate(predicate_prefix + "cost", 2)

    model.add_reloop_variable(flow)

    source = boolean_predicate(predicate_prefix + "source", 1)
    target = boolean_predicate(predicate_prefix + "target", 1)
    edge = boolean_predicate(predicate_prefix + "edge", 2)
    node = boolean_predicate(predicate_prefix + "node", 1)

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

    end = time.time()

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

    print "\nTime needed for the grounding and solving: " + str(end - start) + " s."
    print "\nThus, the maximum flow entering the traffic network at node a is "+str(sol["flow(a, b)"]+sol["flow(a, c)"])+" cars per hour."
    print "\nThe total flow in the traffic network is "+str(total)+" cars per hour."
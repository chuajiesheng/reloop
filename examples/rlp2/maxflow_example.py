from reloop.languages.rlp2 import *
import time
import logging
import sys

def maxflow(grounder, solver):
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    start = time.time()
    model = RlpProblem("traffic flow LP in the spirit of page 329 in http://ampl.com/BOOK/CHAPTERS/18-network.pdf",
                       LpMaximize, grounder, solver)

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
    model += RlpSum([Y], edge('a', Y), flow('a', Y) )

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

    print "\nThe model has been solved: " + str(model.status()) + "."

    sol = model.get_solution()

    print "The solutions for the flow variables are:\n"

    total = 0
    for (predicate_class, args), value in sol.iteritems():
            print(str(predicate_class)+str(args) + " = " + str(value))
            total += value

    try:
        inflow = sol[(flow, (Symbol('a'), Symbol('b')))] + sol[(flow, (Symbol('a'), Symbol('c')))]
    except KeyError:
        inflow = sol[(flow,('a','b'))] + sol[(flow,('a', 'c'))]

    print "\nTime needed for the grounding and solving: " + str(end - start) + " s."
    #TODO: Change output to display correct results for an arbitrary number of edges outgoing from the source
    print "\nThus, the maximum flow entering the traffic network at node a is "+ str(inflow) +" cars per hour."
    print "\nThe total flow in the traffic network is "+str(total)+" cars per hour."
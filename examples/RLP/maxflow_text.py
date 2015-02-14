__author__ = 'kersting'

from reloop.languages.rlp import *

#----------------------------------------------------------
# Reloop Model

#----------------------------------------------------------
# The datalog part

#pyDatalog.create_terms('constraint,Value')

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
def edge2(X,Y):
    yield('a','b')
    yield('a','c')
    yield('b','d')
    yield('b','e')
    yield('c','d')
    yield('c','f')
    yield('d','e')
    yield('d','f')
    yield('e','g')
    yield('f','g')



@pyDatalog.predicate()
def source1(X):
    yield('a')

@pyDatalog.predicate()
def target1(X):
    yield('g')


@pyDatalog.predicate()
def cap3(X,Y,Z):
    yield('a','b',50)
    yield('a','c',100)
    yield('b','d',40)
    yield('b','e',20)
    yield('c','d',60)
    yield('c','f',20)
    yield('d','e',50)
    yield('d','f',60)
    yield('e','g',70)
    yield('f','g',70)


#----------------------------------------------------------
# the LP part

model = reloopProblem("flow LP", lp.LpMaximize)

print "\nBuilding a relational variant of the " + model.name
#declarations
model.predicate("flow", 2, var = True)
model.predicate("cap", 2)
model.predicate("inFlow", 1, var = True)
model.predicate("outFlow", 1, var = True)
# the objective function is added to relational LP first
model += reloopConstraint("sum{ X,Y in source(X) & edge(X,Y) } : { flow(X,Y) }")
# constraints defining inflow are added
input = "forall{ Y in node(Y) & ~source(Y) } : { sum{ X in edge(X,Y) } : { flow(X,Y)} = inFlow(Y) }"
model += reloopConstraint(input)
# constraints defining outflow are added
input = "forall{ X in node(X) & ~target(X) } : { sum{ Y in edge(X,Y) } : { flow(X,Y) }  = outFlow(X) }"
model += reloopConstraint(input)

# constraints defining preservation of flow are added
input = "forall{ X in node(X) & ~source(X) & ~target(X)} : { inFlow(X) = outFlow(X) }"
model += reloopConstraint(input)


# constraints defining lower and upper bounds are added
input = "forall{ X,Y in edge(X,Y) } : { flow(X,Y) >= 0}"
model += reloopConstraint(input)

input = "forall{ X,Y in edge(X,Y) } : { flow(X,Y)  <= cap(X,Y)}"
model += reloopConstraint(input)

print "The model has been build."

#print model

model.solve()

print "The model has been solved: " + model.status()

sol =  model.getSolution()

print "The solutions for the flow variables are:\n"
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        print key+" = "+str(value)

total = 0
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        total += value

print "\nThus, the maximum flow entering the traffic network at node a is "+str(sol["flow(a,b)"]+sol["flow(a,c)"])+" cars per hour."
print "\nThe total flow in the traffic network is "+str(total)+" cars per hour."

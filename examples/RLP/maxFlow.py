__author__ = 'kersting'

from reloop import *

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
def cost3(X,Y,Z):
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

model = reloopProblem("traffic flow LP in the spirit of page 329 in http://ampl.com/BOOK/CHAPTERS/18-network.pdf", lp.LpMaximize)

print "\nBuilding a relational variant of the " + model.name

# the objective function is added to relational LP first

# model += reloopVariable("flow/2")
# constraints defining inflow are added
input = "forall{ Y in node(Y) & ~source(Y) } : { sum{ X in edge(X,Y) } : { 1.0*flow(X,Y)} - 1.0*inFlow(Y) = 0}"
c = reloopConstraint(input)
model += c
c = reloopConstraint("sum{ X,Y in source(X) & edge(X,Y) } : { cost[X,Y]*flow(X,Y) }")
model += c
# constraints defining outflow are added
input = "forall{ X in node(X) & ~target(X) } : { sum{ Y in edge(X,Y) } : { 1.0*flow(X,Y) } - 1.0*outFlow(X) = 0}"
c = reloopConstraint(input)
model += c

# constraints defining preservation of flow are added
input = "forall{ X in node(X) & ~source(X) & ~target(X)} : { 1.0*inFlow(X) - 1.0*outFlow(X) = 0}"
c = reloopConstraint(input)
model += c


# constraints defining lower and upper bounds are added
input = "forall{ X,Y in edge(X,Y) } : { 1.0*flow(X,Y) >= 0}"
c = reloopConstraint(input)
model += c

input = "forall{ X,Y in edge(X,Y) } : { 1.0*flow(X,Y) - 1*cost[X,Y] <= 0}"
c = reloopConstraint(input)
model += c


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

print "\nThus, the maximum flow entering the traffic network at node a is "+str(sol["flow('a','b')"]+sol["flow('a','c')"])+" cars per hour."
print "\nThe total flow in the traffic network is "+str(total)+" cars per hour."
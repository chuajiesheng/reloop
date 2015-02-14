from reloop.languages.rlp import *

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
    yield('a','b',50) # cap(a,b) = 50
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
# Linear Program definition

model = reloopProblem("flow LP", lp.LpMaximize)

print "\nBuilding a relational variant of the " + model.name

#declarations
flow = model.predicate("flow", 2, var=True)
cap = model.predicate("cap", 2)
outFlow = model.predicate("outFlow",1,var = True)
inFlow = Substitution("inFlow", 1)
outFlow = Substitution("outFlow", 1)

#definitions for substitutions
outFlow <<= [ "X", psum("Y in edge(X,Y)", flow("X","Y")) ]
inFlow  <<= [ "Y", psum("X in edge(X,Y)", flow('X','Y')) ]

#objective
model += pobj(psum("X,Y in source(X) & edge(X,Y)", flow("X","Y"))) 
#constraints for flow preservation
model += pall("Z in node(Z) & ~source(Z) & ~target(Z)", inFlow("Z") == outFlow("Z"))
#upper and lower bound constraints
model += pall("X,Y in edge(X,Y)", flow("X","Y") <= cap("X","Y") )
model += pall("X,Y in edge(X,Y)", flow("X","Y") >= 0)

print "The model has been built."
model.solve()


print "The model has been solved: " + model.status() + "."

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

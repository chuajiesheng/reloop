__author__ = 'kersting'

from reloop import *

#----------------------------------------------------------
# Reloop Model

#----------------------------------------------------------
# The datalog part


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
    yield('b','c')
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
    yield('a','c',10)
    yield('b','c',20)
    yield('b','d',40)
    yield('b','e',20)
    yield('c','d',10)
    yield('c','f',70)
    yield('d','e',50)
    yield('d','f',60)
    yield('e','g',60)
    yield('f','g',50)

# time equals the degree of a node times the costs
pyDatalog.load("""
(degree[X]==len_(Y)) <= edge(X,Y)
time(X,Y,Z) <= cost(X,Y,C) & (C*degree[X]==Z)
""")


#pyDatalog.create_terms('constraint,Value,edge')

pyDatalog.load("""
road(X,Y) <= edge(X,Y) & ~source(X)
road(X,Y) <= edge(X,Y) & ~source(Y)
""")



#----------------------------------------------------------
# the LP part

model = reloopProblem("shortest path LP in the spirit of page 331 in http://ampl.com/BOOK/CHAPTERS/18-network.pdf", lp.LpMinimize)

print "\nBuilding a relational variant of the " + model.name

# the objective function is added to relational LP first
input = "sum{ X,Y in road(X,Y)} : { time[X,Y]*use(X,Y) }"
o = reloopConstraint(input)
model += o

# constraints defining inflow are added
input = "forall{ Y in node(Y) & ~source(Y) } : { sum{ X in road(X,Y) } : { 1.0*use(X,Y) } - 1.0*inUse(Y) = 0}"
c = reloopConstraint(input)
model += c


# constraints defining outflow are added
input = "forall{ X in node(X) & ~target(X) } : { sum{ Y in road(X,Y) } : { 1.0*use(X,Y) } - 1.0*outUse(X) = 0}"
c = reloopConstraint(input)
model += c

# constraints defining preservation of flow are added
input = "forall{ X in node(X) & ~source(X) & ~target(X)} : { 1.0*inUse(X) - 1.0*outUse(X) = 0}"
c = reloopConstraint(input)
model += c


#constraints defining lower and upper bounds are added
input = "forall{ X,Y in road(X,Y) } : { 1.0*use(X,Y) >= 0}"
c = reloopConstraint(input)
model += c

input = "sum{ X,Y in source(X) & road(X,Y) } : {1.0*use(X,Y)} = 1"
c = reloopConstraint(input)
model += c


print "The model has been build."

#print model

model.solve()

if model.status():
    print "The model has been solved optimally."

    sol =  model.getSolution()


    print "The shortest path is:\n"
    totalCosts = 0
    for key, value in sol.iteritems():
        if "use" in key and value > 0:
            print key.replace("use","road")
            query = key.replace("use","time").replace('(','[').replace(')',']')
            query = "".join(o if not o in ["'"] else "" for o in query )
            cost = getpyDatalogFunctionValue(query)
            totalCosts += cost


    print "\nThe costs of the shortest path are "+str(totalCosts)+"."

else:
    print "The model has not been solved optimally!"
from reloop.languages.reloop2.logkb import *
from reloop.languages.reloop2.lp import *
import maxflow_example

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

model = maxflow_example.maxflow(PyDatalogLogKb(), Pulp)

from reloop.languages.rlp import *
from reloop.languages.rlp.grounding.block import BlockGrounder
from reloop.languages.rlp.logkb import PyDatalogLogKb
from reloop.solvers.lpsolver import CvxoptSolver


for u in range(1, 10):
    pyDatalog.assert_fact('num', u)

for u in range(1, 4):
    pyDatalog.assert_fact('boxind', u)

pyDatalog.assert_fact('initial', 1, 1, 5)
pyDatalog.assert_fact('initial', 2, 1, 6)
pyDatalog.assert_fact('initial', 4, 1, 8)
pyDatalog.assert_fact('initial', 5, 1, 4)
pyDatalog.assert_fact('initial', 6, 1, 7)
pyDatalog.assert_fact('initial', 1, 2, 3)
pyDatalog.assert_fact('initial', 3, 2, 9)
pyDatalog.assert_fact('initial', 7, 2, 6)
pyDatalog.assert_fact('initial', 3, 3, 8)
pyDatalog.assert_fact('initial', 2, 4, 1)
pyDatalog.assert_fact('initial', 5, 4, 8)
pyDatalog.assert_fact('initial', 8, 4, 4)
pyDatalog.assert_fact('initial', 1, 5, 7)
pyDatalog.assert_fact('initial', 2, 5, 9)
pyDatalog.assert_fact('initial', 4, 5, 6)
pyDatalog.assert_fact('initial', 6, 5, 2)
pyDatalog.assert_fact('initial', 8, 5, 1)
pyDatalog.assert_fact('initial', 9, 5, 8)
pyDatalog.assert_fact('initial', 2, 6, 5)
pyDatalog.assert_fact('initial', 5, 6, 3)
pyDatalog.assert_fact('initial', 8, 6, 9)
pyDatalog.assert_fact('initial', 7, 7, 2)
pyDatalog.assert_fact('initial', 3, 8, 6)
pyDatalog.assert_fact('initial', 7, 8, 8)
pyDatalog.assert_fact('initial', 9, 8, 7)
pyDatalog.assert_fact('initial', 4, 9, 3)
pyDatalog.assert_fact('initial', 5, 9, 1)
pyDatalog.assert_fact('initial', 6, 9, 6)
pyDatalog.assert_fact('initial', 8, 9, 5)

pyDatalog.load("""
    box(I, J, U, V) <= boxind(U) & boxind(V) & num(I) & num(J) & (I > (U-1)*3) & (I <= U*3) & (J > (V-1)*3) & (J <= V*3)
""")

logkb = PyDatalogLogKb()
grounder = BlockGrounder(logkb)
# Note: CVXOPT needs to be compiled with glpk support. See the CVXOPT documentation.
solver = CvxoptSolver(solver_solver='glpk')

model = RlpProblem("play sudoku for fun and profit",
                   LpMaximize, grounder, solver)

I, J, X, U, V = sub_symbols('I', 'J', 'X', 'U', 'V')
"""
We have an n x n array of cells. The indices 1 to n are defined with num(1), ..., num(n).
The predicate fill(I,J,X) indicates the assignment of cell I,J with number X.
"""

num = boolean_predicate("num", 1)
boxind = boolean_predicate("boxind", 1)
box = boolean_predicate("box", 4)
initial = boolean_predicate("initial", 3)
fill = numeric_predicate("fill", 3)


model.add_reloop_variable(fill)

# each cell receives exactly one number
model += ForAll([I, J], num(I) & num(J), RlpSum([X, ], num(X), fill(I, J, X)) >= 1)
model += ForAll([I, J], num(I) & num(J), RlpSum([X, ], num(X), fill(I, J, X)) <= 1)

# each number is encountered exactly once per row
model += ForAll([I, X], num(I) & num(X), RlpSum([J, ], num(J), fill(I, J, X)) >= 1)
model += ForAll([I, X], num(I) & num(X), RlpSum([J, ], num(J), fill(I, J, X)) <= 1)

# each number is encountered exactly once per column
model += ForAll([J, X], num(J) & num(X), RlpSum([I, ], num(I), fill(I, J, X)) >= 1)
model += ForAll([J, X], num(J) & num(X), RlpSum([I, ], num(I), fill(I, J, X)) <= 1)

# each number is encountered exactly once per box
model += ForAll([X, U, V], num(X) & boxind(U) & boxind(V), RlpSum([I, J], box(I, J, U, V), fill(I, J, X)) >= 1)
model += ForAll([X, U, V], num(X) & boxind(U) & boxind(V), RlpSum([I, J], box(I, J, U, V), fill(I, J, X)) <= 1)

# nonnegativity
model += ForAll([I, J, X], num(X) & num(I) & num(J), fill(I, J, X) >= 0)

# initial assignment
model += ForAll([I, J, X], initial(I, J, X), fill(I, J, X) <= 1)

# objective
model += RlpSum([X, ], num(X), fill(1, 1, X))

model.solve()

sol = model.get_solution()
print "The solutions for the fill variables are:\n"
for key, value in sol.iteritems():
	if round(value, 2) >= 0.99:
		print key, "=", round(value, 2)
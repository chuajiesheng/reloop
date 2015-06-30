from distutils.command.config import config
import pulp
import numpy
from rlp import *
import logging

log = logging.getLogger(__name__)

# constants
LpMinimize = 1
LpMaximize = -1

# from reloop.solvers.llp import *

class LpProblem():
    """
    Representation of a linear program. Intended to be inherited by multiple LP solver implementations.
    """
    def __init__(self, name, sense):
        self.name = name
        self.sense = sense
        self._lp_variables = {}

    def solve(self):
        """
        Solves the lp
        """
        raise NotImplementedError()

    def status(self):
        """
        :return: The solution status of the LP.
        """
        raise NotImplementedError()

    def __iadd__(self, other):
        """
        Adds a constraint or objective to the lp.

        :param other: Constraint: Tuple of (lhs, b, sense), where lhs is an expression, b an atom (like an integer)
        and sense either -1, 0 or 1; Objective: An object of type :class:`sympy.core.Expr`
        :return: self
        """
        if isinstance(other, tuple):
            self.add_constraint(other)
        elif isinstance(other, Expr):
            self.add_objective(other)
        else:
            raise ValueError("Tuple (Objective) or Expr (Constraint) was expected.")

        return self

    def add_constraint(self, constraint_tuple):
        """
        To be implemented by the actual solver.

        :param constraint_tuple: Constraint: Tuple of (lhs, b, sense), where lhs is an expression, b an atom (like an integer)
        and sense either -1, 0 or 1
        """
        raise NotImplementedError()

    def add_objective(self, expr):
        """
        To be implemented by the actual solver.

        :param expr: An object of type :class:`sympy.core.Expr`
        """
        raise NotImplementedError()

    def lp_variable(self, name):
        """
        Creates some kind of lp variable, to be implemented by the solver.

        :param name: name of a lp variable
        :return: Some kind of lp variable
        """
        raise NotImplementedError()

    @property
    def lp_variables(self):
        return self._lp_variables

    def add_lp_variable(self, name):
        if name in self._lp_variables:
            return self._lp_variables[name]
        else:
            self._lp_variables[name] = self.lp_variable(name)
        return self._lp_variables[name]

    def get_affine(self, expr):
        pred_names, factors = get_predicate_names(expr)

        length = len(pred_names)
        factor_vector = numpy.zeros(length)

        contained_lp_variables = []
        used_lp_variables = []

        for j in range(length):
            lp_variable = self.add_lp_variable(pred_names[j])

            if pred_names[j] in used_lp_variables:
                factor_vector[used_lp_variables.index(pred_names[j])] += factors[j]
            else:
                contained_lp_variables.append(lp_variable)
                used_lp_variables.append(pred_names[j])
                factor_vector[used_lp_variables.index(pred_names[j])] = factors[used_lp_variables.index(pred_names[j])]

        return [(contained_lp_variables[i], factor_vector[i]) for i in range(len(contained_lp_variables))]

class Pulp(LpProblem):
    """
    LPProblem implementation which uses the LP Solver provided by Pulp
    """
    def __init__(self, name, sense):
        LpProblem.__init__(self, name, sense)
        self.lpmodel = pulp.LpProblem(name, sense)

    def lp_variable(self, name):
        return pulp.LpVariable(name)

    def solve(self):
        self.lpmodel.solve()

    def status(self):
        return pulp.LpStatus[self.lpmodel.status]

    def add_constraint(self, constraint_tuple):
        lhs, b, sense = constraint_tuple
        c = self.get_affine_expression(lhs)
        self.lpmodel += pulp.LpConstraint(c, sense, None, b)

    def add_objective(self, expr):
        self.lpmodel += self.get_affine_expression(expr)

    def get_affine_expression(self, expr):
        variable_factors = self.get_affine(expr)
        c = pulp.LpAffineExpression(variable_factors)
        return c

    def get_solution(self):
        return {x: self.lp_variables[x].value() for x in self.lp_variables}

class LiftedLinear(LpProblem):
    def __init__(self, name, sense):
        LpProblem.__init__(self, name, sense)
        self._index = 0
        self._objective = ()
        self._constraints = {}
        self._constraints[-1] = []
        self._constraints[1] = []
        self._constraints[0] = []
        self._result = None
        # more here

    def solve(self):
        # import reloop.solvers.llp as solver
        raise NotImplementedError("Lifted Linear solving is still not implemented!")

        ineq_constraint_count = len(self._constraints[1]) + len(self._constraints[-1])
        eq_constraint_count = len(self._constraints[0])

        typet = numpy.double
        a = numpy.zeros((eq_constraint_count, self._index), dtype=typet)
        b = numpy.zeros((eq_constraint_count, 1), dtype=typet)

        g = numpy.zeros((ineq_constraint_count, self._index), dtype=typet)
        h = numpy.zeros((ineq_constraint_count, 1), dtype=typet)

        c = numpy.zeros((self._index, 1), dtype=typet)

        i = 0
        for constraint in self._constraints[0]:
            for variable, factor in constraint[0]:
                a[i][variable[0]] = factor
            b[i] = constraint[1]
            i += 1

        i = 0
        for constraint in self._constraints[-1]:
            for variable, factor in constraint[0]:
                g[i][variable[0]] = factor
            h[i] = constraint[1]
            i += 1

        for constraint in self._constraints[1]:
            for variable, factor in constraint[0]:
                g[i][variable[0]] = -factor
            h[i] = -constraint[1]
            i += 1

        for variable in self._objective:
            c[variable[0][0]] = variable[1]


        #a = sp.coo_matrix(numpy.matrix(a))
        #b = sp.coo_matrix(numpy.matrix(b))
        #c = sp.coo_matrix(numpy.matrix(c))

        # self._result = sparse(a, b, c)

        c = self.sense * c

        print(a)
        print(b)
        print(g)
        print(h)

        solvers.options['abstol'] = 0
        #solvers.options['reltol'] = 0
        solvers.options['feastol'] = 1e-7
        solvers.options['maxiters'] = 350

        primalst = {}
        primalst['x'] = matrix(numpy.array([40.0, 70.0, 60.0, 30.0, 20.0, 60.0, 20.0, 50.0, 50.0, 80.0]))
        see = numpy.ones((20, 1))
        print(see)
        primalst['s'] = matrix(1e-100*see)
        self._result = solvers.conelp(c = matrix(c), G =  matrix(g), h = matrix(h), A = matrix(a), b = matrix(b), primalstart=primalst)
        i = 0
        for variable in self._lp_variables:
            var_index = self._lp_variables[variable][0]
            var_opt_sol = self._result['x'][var_index]
            self._lp_variables[variable] = (var_index, var_opt_sol)
            i += 1

    def status(self):
        return "Not Available for LiftedLinearSolver"

    def lp_variable(self, name):
        curr_index = self._index
        self._index += 1
        return curr_index, "undefined"

    def add_constraint(self, constraint_tuple):
        lhs, b, sense = constraint_tuple
        variable_factors = self.get_affine(lhs)
        self._constraints[sense].append((variable_factors, b))

    def add_objective(self, expr):
        self._objective = self.get_affine(expr)

    def get_solution(self):
        return {name: self.lp_variables[name][1] for name in self.lp_variables}


def get_predicate_names(expr):
    pred_names = []
    factors = []

    if expr.func is Add:
        for s in expr.args:
            p, f = get_predicate_names(s)
            pred_names += p
            factors += f

    elif expr.func is Mul:
        if expr.args[0].is_Atom:
            if isinstance(expr.args[1], RlpPredicate):
                value = expr.args[0]
                pred = expr.args[1]
            else:
                raise NotImplementedError()

        elif isinstance(expr.args[0], RlpPredicate):
            if expr.args[1].is_Atom:
                value = expr.args[1]
                pred = expr.args[0]
            elif isinstance(expr.args[1], RlpPredicate):
                raise ValueError("Found non-linear constraint!")
            else:
                raise NotImplementedError()

        else:
            raise NotImplementedError()

        return [sstr(pred), ], [float(value), ]

    elif isinstance(expr, RlpPredicate):
        return [sstr(expr), ], [float(1), ]

    elif expr.func is Pow:
        raise ValueError("Found non-linear constraint!")
    elif isinstance(expr, Number):
        return pred_names, factors 
    else:
        raise NotImplementedError("Cannot get predicates for: " + str(expr) + str(expr.func))

    return pred_names, factors
from distutils.command.config import config
import pulp
import numpy
from reloop2 import *

# constants
LpMinimize = 1
LpMaximize = -1


class LpProblem():

    def __init__(self, name, sense):
        self.name = name
        self.sense = sense
        self._lp_variables = {}

    def solve(self):
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()

    def __iadd__(self, other):
        if isinstance(other, tuple):
            self.add_constraint(other)
        elif isinstance(other, Expr):
            self.add_objective(other)
        else:
            raise ValueError("Tuple (Objective) or Expr was expected.")

        return self

    def add_constraint(self, constraint_tuple):
        raise NotImplementedError()

    def add_objective(self, expr):
        raise NotImplementedError()

    def lp_variable(self, name):
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


class Pulp(LpProblem):
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
        c = self.get_affine(lhs)
        self.lpmodel += pulp.LpConstraint(c, sense, None, b)

    def add_objective(self, expr):
        self.lpmodel += self.get_affine(expr)

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

        c = pulp.LpAffineExpression([(contained_lp_variables[i], factor_vector[i]) for i in range(len(contained_lp_variables))])
        return c


class LiftedLinear(LpProblem):
    def __init__(self, name, sense):
        LpProblem.__init__(self, name, sense)
        self.lpmodel = pulp.LpProblem(name, sense)

    def solve(self):
        raise NotImplementedError

    def status(self):
        return "Not Available for LiftedLinearSolver"


    def lp_variable(self, name):
        raise NotImplementedError

    def affine_expression(self, x, y):
        raise NotImplementedError


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
            if isinstance(expr.args[1], RlpPrediate):
                value = expr.args[0]
                pred = expr.args[1]
            else:
                raise NotImplementedError()

        elif isinstance(expr.args[0], RlpPrediate):
            if expr.args[1].is_Atom:
                value = expr.args[1]
                pred = expr.args[0]
            elif isinstance(expr.args[1], RlpPrediate):
                raise ValueError("Found non-linear constraint!")
            else:
                raise NotImplementedError()

        else:
            raise NotImplementedError()

        return [sstr(pred), ], [float(value), ]

    elif isinstance(expr, RlpPrediate):
        return [sstr(expr), ], [float(1), ]

    elif expr.func is Pow:
        raise ValueError("Found non-linear constraint!")

    else:
        raise NotImplementedError()

    return pred_names, factors
from grounder import Grounder
from reloop.languages.rlp2.visitor import ExpressionGrounder
from reloop.languages.rlp2.rlp import RlpPredicate
from sympy.core.relational import Rel, Ge, Le, Eq
from sympy.core import expand, Add, Mul, Pow, Number, Expr
from sympy.printing import sstr
import scipy.sparse
import numpy


class RecursiveGrounder(Grounder):
    """

    """
    def __init__(self, logkb):
        self.logkb = logkb


    def ground(self, rlpProblem):
        self.lpmodel = LpProblem(rlpProblem.sense)
        self.add_objective_to_lp(self.ground_expression(rlpProblem.objective))

        for constraint in rlpProblem.constraints:
            if isinstance(constraint, Rel):
                lhs = constraint.lhs - constraint.rhs
                ground_result = constraint.__class__(expand(self.ground_expression(lhs)), 0.0)
                self.add_constraint_to_lp(ground_result)
            else:
                # maybe pre-ground here?
                # result = self.ground_expression(constraint.relation, bound=constraint.query_symbols)
                result = constraint.ground(self.logkb)
                for expr in result:
                    ground = self.ground_expression(expr)
                    ground_result = ground.__class__(expand(self.ground_expression(ground.lhs)), ground.rhs)
                    self.add_constraint_to_lp(ground_result)

        return self.lpmodel.get_scipy_matrices(),[name for name in self.lpmodel.lp_variables]

    def ground_expression(self, expr):

        expression_grounder = ExpressionGrounder(expr, self.logkb)
        return expression_grounder.result

    def add_constraint_to_lp(self, constraint):
        """
        Adds a grounded constraint to the LP

        :param constraint: The grounded constraint.
        """
        # log.debug("Add constraint: " + str(constraint))
        # + "\n" + srepr(constraint)
        lhs = constraint.lhs
        b = constraint.rhs
        if constraint.lhs.func is Add:
            for s in constraint.lhs.args:
                if s.is_Atom:
                    lhs -= s
                    b -= s

        # TODO handle Lt and Gt
        if constraint.func is Ge:
            sense = 1
        elif constraint.func is Eq:
            sense = 0
        elif constraint.func is Le:
            sense = -1
        self.lpmodel += (lhs, b, sense)

    def add_objective_to_lp(self, objective):
        """
        Adds a grounded objective to the LP

        :param objective: A grounded expression (the objective)
        """
        # log.debug("Add objective: " + str(objective))
        # + "\n" + srepr(objective)
        expr = objective
        if objective.func is Add:
            for s in objective.args:
                if s.is_Atom:
                    expr -= s

        self.lpmodel += expr



class LpProblem():
    def __init__(self, sense, **options):
        self.sense = sense
        self._index = 0
        self._objective = ()
        self._constraints = {}
        self._constraints[-1] = []
        self._constraints[1] = []
        self._constraints[0] = []
        self._result = None
        self._lp_variables = {}

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

    @property
    def lp_variables(self):
        return self._lp_variables

    def add_lp_variable(self, name):
        if name in self._lp_variables:
            return self._lp_variables[name]
        else:
            self._lp_variables[name] = self.lp_variable(name)
        return self._lp_variables[name]

    def get_scipy_matrices(self):

        ineq_constraint_count = len(self._constraints[1]) + len(self._constraints[-1])
        eq_constraint_count = len(self._constraints[0])

        a = scipy.sparse.dok_matrix((eq_constraint_count, self._index))
        b = scipy.sparse.dok_matrix((eq_constraint_count, 1))

        g = scipy.sparse.dok_matrix((ineq_constraint_count, self._index))
        h = scipy.sparse.dok_matrix((ineq_constraint_count, 1))

        c = scipy.sparse.dok_matrix((self._index, 1))

        i = 0
        for constraint in self._constraints[0]:
            for variable, factor in constraint[0]:
                a[i, variable[0]] = factor
            b[i] = constraint[1]
            i += 1

        i = 0
        for constraint in self._constraints[-1]:
            for variable, factor in constraint[0]:
                g[i, variable[0]] = factor
            h[i] = constraint[1]
            i += 1

        for constraint in self._constraints[1]:
            for variable, factor in constraint[0]:
                g[i, variable[0]] = -factor
            h[i] = -constraint[1]
            i += 1

        for variable in self._objective:
            c[variable[0][0]] = variable[1]

        c = self.sense * c

        return c.todense(), g.tocoo(), h.todense(), a.tocoo(), b.todense()


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
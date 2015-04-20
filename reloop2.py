from sympy import *
from sympy.logic.boolalg import *
from pyDatalog import pyDatalog, pyEngine
import pulp as lp
import numpy as np


class RlpProblem():
    def __init__(self, name, sense, logkb):
        self.lpmodel = lp.LpProblem(name, sense)
        self.logkb = logkb
        self.name = name
        self._reloop_variables = set([])
        self._constraints = []
        self.objective = None
        self._lp_variables = {}

    def add_constraint(self, constraint):
        """Constraints are relations or forallConstraints"""
        self._constraints += [constraint]

    def set_objective(self, objective):
        self.objective = objective

    def add_reloop_variable(self, predicate):
        self._reloop_variables |= {(predicate.name, predicate.arity)}

    @property
    def reloop_variables(self):
        return self._reloop_variables

    @property
    def lp_variables(self):
        return self._lp_variables

    @property
    def constraints(self):
        return self._constraints

    def __iadd__(self, rhs):
        if isinstance(rhs, Rel) | isinstance(rhs, ForAllConstraint):
            self.add_constraint(rhs)
        elif isinstance(rhs, Expr):
            self.set_objective(rhs)
        else:
            raise ValueError("'rhs' must be either an instance of sympy.Rel, sympy.Expr or an instance of "
                             "ForallConstraint!")

        return self

    def add_lp_variable(self, x_name):
        # TODO review this code
        if x_name in self._lp_variables:
            return self._lp_variables[x_name]
        else:
            self._lp_variables[x_name] = lp.LpVariable(x_name)
        return self._lp_variables[x_name]

    def solve(self):
        self.ground_into_lp()
        self.lpmodel.solve()

    def status(self):
        return lp.LpStatus[self.lpmodel.status]

    def get_solution(self):
        return {x: self.lp_variables[x].value() for x in self.lp_variables}

    def ground_into_lp(self):
        self.add_objective_to_lp(self.ground_expression(self.objective))

        for constraint in self.constraints:
            if isinstance(constraint, Rel):
                raise NotImplementedError
            else:
                # maybe pre-ground here?
                # result = self.ground_expression(constraint.relation, bound=constraint.query_symbols)
                result = constraint.ground(self.logkb)
                for expr in result:
                    ground = self.ground_expression(expr)
                    ground_result = ground.__class__(self.ground_expression(ground.lhs), ground.rhs)
                    self.add_constraint_to_lp( ground_result)

    def ground_expression(self, expr):
        if expr.func is Add:
            return Add(*map(lambda x: self.ground_expression(x), expr.args))

        if expr.func is Mul:
            return Mul(*map(lambda x: self.ground_expression(x), expr.args))

        if expr.func is RlpSum:
            result = expr.ground(self.logkb)
            return self.ground_expression(result)

        if isinstance(expr, RlpPredicate):
            if (expr.name, expr.arity) not in self.reloop_variables:
                return expr.ground(self.logkb)

        if expr.func is RlpBooleanPredicate:
            # TODO Evaluate to 0 or 1? Did Martin say: that would be cool?
            raise ValueError("RlpBooleanPredicate is invalid here!")

        return expr

    def add_objective_to_lp(self, objective):
        print "Add objective: " + str(objective)
        # + "\n" + srepr(objective)
        expr = objective
        if objective.func is Add:
            for s in objective.args:
                if s.is_Atom:
                    expr -= s

        c = self.get_affine(expr)
        self.lpmodel += c

    def add_constraint_to_lp(self, constraint):
        print "Add constraint: " + str(constraint)
        # + "\n" + srepr(constraint)
        lhs = constraint.lhs
        b = constraint.rhs
        if constraint.lhs.func is Add:
            for s in constraint.lhs.args:
                if s.is_Atom:
                    lhs -= s
                    b -= s

        c = self.get_affine(lhs)
        if constraint.func is Ge:
            sense = 1
        if constraint.func is Eq:
            sense = 0
        if constraint.func is Le:
            sense = -1
        self.lpmodel += lp.LpConstraint(c, sense, None, b)

    def get_affine(self, expr):
        x_name = []
        x_value = []
        xnames = []
        x = []
        if expr.func is Add:
            for s in expr.args:
                if s.func is Mul:
                    if s.args[0].is_Atom:
                        value = s.args[0]
                        name = srepr(s.args[1])
                    else:
                        value = s.args[1]
                        name = srepr(s.args[0])
                elif isinstance(s, RlpPredicate):
                    value = 1
                    name = srepr(s)
                else:
                    raise NotImplementedError

                x_name.append(name)
                x_value.append(float(value))

        elif expr.func is Mul:
            if expr.args[0].is_Atom:
                value = expr.args[0]
                name = srepr(expr.args[1])
            else:
                value = expr.args[1]
                name = srepr(expr.args[0])
        elif isinstance(expr, RlpPredicate):
            value = 1
            name = srepr(expr)
        else:
            raise NotImplementedError

        x_name.append(name)
        x_value.append(float(value))

        y = np.zeros(len(x_name))
        for j in range(len(x_name)):
            xx = self.add_lp_variable(x_name[j])
            if x_name[j] in xnames:
                y[xnames.index(x_name[j])] += x_value[j]
            else:
                x.append(xx)
                xnames.append(x_name[j])
                y[xnames.index(x_name[j])] = x_value[xnames.index(x_name[j])]
        c = lp.LpAffineExpression([ (x[i],y[i]) for i in range(len(x))])

        return c


    def __str__(self):
        asstr = "Objective: "
        asstr += srepr(self.objective)
        asstr += "\n\n"
        asstr += "Subject to:\n"
        for c in self._constraints:
            asstr += srepr(c)
            asstr += "\n"
        return asstr


class RlpQuery:
    def __init__(self, query_symbols, query):
        self._query_symbols = query_symbols
        self._query = simplify(query)

    @property
    def query_symbols(self):
        return self._query_symbols

    @property
    def query(self):
        return self._query


class ForAllConstraint(RlpQuery):
    def __init__(self, query_symbols, query, relation):
        RlpQuery.__init__(self, query_symbols, query)
        self.relation = relation
        self.result = []
        self.grounded = False

    def ground(self, logkb):
        answer = logkb.ask(self.query_symbols, self.query)

        result = set([])
        if answer is not None:
            lhs = self.relation.lhs - self.relation.rhs
            for a in answer.answers:
                    expression_eval_subs = lhs
                    for index, symbol in enumerate(self.query_symbols):
                        expression_eval_subs = expression_eval_subs.subs(symbol, a[index])
                    result |= {self.relation.__class__(expression_eval_subs, 0.0)}

        self.result = result
        self.grounded = True
        return self.result

    def __str__(self):
        return "FORALL " + str(self.query_symbols) + " in " + str(self.query) + ": " + srepr(self.relation)


class SubSymbol(Symbol):
    """Just a sympy.Symbol, but inherited to be able to define symbols explicitly
    """
    pass


def rlp_predicate(name, arity, boolean=false):
    if arity < 1:
        raise ValueError("Arity must not be less than 1. Dude!")
    if boolean:
        predicate_type = RlpBooleanPredicate
    else:
        predicate_type = RlpPredicate
    predicate_class = type(name + "\\" + str(arity), (predicate_type,), {"arity": arity, "name": name, "result": None,
                                                                         "grounded": False})
    return predicate_class


class RlpPredicate(Function):

    @classmethod
    def eval(cls, *args):
        if not cls.grounded:
            return None
        return cls.result

    def ground(self, logkb):
        args = self.args
        if len(args) > self.arity:
            raise Exception("Too many arguments.")

        if len(args) < self.arity:
            raise Exception("Not enough arguments")

        for argument in args:
            if isinstance(argument, SubSymbol):
                raise ValueError("Found free symbols while grounding: " + str(self))

        answer = logkb.ask_predicate(self)
        if answer is None:
            raise ValueError('Predicate is not defined or no result!')

        if len(answer.answers) != 1:
            raise ValueError("The LogKb gives multiple results. Oh!")

        result = answer.answers.pop()
        self.result = result
        self.grounded = True
        return float(result[0])


    @classmethod
    def __str__(cls):
        return '%s/%s' % (cls.name, cls.arity)

    __repr__ = __str__


class RlpBooleanPredicate(BooleanAtom, Function):
    pass


class RlpSum(Expr, RlpQuery):

    def __init__(self, query_symbols, query, expression):
        RlpQuery.__init__(self, query_symbols, query)
        self.expression = expression
        self.result = None
        self.grounded = False

    def ground(self, logkb):
        answer = logkb.ask(self.query_symbols, self.query)
        result = 0
        for a in answer.answers:
                expression_eval_subs = self.expression
                for index, symbol in enumerate(self.query_symbols):
                    expression_eval_subs = expression_eval_subs.subs(symbol, a[index])
                result += expression_eval_subs
        self.result = result
        self.grounded = True
        return self.result

    @property
    def is_number(self):
        return False

    def _hashable_content(self):
        """We need to overwrite this: The first parameter is a list and because of that the base
        implementation does not work."""
        return tuple(self.query_symbols) + self._args[1:]

    def _sympyrepr(self, printer, *args):
        if not self.grounded:
            return "RlpSum(" + str(self.query_symbols) + " in " + str(self.query) + ", " + srepr(self.expression) + ")"
        return srepr(self.result)



class LogKb:
    def ask(self, query_symbols, query):
        raise NotImplementedError

    def ask_predicate(self, predicate):
        raise NotImplementedError

class PyDatalogLogKb(LogKb):

    def ask(self, query_symbols, query):

        helper_predicate = 'helper(' + ','.join([str(v) for v in query_symbols]) + ')'
        tmp = helper_predicate + " <= " + self.transform_query(query)
        pyDatalog.load(tmp)

        answer = pyDatalog.ask(helper_predicate)
        pyEngine.Pred.reset_clauses(pyEngine.Pred("helper", len(query_symbols)))

        return answer

    def ask_predicate(self, predicate):

        query = predicate.name + "("
        query += ','.join(["'" + str(a) + "'" for a in predicate.args])
        query += ", X)"

        answer = pyDatalog.ask(query)
        return answer

    @staticmethod
    def transform_query(query):
        if query.func is And:
            return " &".join([PyDatalogLogKb.transform_query(arg) for arg in query.args])

        if query.func is Not:
            return " ~" + PyDatalogLogKb.transform_query(query.args[0])

        if isinstance(query, RlpBooleanPredicate):
            join = ",".join([str(arg) if isinstance(arg, SubSymbol) else "'" + str(arg) + "'" for arg in query.args])
            return " " + query.name + "(" + join + ")"

        raise NotImplementedError
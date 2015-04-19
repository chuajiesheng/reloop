from sympy import *
from sympy.logic.boolalg import *
from pyDatalog import pyDatalog, pyEngine
import pulp as lp


class RlpProblem():
    def __init__(self, logkb, name="noname", sense=0):
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
        self._reloop_variables |= set([(predicate.name, predicate.arity)])

    @property
    def reloop_variables(self):
        return self._reloop_variables

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
        # return {x: self.myLpVars[x].value() for x in self.myLpVars}
        pass

    def ground_into_lp(self):
        self.add_to_lp(self.ground_expression(self.objective))

        for constraint in self.constraints:
            if isinstance(constraint, Rel):
                raise NotImplementedError
            else:
                # maybe pr ground here?
                # result = self.ground_expression(constraint.relation, bound=constraint.query_symbols)
                result = constraint.ground(self.logkb)
                for expr in result:
                    ground = self.ground_expression(expr)
                    self.add_to_lp(ground)

    def ground_expression(self, expr):
        if expr.func is RlpSum:
            result = expr.ground(self.logkb)
            return self.ground_expression(result)

        if expr.func is RlpPredicate:
            if set([(expr.name, expr.arity)]) not in self.reloop_variables:
                return expr.ground(self.logkb)

        if expr.func is RlpBooleanPredicate:
            # TODO Evaluate to 0 or 1? Did Martin say: that would be cool?
            raise ValueError("RlpBooleanPredicate is invalid here!")

        return expr

    @staticmethod
    def add_to_lp(expr, rhs=None):
        pass

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
        result = []
        for a in answer.answers:
                expression_eval_subs = self.expression
                for index, symbol in enumerate(self.query_symbols):
                    expression_eval_subs = expression_eval_subs.subs(symbol, int(a[index]))
                result += expression_eval_subs
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

        answer = logkb.ask(self)
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
    def ask(cls):
        args = cls.args
        if len(args) > cls.arity:
            raise Exception("Too many arguments.")
        if len(args) < cls.arity:
            raise Exception("Not enough arguments")
        for argument in args:
            if isinstance(argument, SubSymbol):
                return Expr.__new__(cls, *args)
        query = cls.name + "("
        query += ','.join(["'" + str(a) + "'" for a in args])
        query += ")"
        print("Log: pyDatalog query: " + query)
        answer = pyDatalog.ask(query)
        if answer is None:
            return S.false
        return S.true

    # @classmethod
    # def _eval_simplify(cls, ratio, measure):
    #     return cls


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
                    expression_eval_subs = expression_eval_subs.subs(symbol, int(a[index]))
                result += expression_eval_subs
        self.result = result
        self.grounded = True
        return self.result

    @property
    def is_number(self):
        return False

    def _sympyrepr(self, printer, *args):
        if not self.grounded:
            return "RlpSum(" + str(self.query_symbols) + " in " + str(self.query) + ", " + srepr(self.expression) + ")"
        return srepr(self.result)


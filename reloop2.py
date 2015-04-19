from sympy import *
from sympy.logic.boolalg import *
from pyDatalog import pyDatalog, pyEngine
import pulp as lp


class RlpProblem():
    def __init__(self, name="noname", sense=0):
        self.lpmodel = lp.LpProblem(name, sense)
        self.name = name
        self._reloop_variables = set([])
        self._constraints = []
        self.objective = None

    def add_constraint(self, constraint):
        """Constraints are relations or forallConstraints"""
        self._constraints += [constraint]

    def set_objective(self, objective):
        self.objective = objective

    def add_variable(self, predicate):
        self._reloop_variables |= set([(predicate.name, predicate.arity)])

    @property
    def reloop_variables(self):
        return self._reloop_variables

    def __iadd__(self, rhs):
        if isinstance(rhs, Rel) | isinstance(rhs, ForAllConstraint):
            self.add_constraint(rhs)
        elif isinstance(rhs, Expr):
            self.set_objective(rhs)
        else:
            raise ValueError("'rhs' must be either an instance of sympy.Rel, sympy.Expr or an instance of "
                             "ForallConstraint!")

        return self

    def solve(self):
        self.ground_into_lp()
        self.lpmodel.solve()

    def status(self):
        return lp.LpStatus[self.lpmodel.status]

    def get_solution(self):
        # return {x: self.myLpVars[x].value() for x in self.myLpVars}
        pass

    def ground_into_lp(self):
        pass

    def __str__(self):
        str = "OBJECTIVE: "
        str += srepr(self.objective)
        str += "\n\n"
        str += "Subject to:\n"
        for c in self._constraints:
            str += srepr(c)
            str += "\n"
        return str


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

    def __str__(self):
        return "FORALL: " + str(self.query_symbols) + " in " + str(self.query) + ": " + repr(self.relation)

class SubstitutionSymbol(Symbol):
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
    predicate_class = type(name + "\\" + str(arity), (predicate_type,), {"arity": arity, "name": name})
    return predicate_class


class RlpPredicate(Function):
    @classmethod
    def eval(cls, *args):
        return None

    def ask(cls):
        args = cls.args
        if len(args) > cls.arity:
            raise Exception("Too many arguments.")

        if len(args) < cls.arity:
            raise Exception("Not enough arguments")

        for argument in args:
            if isinstance(argument, SubstitutionSymbol):
                return None

        query = cls.name + "("
        query += ','.join(["'" + str(a) + "'" for a in args])
        query += ", X)"

        print("Log: pyDatalog query: " + query)
        answer = pyDatalog.ask(query)
        if answer is None:
            raise ValueError('Predicate is not defined or no result!')

        if len(answer.answers) == 1:
            result = answer.answers.pop()
            return float(result[0])

        raise ValueError("PyDatalog gives multiple results. Oh!")

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
            if isinstance(argument, SubstitutionSymbol):
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

    @property
    def is_number(self):
        return False
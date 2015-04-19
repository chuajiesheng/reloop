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

    def add_constraint(self, constraint):
        """Constraints are relations or forallConstraints
        """
        if (constraint is not Rel) | (constraint is not ForAllConstraint):
            raise ValueError("'constraint' must be either an instance of sympy.Re or an instance of ForallConstraint!")
        self._constraints += [constraint]

    def set_objective(self, objective):
        pass

    def add_variable(self, predicate):
        self._reloop_variables |= set([(predicate.name, predicate.arity)])

    @property
    def reloop_variables(self):
        return self._reloop_variables

    def __ilshift__(self, objective):
        self.set_objective(objective)

    def __iadd__(self, constraint):
        self.add_constraint(constraint)


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
        RlpQuery.__init__(query_symbols, query)
        self.relation = relation


class SubstitutionSymbol(Symbol):
    """Just a sympy.Symbol, but inherited to be able to define symbols explicitly
    """
    pass


# def rlp_function(name, arity):
# predicate_class = type(name + "\\" + str(arity), (RlpFunction,), {"arity": arity, "name": name})
#     return predicate_class


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


class RlpBooleanPredicate(BooleanFunction):
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


class RlpSum(Expr, RlpQuery):
    def __init__(self, query_symbols, query, expression):
        RlpQuery.__init__(self, query_symbols, query)
        self.expression = expression


# class RlpPredicate(Expr):
#
#     def __new__(cls, *args):
#         if len(args) > cls.arity:
#             raise Exception("Too many arguments.")
#
#         if len(args) < cls.arity:
#             raise Exception("Not enough arguments")
#
#         for argument in args:
#             if isinstance(argument, SubstitutionSymbol):
#                 return Expr.__new__(cls, *args)
#
#         query = cls.name + "("
#         query += ','.join(["'" + str(a) + "'" for a in args])
#         query += ")"
#
#         print("Log: pyDatalog query: " + query)
#         answer = pyDatalog.ask(query)
#         if answer is None:
#             return False
#
#         return True


# class RlpPredicate(Function):
#
#     @classmethod
#     def eval(cls, *args):
#         if len(args) > cls.arity:
#             raise Exception("Too many arguments.")
#
#         if len(args) < cls.arity:
#             raise Exception("Not enough arguments")
#
#         for argument in args:
#             if isinstance(argument, SubstitutionSymbol):
#                 return None
#
#         query = cls.name + "("
#         query += ','.join(["'" + str(a) + "'" for a in args])
#         query += ", X)"
#
#         print("Log: pyDatalog query: " + query)
#         answer = pyDatalog.ask(query)
#         if answer is None:
#             raise ValueError('Predicate is not defined or no result!')
#
#         if len(answer.answers) == 1:
#             result = answer.answers.pop()
#             return float(result[0])
#
#         raise ValueError("PyDatalog gives multiple results. Oh!")
#
#     @classmethod
#     def __str__(cls):
#         return '%s/%s' % (cls.name, cls.arity)
#
#     __repr__ = __str__



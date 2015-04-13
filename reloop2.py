from sympy import *
from pyDatalog import pyDatalog, pyEngine
import pulp as lp


class RlpProblem(pyDatalog.Mixin):
    
    def __init__(self, name="noname", sense=0):
        self.lpmodel = lp.LpProblem(name, sense)
        self.name = name
        self.reloop_variables = set([])

    def add_constraint(self, relation):
        pass
    
    def add_forall_constraint(self, forall):
        pass
    
    def set_objective(self, objective):
        pass

    def add_variable(self, predicate):
        self.reloop_variables |= set([(predicate.name, predicate.arity)])

    def get_variables(self):
        return self.reloop_variables

    def __ilshift__(self, objective):
        self.set_objective(objective)

    def __iadd__(self, relation):
        self.add_constraint(relation)


class Constraint:
    
    def __init__(self, relation):
        self.relation = relation  


class ForAll:
    
    def __init__(self, kb_symbols, query, constraint):
        pass


''' to allow strings in predicate params
'''
class SubstitutionSymbol(Symbol):
    pass

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

class RlpAtom(Function):

    @classmethod
    def eval(cls, *args):
        return None

# def rlp_function(name, arity):
#     predicate_class = type(name + "\\" + str(arity), (RlpFunction,), {"arity": arity, "name": name})
#     return predicate_class


def rlp_predicate(name, arity):
    predicate_class = type(name + "\\" + str(arity), (RlpPredicate,), {"arity": arity, "name": name})
    return predicate_class

class RlpPredicate(RlpAtom):
    
    @classmethod
    def eval(cls, *args):
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

# def rlpSum(symbols, query, expression):
#    return RlpSum(symbols, query, expression)


class RlpSubstitution(RlpAtom):
    pass


class RlpSum(Expr, RlpQuery):

    def __init__(self, query_symbols, query, expression):
        RlpQuery.__init(self, query_symbols, query)


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





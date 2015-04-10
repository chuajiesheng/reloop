from sympy import *
from pyDatalog import pyDatalog, pyEngine
import pulp as lp


class RlpProblem(pyDatalog.Mixin):
    
    def __init__(self, name="noname", sense=0):
        self.lpmodel = lp.LpProblem(name, sense)
        self.name = name
        
    def add_constraint(self, relation):
        pass
    
    def add_forall_constraint(self, forall):
        pass
    
    def set_objective(self, objective):
        pass

    def __ilshift__(self, objective):
        self.set_objective(objective)

    def __iadd__(self, relation):
        self.add_constraint(relation)


class Constraint:
    
    def __init__(self, relation):
        self.relation = relation  


class ForAll:
    
    def __init__(self, symbols, query, constraint):
        pass


''' to allow strings in predicate params
'''
class SubstitutionSymbol(Symbol):
    pass


def rlp_function(name, arity):
    predicate_class = type(name + "\\" + str(arity), (RlpFunction,), {"arity": arity, "name": name})
    return predicate_class


def rlp_predicate(name, arity):
    predicate_class = type(name + "\\" + str(arity), (RlpPredicate,), {"arity": arity, "name": name})
    return predicate_class


class RlpPredicate(Expr):
           
    def __new__(cls, *args):
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
            return False
        
        return True
    
class RlpFunction(Function):
    
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


class RlpSum(Expr):
    
    def doit(self, **hints):
        
        sum_symbols, query, expression = self.args
        
        helper_predicate = 'helper(' + ','.join([str(v) for v in sum_symbols]) + ')'
        pyDatalog.load(helper_predicate + " <= " + query)
        
        answer = pyDatalog.ask(helper_predicate)
        pyEngine.Pred.reset_clauses(pyEngine.Pred("helper", len(sum_symbols)))
            
        result = 0
        for a in answer.answers:
                expression_eval_subs = expression
                for index, symbol in enumerate(sum_symbols):
                    expression_eval_subs = expression_eval_subs.subs(symbol, int(a[index]))
                result += expression_eval_subs
        return result
    





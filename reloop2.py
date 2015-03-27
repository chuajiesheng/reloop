from sympy import *
from pyDatalog import pyDatalog, pyEngine

## PredicateFactory, is the same as

#class specificPredicate(rlpPred):
#    name = "specificPredicate"
#    arity = 2
def PredicateFactory(name, arity):
    predicateClass = type(name + "\\" + str(arity), (RlpPredicate,),{"arity": arity, "name" : name})
    return predicateClass

# to allow strings in predicate params
class SubstitutionSymbol(Symbol):
    pass

class RlpPredicate(Function):
    
    @classmethod
    def eval(cls, *args):
        if len(args) > cls.arity:
            raise Exception("Too many arguments.")
        
        if len(args) < cls.arity:
            raise Exception("Not enough arguments")
        
        for arg in args:
            if isinstance(arg, SubstitutionSymbol):
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
    def __str__(self):
        return '%s/%s' % (self.name, self.arity)

    __repr__ = __str__
    
class RlpSum(Expr):
    
    def doit(self, **hints):
        symbols, query, expression = self.args
            
        helperPredicate = 'helper(' + ','.join([str(v) for v in symbols]) + ')'
        pyDatalog.load(helperPredicate + " <= " + query)
        
        answer = pyDatalog.ask(helperPredicate)
        pyEngine.Pred.reset_clauses(pyEngine.Pred("helper",len(symbols)))
            
        result = 0
        for a in answer.answers:
                result += expression.subs(symbols[0], int(a[0]))
        
        return result
        
def rlpSum(symbols, query, expression):
    return RlpSum(symbols, query, expression).doit()

## Relational Program starts here

@pyDatalog.predicate()
def attribute3(X,Y,Z):
    yield("1","1","2")
    yield("1","2","2")
    yield("2","1","2")
    yield("2","2","1")
    yield("3","1","3")
    yield("3","2","4")
    yield("4","1","4")
    yield("4","2","3")
    yield("7","2","3")
    yield("7","2","5")

# define symbols
x = SubstitutionSymbol('x')
y = SubstitutionSymbol('y')
X = SubstitutionSymbol('X')


attribute = PredicateFactory("attribute", 2)
print(attribute)
print(type(attribute))

print(attribute("1","2"))

simpleSum = rlpSum([X,], "attribute(X,'1',Y)", attribute(X, '1')*y*y)
simpleSum.subs(y, 1)



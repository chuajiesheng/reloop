import pyparsing as pp
from pyDatalog import pyDatalog, pyEngine
import pulp as lp
import numpy as np

#-----------------------------------------------------------------------------
# The following statements define the grammar for the parser.

# the parser for a parameterized constraints
number = pp.Regex(r"[+-]?\d+\.\d*([eE][+-]?\d+)?") | pp.Word(pp.nums)

plus  = pp.Literal( "+" )
minus = pp.Literal( "-" )
mult  = pp.Literal( "*" )
addop  = (plus | minus)

LPAR  = pp.Literal( "(" )
RPAR  = pp.Literal( ")" )
LSPAR  = pp.Literal( "[" )
RSPAR  = pp.Literal( "]" )
COMMA  = pp.Literal( "," )
AND  = pp.Literal( "&" )

# ground atoms in a ground term
predicateName = pp.Word(pp.alphanums)
constant = pp.Word(pp.alphanums.lower())
def substituteConstant(s,l,t):
    return "'"+t[0]+"'"
constant.setParseAction(substituteConstant)

groundArglist = constant + pp.ZeroOrMore( COMMA + constant)
groundAtom = predicateName + LPAR + pp.Optional(groundArglist, default=[]) + RPAR
groundFunction=predicateName + LSPAR + pp.Optional(groundArglist, default=[]) + RSPAR

# parameterized term
multGroundTerm = (number + mult + groundAtom) | (groundFunction + mult + groundAtom) | (number + mult + groundFunction)
groundTerm = pp.Combine(multGroundTerm + pp.ZeroOrMore(addop + multGroundTerm))
#input = "1*edge(a,b)+1*edge(c,d)"
#result = groundTerm.parseString(input,parseAll=True)
#print result

logTerm = constant | pp.Word(pp.alphanums)

arglist = logTerm + pp.ZeroOrMore( COMMA + logTerm)
atom = predicateName + LPAR + pp.Optional(arglist, default=[]) + RPAR
# a function is gives back a number
function = predicateName + LSPAR + pp.Optional(arglist, default=[]) + RSPAR

# parameterized term
multTerm = (number + mult + atom) | (function + mult + atom) | (number + mult + function)
parTerm = pp.Combine(multTerm + pp.ZeroOrMore(addop + multTerm), adjacent=False )

# input = "1*edge(X,Y)+1*edge(Y,X)"
# result = parTerm.parseString(input,parseAll=True)
# print result
# exit()
# logical query
# only conjunctions for now
literal =  ("~"+atom) | atom
query = pp.Combine((literal + pp.ZeroOrMore(AND + literal)), adjacent=False )
#input = "edge(X,Y) & edge(Y,X)"
#result = query.parseString(input,parseAll=True)
#print result

SUM  = pp.Literal( "sum" )
logVar = pp.Word(pp.alphas.upper())
logVarList = (logVar + pp.ZeroOrMore( COMMA.suppress() + logVar)).setParseAction(lambda t : t.asList())
IN  = pp.Literal( "in" ).suppress()
COLON  = pp.Literal( ":" ).suppress()
LCPAR  = pp.Literal( "{" ).suppress()
RCPAR  = pp.Literal( "}" ).suppress()

# parameterized sum
sumParTerm = SUM + LCPAR + pp.Group(logVarList) + IN + query + RCPAR + COLON + LCPAR + parTerm + RCPAR
#input = "sum { X,Y in edge(X,Y) & edge(Y,X) } : { 1*flow(X) }"
#result = sumParTerm.parseString(input,parseAll=True)
#print result

rlobjective = pp.Group(sumParTerm) ^ ( pp.Group(sumParTerm) + pp.Combine(addop + groundTerm, adjacent=False )) ^ pp.Combine(groundTerm, adjacent=False )
# input = "sum{ Y in edge(Y,X) } : { 1*flow(Y,X) } - 1*inFlow(b)"
# input = "sum{ X,Y in edge(X,Y) } : { cost[X,Y]*flow(X,Y) }"
# input = "sum{ X,Y in source(X) & edge(X,Y) } : { time[X,Y]*use(X,Y) }"
# result = rlobjective.parseString(input,parseAll=True)
# print result
# exit()
FORALL  = pp.Literal( "forall" )
EQ  = pp.Literal( "=" )
LEQ  = pp.Literal( "<=" )
GEQ  = pp.Literal( ">=" )

parEquation = (pp.Group(sumParTerm) + pp.Combine((LEQ ^ GEQ ^ EQ ) + number, adjacent=False )) |  \
              (pp.Group(sumParTerm) + pp.Combine(addop + parTerm + (LEQ ^ GEQ ^ EQ ) + number, adjacent=False )) |  \
              pp.Combine(parTerm + (LEQ ^ GEQ ^ EQ ) + number, adjacent=False )
#input = "sum{ Y in edge(Y,X) } : { 1*flow(Y,X) } - 1*inFlow(X) = 0"
#result = parEquation.parseString(input,parseAll=True)
#print result

rlconstraint = (pp.Group(FORALL + LCPAR + pp.Group(logVarList) + IN + query) + RCPAR + COLON + LCPAR + parEquation + RCPAR) | \
               rlobjective + pp.Combine( (LEQ ^ GEQ ^ EQ ) + number, adjacent=False )

#input = "forall{ X,Y in node(X)&node(Y) } : { sum{ Y in edge(Y,X)&edge(Y,X) } : { 1*flow(Y,X) } - 1*inFlow(X) = 0}"
#input = "sum{ X,Y in edge(X,Y) } : { 1*flow(Y,X) } -1 = 0"
#result = rlconstraint.parseString(input,parseAll=True)
#print result

# End of grammar definition
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# The following statements define the grammar for a parser to extract the
# variables from queries and parTerms after we have parsed the input
# using the above parser.

# extract all variables of a query
queryAtom = predicateName.suppress() + LPAR.suppress() + pp.Optional(arglist, default=[]) + RPAR.suppress()
queryAtom.setParseAction(lambda t : list(set(''.join([o if not o in [','] else ' ' for o in t]).split())))
variablesQuery = (queryAtom + pp.ZeroOrMore(AND.suppress() + queryAtom))
#input = "node(X)&node(Y,Y,Z)"
#result = variablesQuery.parseString(input,parseAll=True).asList()
#print result

# extract all variables of a parTerm
variablesParTerm = (pp.Optional(minus).suppress() + number.suppress() + mult.suppress() + queryAtom) + \
                   pp.ZeroOrMore(addop.suppress() + number.suppress() + mult.suppress() + queryAtom)
#input = "-1*flow(Y,X)"
#result = variablesParTerm.parseString(input,parseAll=True).asList()
#print result

# replace all ground function calls
functionCallConstant = pp.Word(pp.alphanums.lower())
def substituteConstant(s,l,t):
    return "'"+t[0]+"'"
functionCallConstant.setParseAction(substituteConstant)

functionCallGroundArglist = functionCallConstant + pp.ZeroOrMore( COMMA + functionCallConstant)

groundCall=(predicateName + LSPAR + pp.Optional(functionCallGroundArglist, default=[]) + RSPAR)
def transformGroundCall(s,l,t):
    punc = ['[']
    tmp= [o if not o in punc else '(' for o in t]
    tmp[-1] = ','
    value = pyDatalog.ask("".join(tmp)+'Value)')

    if value:
        val = value.answers[0]
        val = val[0]
    else:
        val = 0
    return str(float(val))
groundCall.setParseAction(transformGroundCall)

def evalMultGroundCall(s,l,t):
    return str(eval("".join(t)))

numberGroundCall = number + mult + groundCall
numberGroundCall.setParseAction(evalMultGroundCall)

multGroundCall = (number + mult + groundAtom) | (groundCall + mult + groundAtom) | numberGroundCall


groundCallTerms = pp.Combine(multGroundCall + pp.ZeroOrMore(addop + multGroundCall))#.setParseAction(printT)

def replaceFunctionCalls(String):
    return groundCallTerms.transformString(String)

#print parTerm.parseString('cost[n1,n2]*flow(n1,n2)')#+cost[n1,n3]*flow(n1,n3)')

#print query.transformString('flow(1,X)')#+cost[n1,n3]*flow(n1,n3)')

#exit()

# End of grammar definition
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# The following are helper functions for extracting the variables after
# we have parsed a constraint

def getpyDatalogFunctionValue(query):
    string = groundCall.transformString(query)
    return float(string)

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

class reloopToken:

    def __init__(self, LogVars = [], QueryString='', TermString=''):
        self.LogVars = LogVars
        self.QueryString = QueryString
        self.TermString = TermString
        self.Query = 'constraint(' + ','.join(LogVars) + ')'
        self.Clause = self.Query + '<=' + query.transformString(self.QueryString)

    def queryString(self):
        return self.QueryString

    def termString(self):
        return self.TermString

    def logVars(self):
        return self.LogVars

    def logVarsInQuery(self):
        return list(set(self.Query,parseAll=True).asList())

    def logVarsInTerm(self):
        return variablesParTerm.parseString(self.Term,parseAll=True).asList()

    def query(self):
        return self.Query

    def clause(self):
        return self.Clause

    def __str__(self):
        return "\n %s\n %s\n %s" % (self.LogVars,self.QueryString,self.TermString)

    def type(self):
        return self.__class__.__name__

class reloopForAll(reloopToken):

    def __init__(self, token1, token2,token3,sense):
        reloopToken.__init__(self, token1, token2, token3)
        self.sense = sense
        if self.sense == -1:
            lhs,rhs = token3.split('<=')
        elif self.sense == 1:
            lhs,rhs = token3.split('>=')
        else:
            lhs,rhs = token3.split('=')

    def logVarsInTerm(self):
        lhs,rhs = self.Term.replace('>=',' ').replace('<=',' ').replace('=',' ').split()
        return list(set(variablesParTerm.parseString(lhs,parseAll=True).asList()))

    def getSense(self):
        if self.sense == -1:
            lhs,rhs = self.TermString.split('<=')
        elif self.sense == 1:
            lhs,rhs = self.TermString.split('>=')
        else:
            lhs,rhs = self.TermString.split('=')
        rhs = float(rhs)
        return lhs,rhs,self.sense



class reloopSum(reloopToken):

    def __init__(self, token1,token2,token3):
        reloopToken.__init__(self, token1, token2, token3)

class reloopConstraint:

    def __init__(self, String):

        self.tokens = []
        self.string = String
        forall = []


        if (String.startswith('forall')):
            #a forall constraint

            result = rlconstraint.parseString(String,parseAll=True).asList()
            for token in result:
                print token
                if token[0] == 'forall':
                    forall = token[1:]
                elif token[0] == 'sum':
                    print token
                    self.tokens.append(reloopSum(token[1],token[2],token[3]))
                else:
                    if '<=' in token:
                        self.sense = -1
                    elif '>=' in token:
                        self.sense = 1
                    else:
                        self.sense = 0
                    self.tokens[:0]= [reloopForAll(forall[0],forall[1],token,self.sense)]

        elif (String.startswith('sum')):
            #a sum constraint

            if ("<=" in String) or (">=" in String) or ("=" in String):
                # a "forall" constraint with no query

                result = rlconstraint.parseString(String,parseAll=True).asList()

                forall= [[],'True']

                for token in result:

                    if ("<=" in token) or (">=" in token) or ("=" in token):

                        if '<=' in token:
                            self.sense = -1
                        elif '>=' in token:
                            self.sense = 1
                        else:
                            self.sense = 0

                        self.tokens[:0]= [reloopForAll(forall[0],forall[1],token,self.sense)]
                    else:
                        # a sum token
                        self.tokens.append(reloopSum(token[1],token[2],token[3]))

            else:
                # it is the objective
                result = rlobjective.parseString(String,parseAll=True).asList()

                self.sense = -2

                for token in result:

                    self.tokens.append(reloopSum(token[1],token[2],token[3]))



    def getParts(self):
        return self.tokens

    def getSense(self):
        return self.sense

    def __str__(self):
        return ','.join(['%s' % t for t in self.tokens])

    def query(self):
        for t in self.tokens:
            print t.type()

#input = "forall{ X,Y in node(X)&node(Y) } : { sum{ Y in edge(Y,X)&edge(Y,X) } : { 1*flow(Y,X) } - 1*inFlow(X) = 0}"
#print input
#c = reloopConstraint(input)
#print c


class reloopProblem(pyDatalog.Mixin):

    def __init__(self, name='NoName', sense = 0):
        self.name = name
        self.sense = 0
        self.lpmodel = lp.LpProblem(name, sense)
        self.myLpVars = {}
        self.definitions = []

    def __iadd__(self, value) :
        if isinstance(value,reloopConstraint):
            self.addConstraint(value)
        return self

    def __str__(self):
        return '%s' % self.lpmodel

    def name(self):
        return self.name

    def printModel(self):
        print self.lpmodel

    def solve(self):
        self.lpmodel.solve()

    def status(self):
        return lp.LpStatus[self.lpmodel.status]

    def printLpVars(self):
        for key, value in self.myLpVars.iteritems():
            print key+" = "+str(value)

    def addLpVar(self,x_name):

        if x_name in self.myLpVars:
            return self.myLpVars[x_name]
        else:
            self.myLpVars[x_name]=lp.LpVariable(x_name)
        return self.myLpVars[x_name]

    def getSolution(self):
        return {x: self.myLpVars[x].value() for x in self.myLpVars}

    def replaceFunctionCalls(self,String):
        return groundCallTerms.transformString(String)

    def addConstraintString(self,answer,sense,b):
        global constants

        answer = answer.replace("--","+")


        # parsing the string
        punc = ['+','-']
        consStr = list(answer)
        tmp=''.join([o if not o in punc else ' '+o for o in consStr]).split()
        x_name = []
        x_value = []
        xnames = []
        x = []
        for term in tmp:
            if '*' not in term:
                b -= float(term)
            else:
                punc = ['*']
                value, name=''.join([o if not o in punc else ' ' for o in term]).split()
                x_name.append(name)
                if is_number(value):
                    x_value.append(float(value))
                else:
                    pass
        y = np.zeros(len(x_name))
        for j in range(len(x_name)):
            xx = self.addLpVar(x_name[j])
            if(x_name[j] in xnames):
                y[xnames.index(x_name[j])] += x_value[j]
            else:
                x.append(xx)
                xnames.append(x_name[j])
                y[xnames.index(x_name[j])] = x_value[xnames.index(x_name[j])]
        c = lp.LpAffineExpression([ (x[i],y[i]) for i in range(len(x))])

        if sense==-2:
            self.lpmodel += c
        else:
             self.lpmodel += lp.LpConstraint(c,sense,None,b)

       # self.printLpVars()

    def addSumConstraints(self, forAllAns, forAll, Sums):

        lhs,b,sense = forAll.getSense()

        for ansForAll in forAllAns:


            termSum = ''
            for Sum in Sums:
                clause = Sum.clause()
                query  = Sum.query()
                term   = Sum.termString()
                arity = len(forAll.logVars())
                # print term
                index = 0
                for var in forAll.logVars():
                    clause = clause.replace(var,"'"+ansForAll[index]+"'")
                    query = query.replace(var,ansForAll[index])
                    term = term.replace(var,ansForAll[index])
            #    pyDatalog.clear()
                pyDatalog.load(clause)
                sumAns = pyDatalog.ask(query)
                pyEngine.Pred.reset_clauses(pyEngine.Pred("constraint",arity))
                if sumAns:
                    for ans in sumAns.answers:
                        term2 = term
                        index = 0
                        for var in Sum.logVars():
                            term2 = term2.replace(var,ans[index])
                            index += 1
                        termSum  = termSum + '+' + term2

            if not termSum == '':
                termSum = termSum[1:]
            answer  = lhs
            index = 0
            for var in forAll.logVars():
                answer = answer.replace(var,ansForAll[index])
                index += 1
            answer = replaceFunctionCalls(termSum + answer)
            self.addConstraintString(answer,sense,b)

    def addSumConstraintsTrue(self, forAll, Sums):

        lhs,b,sense = forAll.getSense()


        termSum = ''
        for Sum in Sums:
            clause = Sum.clause()
            query  = Sum.query()
            term   = Sum.termString()

           # pyDatalog.clear()
            pyDatalog.load(clause)
            sumAns = pyDatalog.ask(query)
            arity = len(Sum.logVars())
            pyEngine.Pred.reset_clauses(pyEngine.Pred("constraint",arity))

            if sumAns:
                for ans in sumAns.answers:
                    term2 = term
                    index = 0
                    for var in Sum.logVars():
                        term2 = term2.replace(var,ans[index])
                        index += 1
                    termSum  = termSum + '+' + term2

        if not termSum == '':
            termSum = termSum[1:]

        answer = replaceFunctionCalls(termSum)

        self.addConstraintString(answer,sense,b)

    def addObjective(self, Sums):


        termSum = ''
        for Sum in Sums:
            clause = Sum.clause()
            query  = Sum.query()
            term   = Sum.termString()
            pyDatalog.load(clause)
            arity = len(Sum.logVars())
            sumAns = pyDatalog.ask(query)
            pyEngine.Pred.reset_clauses(pyEngine.Pred("constraint",arity))


            if sumAns:
                for ans in sumAns.answers:
                    term2 = term
                    index = 0
                    for var in Sum.logVars():
                        term2 = term2.replace(var,ans[index])
                        index += 1
                    termSum  = termSum + '+' + term2

        if not termSum == '':
            termSum = termSum[1:]

        answer = self.replaceFunctionCalls(termSum)


        self.addConstraintString(answer,-2,-2)


    def addConstraint(self,constraint):

        if constraint.getSense() > -2:
            # constraint
            #print constraint
            parts = constraint.getParts()
            if (parts[0].query() == "constraint()"):
                self.addSumConstraintsTrue(parts[0],parts[1:])
            else:
                pyDatalog.load(parts[0].clause())
                ans = pyDatalog.ask(parts[0].query())
                arity = len(parts[0].logVars())
                pyEngine.Pred.reset_clauses(pyEngine.Pred("constraint",arity))

                if ans:
                    self.addSumConstraints(ans.answers, parts[0], parts[1:])

        else:
            #objective
            parts = constraint.getParts()
            self.addObjective(parts)







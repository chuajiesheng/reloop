import pyparsing as pp
from pyDatalog import pyDatalog, pyEngine
import pulp as lp
import numpy as np
from numbers import Number

#-----------------------------------------------------------------------------
# The following statements define the grammar for the parser.

# the parser for a parameterized constraints

@pyDatalog.predicate()
def test(X,Y,Z):
    yield('a','b', 3.14)


MAXLEN = 1000
class Term:
    def __add__(a,b):
        global arithmetic
        if isinstance(b,Number) or isinstance(b,Term):        
            return arithmetic.parseString("+".join([str(a),str(b)]),parseAll=True)[0]
        else: return NotImplemented
    def __radd__(a,b):
        global arithmetic
        if isinstance(b,Number):        
            return arithmetic.parseString("+".join([str(a),str(b)]),parseAll=True)[0]
        else: return NotImplemented
    def __eq__(a,b):
        #TODO: HACK!!!
        global parEquation
        if isinstance(b,basestring): return False
        else: return parEquation.parseString(str(a) + "=" + str(b),parseAll=True)[0]
    def __ge__(a,b):
        global parEquation
        #TODO: HACK!!!
        if isinstance(b,basestring): return False
        else: return parEquation.parseString(str(a) + ">=" + str(b),parseAll=True)[0]
    def __le__(a,b):
        global parEquation
        #TODO: HACK!!!
        if isinstance(b,basestring): return False
        else: return parEquation.parseString(str(a) + "<=" + str(b),parseAll=True)[0]
    def getVars( self, predicate=None ):
        raise NotImplementedError( "Implement me!" )
    def getPredicates( self ):
        raise NotImplementedError( "Implement me!" )
    def substitute(self, subdict ):
        raise NotImplementedError( "Implement me!" )
    def groundingTheory(self, index):
        raise NotImplementedError( "Implement me!" )
    def flatten(self):
        return self
    def freeVars(self):
        return self.getVars()

class Logvar: 
    def __init__(self, s,l,t):
        self.name = t[0]
    def __repr__(self):
        return str(self.name)
    def __str__(self):
        return self.__repr__()

class Constant: 
    def __init__(self, s,l,t):
        self.name = t[0]
    def __repr__(self):
        return str(self.name)
    def __str__(self):
        return self.__repr__()

number = pp.Regex(r"[+-]?\d+\.\d*([eE][+-]?\d+)?") | pp.Word(pp.nums)

plus  = pp.Literal( "+" )
minus = pp.Literal( "-" )
mult  = pp.Literal( "*" )
addop  = (plus | minus)

LPAR  = pp.Literal( "(" )
RPAR  = pp.Literal( ")" )
COMMA  = pp.Literal( "," )
AND  = pp.Literal( "&" )

# ground atoms in a ground term
predicateName = pp.Word(pp.alphanums.lower(),pp.alphanums)

constant = pp.Word(pp.alphanums.lower()) | number

logvar = pp.Word(pp.alphanums.upper(),pp.alphanums)
argument = constant | logvar
arglist = argument + pp.ZeroOrMore( COMMA.suppress() + argument)
atom = predicateName + LPAR.suppress() + pp.Optional(arglist, default=[]) + RPAR.suppress()

# at = atom.parseString("edge(X,a)")[0]
# print at.getVars()
# at.substitute({'a':'pns'})
# print at

# groundFunction=predicateName + LSPAR + pp.Optional(groundArglist, default=[]) + RSPAR
# parameterized term
operand = number | atom
monomial = operand + pp.ZeroOrMore(mult.suppress() + operand)
sumParTerm = pp.Forward()
term = sumParTerm | monomial
arithmetic = term + pp.ZeroOrMore(addop + term)




class Predicate: 
    def __init__(self,name,arity):
        self.name = name
        self.arity = arity
    def __call__(self,*args):
        global arglist
        if len(args) != self.arity:
            raise TypeError("{} takes exactly {} arguments, you supplied {}.".format(self.name, self.arity, len(args)))

        argparse = arglist.parseString(",".join(args)).asList()
        return Atom(0,0,[self.name] + argparse)
    def __repr__(self):
        return self.name + "/" + str(self.arity)
    def __str__(self):
        return self.__repr__()

class Substitution(Predicate):
    def __ilshift__(self, b): 
        self.myterm = b[1]
        if not isinstance(self.myterm, Term):
            raise TypeError("The expression must be a term.")
        self.args = arglist.parseString(b[0]).asList()
        if len(self.args) != self.arity:
            raise TypeError("{} takes exactly {} arguments, you supplied {}.".format(self.name, self.arity, len(self.args)))
        return self
    def __call__(self, *args):
        if len(args) != self.arity:
            raise TypeError("{} takes exactly {} arguments, you supplied {}.".format(self.name, self.arity, len(self.args)))
        subdict = {}
        for ind in range(0,self.arity):
            subdict[str(self.args[ind])] = str(args[ind])
        return self.myterm.substitute(subdict)



class Atom(Term):
    def __init__(self, s,l,t):
        self.args =  t[1:len(t)]
        self.predicate = (t[0],len(self.args))
        self.queried = False
        self.substituted = False
        self.val = "uninit"
    def __repr__(self):
        return (self.predicate[0] + "(" + ",".join([str(u) for u in self.args]) +")") if not self.queried else self.val
    def __str__(self):
        return self.__repr__()
    def __float__(self):
        return float(self.val)
    def __mul__(a,b):
        if isinstance(b,Atom) or isinstance(b,Number):     
            return monomial.parseString("*".join([str(a),str(b)]),parseAll=True)[0]
        else: return NotImplemented
    def __rmul__(a,b):
        if isinstance(b,Number):     
            return monomial.parseString("*".join([str(a),str(b)]),parseAll=True)[0]
        else: return NotImplemented
    def ask(self):
        value = pyDatalog.ask(self.predicate[0] + "(" + ",".join(["'"+str(u)+"'" for u in self.args]) +',Value)')
        if value:
            val = value.answers[0]
            self.val = str(val[0])
        else:
            self.val = "0"    
        self.queried = True
    def groundingTheory(self, index):
        res = self.predicate[0] + "(" + ",".join([str(u) for u in self.args]) +',VAL{})'.format(index) 
        return res


    def forget(self):
        self.val = "uninit"
        self.queried = False
    def getVars(self, pred=None):
        v = []
        for u in self.args:
            if isinstance(u,Logvar):
                v.append(u)
        return v
    def substitute(self,subdict):
        newarglist = []
        global atom
        for ndx, member in enumerate(self.args):
            if subdict.has_key(str(member)): 
                newarglist.append(subdict[str(member)])
            else: newarglist.append( self.args[ndx] )
        newatom = self.predicate[0] + "(" + ",".join([str(u) for u in newarglist]) +")"
        res =  atom.parseString(newatom,parseAll=True)[0]
        # print "res:", res
        return res

class Monomial(Term):
    def __init__(self, s,l,t):
        self.atoms = []
        self.numbers = []
        self.compact = False
        self.queried = False
        for term in t:
            if isinstance(term,Atom): self.atoms.append(term)
            else: self.numbers.append(term) 
    def __repr__(self): 
        numbers = self.numbers
        if self.compact:
            coeff = 1.0
            for n in self.numbers: coeff *= float(n)
            numbers = [coeff]
        return "*".join([str(u) for u in numbers + self.atoms])
    def __str__(self):
        return self.__repr__()
    def __mul__(a,b):     
        return monomial.parseString("*".join([str(a),str(b)]),parseAll=True)[0]
    __rmul__ = __mul__
    def __float__(self):
        coeff = 1.0
        for n in self.numbers: coeff *= float(n)
        return coeff
    def getPredicates(self):
        return set(at.predicate for at in self.atoms)
    def getVars(self, pred=None):
        res = []
        for at in self.atoms:
            if pred is not None:
                if at.predicate != pred: continue 
            res.append(at.getVars())
        return res
    def ask(self,noquery):
        atoms = []
        mypredicates = self.getPredicates()
        query = mypredicates - noquery
        for a in self.atoms:
            if a.predicate in query: 
                a.ask()
                #note: queried atoms become floats in string form -- their
                #str method returns a string of a float, and
                #float(a) now works, returning the queried value.
                #Therefore, unless forget() is called, the code will treat
                #them as numbers from now on.
                self.numbers.append(a)
            else:
                atoms.append(a)
        self.atoms = atoms
        self.queried = True
    def groundingTheory(self,index):
        rhs = []
        if len(self.numbers) == 0: lhs = "1.0"
        else: lhs = "*".join([str(n) for n in self.numbers])

        if len(self.atoms) == 0: return ["mon{}".format(index) + "(" + "{}" + "," + lhs + ")" , "" ]

        for ndx,at in enumerate(self.atoms):
            rhs.append(at.groundingTheory(ndx+index+1))
            lhs += "*VAL{}".format(ndx+index+1)
        varss = set([])
        v = self.getVars()
        for vv in v: varss |= set(vv)
        return ["mon{}".format(index) + "(" + ",".join([str(u) for u in varss]) + "," + lhs + ")", "&".join(rhs)]

    def forget(self):
        numbers = []
        #when we forget, an atom that was treated as a number 
        #reverts back to its "atom" state. C.f. ask()
        for n in self.numbers: 
            if isinstance(n,Atom): 
                n.forget()
                self.atoms.append(n)
            else:
                numbers.append(n)
        self.numbers = numbers
        self.queried = False
    def setCompact(self):
        self.compact = True
        return self
    def unsetCompact(self):
        self.compact = False
        return self
    def switchSign(self):
        return monomial.parseString("-1.0*"+str(self),parseAll=True)[0]
    def isNumeric(self):
            return len(self.atoms)==0
    def substitute(self,subdict):
        newatoms = []
        for at in self.atoms:
            newatoms.append( at.substitute(subdict) )
        #TODO: it could happen that after substitution an atomic becomes numeric 
        return Monomial(0,0,self.numbers + newatoms)
    def getCoefficients(self,predicates):
        newatoms = []
        newnumbers = list(self.numbers)
        if len(newnumbers) == 0: newnumbers.append(Constant(0,0,"1.0"))  

        if len(self.atoms) == 1:
            newatoms.append(atom.parseString("one("+",".join([str(u) for u in self.atoms[0].args]) +")",parseAll=True)[0])
        else:    
            for at in self.atoms:
                if not at.predicate in predicates:
                    newatoms.append(at)

        return Monomial(0,0,newnumbers+newatoms).setCompact()


class Arithmetic(Term):
    def __init__(self, s,l,t):
        self.numeric = []
        self.atomic = []
        self.compact = False
        for i in range(0,len(t)):
            if isinstance(t[i],Monomial) or isinstance(t[i],Parsum):
                if t[i].isNumeric(): self.numeric.append(t[i])
                else: self.atomic.append(t[i])
            else:
                if str(t[i]) == "-":
                    t[i+1] = t[i+1].switchSign()
    def __repr__(self): 
        numeric = self.numeric
        if self.compact:
            coeff = 0.0
            for n in self.numeric: coeff += float(n)
            numeric = [coeff]

        return " + ".join([str(u) for u in self.atomic + numeric])
    def __str__(self):
        return self.__repr__()
    def getVars(self, pred = None):
        res = []
        for at in self.atomic:
            if pred in at.getPredicates():
                res.append(at.getVars(pred = pred))
        return res
    def getPredicates(self):
        res = set([])
        for t in self.atomic:
            if isinstance(t,Monomial): res = res.union(t.getPredicates())
        return res
    def setCompact(self):
        self.compact = True
        for am in self.atomic + self.numeric: am.setCompact()
    def unsetCompact(self):
        self.compact = False
        for am in self.atomic + self.numeric: am.unsetCompact()
    def ask(self,noquery):
        atomic = []
        #note: the idea here is the same as in monomial.ask()
        #after querying all atoms in the atomic monomial may disappear,
        #hence, it becomes a number
        for am in self.atomic:
            am.ask(noquery)
            if am.isNumeric(): self.numeric.append(am)
            else: atomic.append(am)
        self.atomic = atomic
    def forget(self):
        #revert the numerics
        numeric = []
        for m in self.atomic: m.forget()
        for m in self.numeric:
            m.forget()
            if m.isNumeric():
                numeric.append(m)
            else: self.atomic.append(m)
    def isNumeric(self):
        return len(self.atomic) == 0
    def switchSign(self):
        tmp = []
        for m in self.atomic + self.numeric:
            tmp.append(m.switchSign())
        tmpstr = " + ".join([str(u) for u in tmp])
        return arithmetic.parseString(tmpstr, parseAll=True)[0] 
    def substitute(self,subdict):
        newatomic = []
        for at in self.atomic:
            # print at
            # print at.substitute(subdict)
            newatomic.append( at.substitute(subdict) )
        # exit()
        #TODO: it could happen that after substitution an atomic becomes numeric 
        return Arithmetic(0,0,self.numeric + newatomic)
    def flatten(self):
        res = ""
        res += "+".join([str(v) for v in self.numeric])
        p = ""
        if len(self.atomic) > 0 and len(self.numeric) > 0 : p = "+"  
        res += p + "+".join([str(v.flatten()) for v in self.atomic])
        return arithmetic.parseString(res, parseAll=True)[0]
    def getCoefficients(self, predicates):
        res = ""
        res += "+".join([str(v) for v in self.numeric])
        p = ""
        if len(self.atomic) > 0 and len(self.numeric) > 0 : p = "+"    
        res += p + "+".join([str(v.getCoefficients(predicates)) for v in self.atomic])


        return arithmetic.parseString(res, parseAll=True)[0]

    def groundingTheory(self, index):
        res = []
        for ndx, at in enumerate(self.atomic + self.numeric):
            res.append(at.groundingTheory(index + ndx*30))
        return res

    def reduceVars(self, predicate):
        newvarlist = ["TMPVAR{}".format(u) for u in range(0,predicate[1])]
        t = []
        for at in self.atomic:
            v = at.getVars(predicate)[0][0]
            subdict = {}
            for ndx, logvar in enumerate(v):
                subdict[str(logvar)] = newvarlist[ndx]
            t.append(at.substitute(subdict))
        res = "+".join([str(tt) for tt in t])
        return arithmetic.parseString(res, parseAll=True)[0]

    



class Parsum(Term):
    def __init__(self, s,l,t):
        self.terms = t
        self.qvars = t[1]
        self.query = t[2]
        self.expr = t[3]

    def __getitem__(self,index):
        return self.terms[index]
    def __eq__(self,a):
        if a == "sum": return True
        else: return False
    def __repr__(self):
        return "sum {" + ",".join([str(v) for v in self.qvars]) + " in " + str(self.query) + "} : {" + str(self.expr) + "}"
    __str__ = __repr__

    def isNumeric(self):
        return self.expr.isNumeric()
    def switchSign(self):
        tmpstr = "sum {" + ",".join([str(v) for v in self.qvars]) + " in " + str(self.query) + "} : {" + str(self.expr.switchSign()) + "}"
        return sumParTerm.parseString(tmpstr, parseAll=True)[0]
    def setCompact(self):
        self.expr.setCompact()
    def getPredicates(self):
        return self.expr.getPredicates()
    def substitute(self,subdict):
        # print self.terms
        # t = self.terms[:]
        # print t
        # t.append(self.terms[3].substitute(subdict))
        # print t
        #TODO: something terrible happens in the commented code
        # figure out why???
        global sumParTerm
        #TODO: this should be done properly 
        # print subdict
        qstring = str(self.query) 
        varlist = ",".join([str(v) for v in self.qvars])
        for u in subdict.keys():
            qstring = qstring.replace(str(u), str(subdict[u]))
            varlist = varlist.replace(str(u), str(subdict[u]))
        newsum = "sum {" + varlist + " in " + qstring + "}:{" + str(self.expr.substitute(subdict)) + "}"
        #TODO: could we have substitution in the variable query??
        return sumParTerm.parseString(newsum,parseAll=True)[0]
    def flatten(self):
        res = []
        flatexpr = arithmetic.parseString(str(self.expr.flatten()), parseAll=True)[0]
        for term in flatexpr.numeric + flatexpr.atomic:
            tmpvars = []
            tmpqueries = [str(self.query)] 
            if isinstance(term,Parsum):
                tmpvars += [str(v) for v in term.qvars]
                tmpqueries.append(str(term.query))
                termstr = str(term.expr)
            else: termstr = str(term)

            flatstr = "sum {" + ",".join([str(v) for v in list(self.qvars) + tmpvars])
            flatstr += " in " + "&".join(tmpqueries) 
            flatstr += "}:{ " + termstr + "}"
            res.append(flatstr)

        return arithmetic.parseString("+".join(res), parseAll=True)[0]
    def getVars(self, pred=None):
        return self.expr.getVars(pred = pred)

    def getCoefficients(self, predicates):
        newsum = "sum {" + ",".join([str(v) for v in self.qvars]) + " in " + str(self.query) + "}:{" + str(self.expr.getCoefficients(predicates)) + "}"
        #TODO: could we have substitution in the variable query??
        return sumParTerm.parseString(newsum,parseAll=True)[0]

    def groundingTheory(self, index):
        [lhs, rhs] = self.expr.groundingTheory(index)[0]
        if len(rhs) == 0: p = str(self.query)
        else: p =  str(self.query) + "&" + rhs
        return [lhs, p]



class Parequation:
    def __init__(self, s,l,t):
        global arithmetic
        self.lhs = t[0]
        self.sense = t[1]
        self.rhs = t[2]
        if not self.rhs.isNumeric():
            self.lhs = arithmetic.parseString(" - ".join([str(self.lhs),str(self.rhs)]),parseAll=True)[0]
            self.rhs = arithmetic.parseString("0.0",parseAll=True)[0]
    def __getitem__(self,index):
        return self.lhs
    def __repr__(self):
        return str(self.lhs) + " " + self.sense + " " + str(self.rhs)
    __str__ = __repr__

    def isNumeric(self):
        return self.terms[3].isNumeric()
    def switchSign(self):
        self.terms[3].switchSign()
    def setCompact(self):
        self.terms[3].setCompact()


def psum(query, arit):
    return arithmetic.parseString("sum {" + query + "} : {" + str(arit) +"}",parseAll=True)[0]
def pall(query, pareq):
    print "forall {" + query + "} : {" + str(pareq) + "}" 
    return reloopConstraint("forall {" + query + "} : {" + str(pareq) + "}" )  
def pobj(pareq):
    print "objective {" + str(pareq) + "}" 
    return reloopConstraint(str(pareq))

constant.setParseAction(lambda s,l,t: Constant(s,l,t))
logvar.setParseAction(lambda s,l,t: Logvar(s,l,t))
atom.setParseAction(lambda s,l,t: Atom(s,l,t))
monomial.setParseAction(lambda s,l,t: Monomial(s,l,t))
arithmetic.setParseAction(lambda s,l,t: Arithmetic(s,l,t))

literal =  ("~"+atom) | atom
query = pp.Combine((literal + pp.ZeroOrMore(AND + literal)), adjacent=False )

SUM  = pp.Literal( "sum" )
logVarList = (logvar + pp.ZeroOrMore( COMMA.suppress() + logvar)).setParseAction(lambda t : t.asList())
IN  = pp.Literal( "in" ).suppress()
COLON  = pp.Literal( ":" ).suppress()
LCPAR  = pp.Literal( "{" ).suppress()
RCPAR  = pp.Literal( "}" ).suppress()

# parameterized sum
sumParTerm << SUM + LCPAR + pp.Group(logVarList) + IN + query + RCPAR + COLON + LCPAR + arithmetic + RCPAR
sumParTerm.setParseAction(lambda s,l,t: Parsum(s,l,t))

# p = Predicate("testy",3)
# atom1 = p('a','b','x')
# print atom1.groundingTheory(5)

# atom2 = p('x','y','x')
# print atom2*5.0
# print 5.0*atom1
# mon = -5.0*atom1
# print (mon*atom2).substitute({"x":"muffins"})
# print mon*atom2
# art = mon*atom2 + 3.0
# print art
# art = art + 3.14 + atom1
# print art
# art.setCompact()
# print art
# exit()


# p('e','f','g')

# mon = monomial.parseString("edge(X,Y)*3.0*2.5*test(a,b)*-1.0",parseAll=True)[0]
# print mon
# print mon.groundingTheory(5)
# exit()
# query = set([("edge",2)])
# mon.ask(query)
# print mon
# mon.setCompact()
# print mon
# mon.unsetCompact()
# print mon
# mon.forget()
# print mon
# print "predicates: " + str(mon.getPredicates())
# print "variables: " + str(mon.getVars())
# mon.substitute({"X":"something"})
# print mon
# exit()
# art = arithmetic.parseString("edge(X,Y)*cost(Y,X)*1.0*2.5",parseAll=True)[0]

# print art
# print art.getCoefficient(set([("cost",2)]))
# art.ask(set([("test",2)]))
# print art
# art.setCompact()
# print art
# art.forget()
# print art
# art.unsetCompact()
# print art
# exit()


# logical query
# only conjunctions for now
# input = "sum { X,Y in ~edge(a,X) & edge(Y,X) } : { 1*flow(X)*cost(X,Y) + sum { Z in s(Z) }:{ 3*flow(Z) } } + 5"
# result = arithmetic.parseString(input,parseAll=True)[0]
# print result 
# t = result.flatten()
# print t
# t = t.reduceVars(("flow",1))
# print t
# c = t.getCoefficients(set([("flow",1)]))
# print c
# dlg = c.groundingTheory(3)
# for d in dlg:
#     print d[0],":-", d[1]
# edge = Predicate("edge",2)
# flow = Predicate("flow",1)
# print psum("X,Y in ~edge(a,X) & edge(Y,X)", flow("X")*edge("X","Y") + 3) + 5



rlobjective = pp.Group(sumParTerm) ^ ( pp.Group(sumParTerm) + pp.Combine(addop + arithmetic, adjacent=False )) ^ pp.Combine(arithmetic, adjacent=False )
# input = "sum{ Y in edge(Y,X) } : { 1*flow(Y,X) } - 1*inFlow(b)"
#input = "sum{ X,Y in edge(X,Y) } : { cost[X,Y]*flow(X,Y) }"
#input = "sum{ X,Y in source(X) & edge(X,Y) } : { time[X,Y]*use(X,Y) }"
# result = rlobjective.parseString(input,parseAll=True)
# print result
# exit()
FORALL  = pp.Literal( "forall" )
EQ  = pp.Literal( "=" )
LEQ  = pp.Literal( "<=" )
GEQ  = pp.Literal( ">=" )

parEquation = arithmetic + (LEQ ^ GEQ ^ EQ ) + arithmetic
parEquation.setParseAction(lambda s,l,t: Parequation(s,l,t))

# input = "sum{ Y in edge(Y,X) } : { 1*flow(Y,X) } - 1*inFlow(X) = 0"
# result = parEquation.parseString(input,parseAll=True)
# print result
# input = "sum{ Y in edge(Y,X) } : { 1*flow(Y,X) } = inFlow(X)"
# result = parEquation.parseString(input,parseAll=True)


rlconstraint = pp.Group(FORALL + LCPAR + pp.Group(logVarList) + IN + query) + RCPAR + COLON + LCPAR + parEquation + RCPAR

#input = "forall{ X,Y in node(X)&node(Y) } : { sum{ Y in edge(Y,X)&edge(Y,X) } : { 1*flow(Y,X) } - 1*inFlow(X) = 0}"
#input = "sum{ X,Y in edge(X,Y) } : { 1*flow(Y,X) } -1 = 0"
#result = rlconstraint.parseString(input,parseAll=True)
#print result
# THIS IS A HACK, SHOULD DONE PROPERLY
lastterm = arithmetic + (LEQ ^ GEQ ^ EQ ) + number

SLASH = pp.Literal( "/" )
lppreddeclartion = predicateName + pp.Suppress(SLASH) + pp.Word(pp.nums)
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
        self.Query = 'constraint(' + ','.join([str(u) for u in LogVars]) + ')'
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
        #we keep track of which predicates occur in this constraint
        self.predicates = set([])
        if (String.startswith('forall')):
            #a forall constraint
            result = rlconstraint.parseString(String,parseAll=True).asList()
            for token in result:
                if token[0] == 'forall':
                    forall = token[1:]
                elif isinstance(token,Parequation):
                    lhs = token.lhs
                    #extract predicates from arithmetic
                    self.predicates |= token[3].getPredicates()
                    tail = []
                    for t in lhs.numeric + lhs.atomic:
                        if isinstance(t,Parsum):
                            self.tokens.append(reloopSum(t[1],t[2],t[3]))
                        else: tail.append(t)
                    if token.sense == '<=': self.sense = -1
                    elif token.sense == '>=': self.sense = 1
                    else: self.sense = 0\
                    # TODO: ugly!!!!
                    pad = ""
                    if len(tail) == 0: pad = "+0.0"
                    tail = pad + " + ".join([str(t) for t in tail]) + token.sense + str(token.rhs)
                    # print tail
                    # print tail
                    #keep track of predicates
                    tmp = lastterm.parseString(tail,parseAll=True)
                    # self.predicates |= tmp[0].getPredicates()
                    self.tokens[:0]= [reloopForAll(forall[0],forall[1],tail,self.sense)]

        elif (String.startswith('sum')):
            #a sum constraint

            if ("<=" in String) or (">=" in String) or ("=" in String):
                # a "forall" constraint with no query

                result = rlconstraint.parseString(String,parseAll=True).asList()
                print result
                exit()
                forall= [[],'True']

                for token in result:
                    if ("<=" in token) or (">=" in token) or ("=" in token):

                        if '<=' in token:
                            self.sense = -1
                        elif '>=' in token:
                            self.sense = 1
                        else:
                            self.sense = 0
                        #keep track of predicates
                        tmp = lastterm.parseString(token,parseAll=True)
                        self.predicates |= tmp[0].getPredicates()

                        self.tokens[:0]= [reloopForAll(forall[0],forall[1],token,self.sense)]
                    else:
                        print token
                        token = token[0]
                        print token
                        # a sum token
                        #keep track of predicates
                        self.predicates |= token[3].getPredicates()
                        self.tokens.append(reloopSum(token[1],token[2],token[3]))

            else:
                # it is the objective
                result = rlobjective.parseString(String,parseAll=True).asList()
                self.sense = -2

                for token in result:
                    token = token[0]
                    #keep track of predicates
                    self.predicates |= token[3].getPredicates()
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
        self.myRLPVars = set([])
        self.functions = set([])

    def __iadd__(self, value) :
        if isinstance(value,reloopConstraint):
            self.addConstraint(value)
            return self
        else: return NotImplemented

    def __str__(self):
        return '%s' % self.lpmodel

    def name(self):
        return self.name

    def printModel(self):
        print self.lpmodel

    def writeModel(self,filename):
        self.lpmodel.writeLP(filename)


    def solve(self):
        self.lpmodel.solve()

    def status(self):
        return lp.LpStatus[self.lpmodel.status]

    def printLpVars(self):
        for key, value in self.myLpVars.iteritems():
            print key+" = "+str(value)
    
    def predicate(self, name, arity, var=False):
       if var: self.myRLPVars |= set([(name, arity)])
       return Predicate(name, arity)


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

        answer = answer.replace("- -","+")
        answer = answer.replace("+ -","-")
        answer = answer.replace("+ +","+")
        answer = answer.replace("- +","-")
        answer = answer.replace(" + "," +")
        answer = answer.replace(" - "," -")
        # exit()


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
                index = 0
                for var in forAll.logVars():
                    clause = clause.replace(str(var),"'"+ansForAll[index]+"'")
                    query = query.replace(str(var),ansForAll[index])
                    term = str(term).replace(str(var),ansForAll[index])
                pyDatalog.load(clause)
                sumAns = pyDatalog.ask(query)
                pyEngine.Pred.reset_clauses(pyEngine.Pred("constraint",arity))
                if sumAns:
                    for ans in sumAns.answers:
                        term2 = term
                        index = 0
                        for var in Sum.logVars():
                            term2 = term2.replace(str(var),ans[index])
                            index += 1
                        termSum  = termSum + '+' + term2

            if not termSum == '':
                termSum = termSum[1:]
            answer  = lhs
            index = 0
            for var in forAll.logVars():
                answer = answer.replace(str(var),ansForAll[index])
                index += 1
            
            if str(termSum) != "":
                answer = '+'.join([str(termSum), str(answer)])
            else: answer = str(answer)
            parse = arithmetic.parseString(answer,parseAll=True)[0]
            parse.ask(self.myRLPVars)
            parse.setCompact()
            answer = str(parse)

            # atom.setParseAction(lambda s,l,t: Atom(s,l,t))
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
                    term2 = str(term)
                    index = 0
                    for var in Sum.logVars():
                        term2 = term2.replace(var,ans[index])
                        index += 1
                    termSum  = termSum + '+' + term2

        if not termSum == '':
            termSum = termSum[1:]
        parse = arithmetic.parseString(termSum ,parseAll=True)[0]
        parse.ask(self.myRLPVars)
        parse.setCompact()
        answer = str(parse)
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
                    term2 = str(term)
                    index = 0
                    for var in Sum.logVars():
                        term2 = term2.replace(str(var),str(ans[index]))
                        index += 1
                    termSum  = termSum + '+' + term2

        if not termSum == '':
            termSum = termSum[1:]

        parse = arithmetic.parseString(termSum ,parseAll=True)[0]
        parse.ask(self.myRLPVars)
        parse.setCompact()
        answer = str(parse)
        # answer = self.replaceFunctionCalls(termSum)


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



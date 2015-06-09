from sympy import srepr, simplify, sstr
from sympy.core import *
from sympy.logic.boolalg import *
from infix import or_infix


class RlpProblem():
    """
    The model of a Relational Linear Program.
    """
    def __init__(self, name, sense, logkb, lp):
        """
        Instantiates the model

        :param name: The name of the problem, describing it
        :param sense: LpMaximize or LpMinimize
        :param logkb: An instance of :class:`.logkb.LogKB`
        :param lp: A type of :class:`lp.LpProblem`
        """
        self.lpmodel = lp(name, sense)
        self.logkb = logkb
        self.name = name
        self._reloop_variables = set([])
        self._constraints = []
        self.objective = None

    def add_reloop_variable(self, *predicates):
        """
        Introduces predicates as lp variables. These predicate wont be grounded.

        :param predicates: A tuple of predicates to be added to the model
        """
        for predicate in predicates:
            self._reloop_variables |= {(predicate.name, predicate.arity)}

    @property
    def reloop_variables(self):
        return self._reloop_variables

    @property
    def constraints(self):
        return self._constraints

    def __iadd__(self, rhs):
        """
        Adds the objective or a constraint to the model.

        :param rhs: Either an instance of :class :`Expr` (objective) or an instance of Rel or ForAllConstraint (constraint)
        :return: The class instance itself
        """

        if is_valid_relation(rhs) | isinstance(rhs, ForAll):
            self._constraints += [rhs]
        elif isinstance(rhs, Expr):
            self.objective = rhs
        else:
            raise ValueError("'rhs' must be either an instance of sympy.Rel, sympy.Expr or an instance of "
                             "ForallConstraint!")

        return self

    def solve(self):
        """
        Grounds and solves the logical programm.
        """
        self.ground_into_lp()
        self.lpmodel.solve()

    def status(self):
        """
        Passes the call to self.lpmodel
        :return: The solution status of the LP.

        """
        return self.lpmodel.status()

    def get_solution(self):
        """
        Passes the call to self.lpmodel

        :return: The solution of the LP
        """
        return self.lpmodel.get_solution()

    def ground_into_lp(self):
        """
        Ground the RLP by grounding the objective and each constraint.
        """
        self.add_objective_to_lp(self.ground_expression(self.objective))

        for constraint in self.constraints:
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

    def ground_expression(self, expr):
        """
        Recursively grounds any sympy expression, :class:`.RlpSum`, :class:`.RlpPredicate`, ...

        :param expr: The expression which is to be grounded
        :return: A grounded expression
        """
        if expr.func in [Mul, Add, Pow]:
            return expr.func(*map(lambda a: self.ground_expression(a), expr.args))

        if expr.func is RlpSum:
            result = expr.ground(self.logkb)
            return self.ground_expression(result)

        if isinstance(expr, NumericPredicate):
            if (expr.name, expr.arity) not in self.reloop_variables:
                return expr.ground(self.logkb)

        if expr.func is BooleanPredicate:
            # TODO Evaluate to 0 or 1? Did Martin say: that would be cool?
            raise ValueError("RlpBooleanPredicate is invalid here!")

        return expr

    def add_objective_to_lp(self, objective):
        """
        Adds a grounded objective to the LP

        :param objective: A grounded expression (the objective)
        """
        print "Add objective: " + str(objective)
        # + "\n" + srepr(objective)
        expr = objective
        if objective.func is Add:
            for s in objective.args:
                if s.is_Atom:
                    expr -= s

        self.lpmodel += expr

    def add_constraint_to_lp(self, constraint):
        """
        Adds a grounded constraint to the LP

        :param constraint: The grounded constraint.
        """
        print "Add constraint: " + str(constraint)
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

    def __str__(self):
        asstr = "Objective: "
        asstr += srepr(self.objective)
        asstr += "\n\n"
        asstr += "Subject to:\n"
        for c in self._constraints:
            asstr += srepr(c)
            asstr += "\n"
        return asstr


class Query:
    """
    Internal representation of a logical query.
    """
    def __init__(self, query_symbols, query):
        """
        :param query_symbols: List of type :class:`SubSymbol`
        :param query: A logical query
        """
        self._query_symbols = query_symbols
        self._query = simplify(query)

    @property
    def query_symbols(self):
        return self._query_symbols

    @property
    def query(self):
        return self._query


class ForAll(Query):
    """
    Wraps a :class:`.Query` and a :class:`.Rel` to represent a set of constraints.
    """
    def __init__(self, query_symbols, query, relation):
        Query.__init__(self, query_symbols, query)
        if not is_valid_relation(relation):
            raise ValueError("Third argument has to be a valid relation.")
        self.relation = relation
        self.result = []
        self.grounded = False

    def ground(self, logkb):
        """
        Grounds the query and relation

        :param logkb: An implementation of a Logical Knowledge Base
        :type logkb: :class:`.LogKB`
        :return: A set of grounded constraints
        """
        answers = logkb.ask(self.query_symbols, self.query)

        result = set([])
        if answers is not None:
            lhs = self.relation.lhs - self.relation.rhs
            for answer in answers:
                    expression_eval_subs = lhs
                    for index, symbol in enumerate(self.query_symbols):
                        expression_eval_subs = expression_eval_subs.subs(symbol, answer[index])
                    result |= {self.relation.__class__(expression_eval_subs, 0.0)}

        self.result = result
        self.grounded = True
        return self.result

    def __str__(self):
        return "FORALL " + str(self.query_symbols) + " in " + str(self.query) + ": " + srepr(self.relation)


class SubSymbol(Symbol):
    """
    Just a sympy.Symbol, but inherited to be able to define symbols explicitly
    """
    pass


def sub_symbols(*symbols):
    """
    Convenience function for instantiating multiple :class:`.SubSymbol` at once.

    :param symbols: Tuple of strings
    :return: Tuple of SubSymbols
    """
    return tuple(map(lambda s: SubSymbol(s), symbols))


def boolean_predicate(name, arity):
    """
    Convenience function for generating a :class:`BooleanPredicate` type

    :param name: Name of the predicate
    :param arity: Arity (must match count of relation elements)
    :return: A type with the given name, inherited from :class:`BooleanPredicate`
    """
    return rlp_predicate(name, arity, boolean=true)


def numeric_predicate(name, arity):
    """
    Convenience function for generating a :class:`NumericPredicate` type

    :param name: Name of the predicate
    :param arity: Arity (count of relation elements decremented by one)
    :return: A type with the given name, inherited from :class:`NumericPredicate`
    """
    return rlp_predicate(name, arity, boolean=false)


def rlp_predicate(name, arity, boolean):
    if arity < 0:
        raise ValueError("Arity must not be less than 0. Dude!")
    if arity == 0 & boolean:
        raise ValueError("Arity must not be less than 1, if boolean is true. Dude!")

    if arity == 0:
        predicate_type = RlpPredicate
    elif boolean:
        predicate_type = BooleanPredicate
    else:
        predicate_type = NumericPredicate
    predicate_class = type(name, (predicate_type,), {"arity": arity, "name": name, "result": None,
                                                                         "grounded": False})
    return predicate_class

class RlpPredicate(Expr):
    pass

class NumericPredicate(RlpPredicate, Function):
    """
    Representing a predicate that is understood as a function. That is, though the relation :math:`R` inside the LogKB
    has :math:`k` elements, we define :math:`R(e_1, ..., e_{k-1}) := e_{k}`.
    """
    @classmethod
    def eval(cls, *args):
        if not cls.grounded:
            return None
        return cls.result

    def ground(self, logkb):
        """
        Grounds itself

        :param logkb: An implementation of a Logical Knowledge Base
        :type logkb: :class:`.LogKB`
        :return: The :math:`e_{k}` th element
        """
        args = self.args
        if len(args) > self.arity:
            raise Exception("Too many arguments.")

        if len(args) < self.arity:
            raise Exception("Not enough arguments")

        for argument in args:
            if isinstance(argument, SubSymbol):
                raise ValueError("Found free symbols while grounding: " + str(self))

        answers = logkb.ask_predicate(self)
        if answers is None:
            raise ValueError('Predicate is not defined or no result!')

        if len(answers) != 1:
            raise ValueError("The LogKb gives multiple results. Oh!")

        result = answers.pop()
        self.result = result
        self.grounded = True
        return float(result[0])


    @classmethod
    def __str__(cls):
        return '%s/%s' % (cls.name, cls.arity)

    __repr__ = __str__


class BooleanPredicate(BooleanAtom, Function):
    """
    A Predicate to use in boolean expressions; can be used like a function inside boolean terms.
    """
    pass


class RlpSum(Expr, Query):
    """

    """
    def __init__(self, query_symbols, query, expression):
        Query.__init__(self, query_symbols, query)
        if not isinstance(expression, Expr):
            raise ValueError("The third argument was not an sympy.core.Expr!")
        if isinstance(expression, Rel):
            raise ValueError("You cannot use a sympy.core.Rel instance here!")
        self.expression = expression
        self.result = None
        self.grounded = False

    def ground(self, logkb):
        """
        Grounds the query and expression

        :param logkb: An implementation of a Logical Knowledge Base
        :type logkb: :class:`.LogKB`
        :return: An summation of the grounded expressions
        """
        answers = logkb.ask(self.query_symbols, self.query)
        result = Float(0.0)
        for answer in answers:
                expression_eval_subs = self.expression
                for index, symbol in enumerate(self.query_symbols):
                    expression_eval_subs = expression_eval_subs.subs(symbol, answer[index])
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

@or_infix
def eq(a, b):
    return Eq(a, b)

@or_infix
def ge(a, b):
    return Ge(a, b)

@or_infix
def le(a, b):
    return Le(a, b)

def is_valid_relation(relation):
    if isinstance(relation, Gt) | isinstance(relation, Lt):
        raise NotImplementedError("StrictGreaterThan and StrictLessThan is not implemented!")
    if isinstance(relation, Rel):
        return True
    return False
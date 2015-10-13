from abc import ABCMeta
from sympy.core import Add
from sympy.core.function import expand
from sympy.core import Mul
from sympy.core import Symbol

from reloop.languages.rlp import *
import abc


class ImmutableVisitor():
    """
    Class interfacing a generic visitor used by the Normalizer
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def visit(self, expr):
        raise NotImplementedError("")

    @property
    def result(self):
        return self._result


class Normalizer(ImmutableVisitor):
    """
    Normalizes a given expression by visiting each node in the syntax tree and applying different methods for the different occuring types in the given expression.
    """

    def __init__(self, expr):
        expanded_expr = expand(expr)

        if not expanded_expr.has(RlpSum):
            self._result = expanded_expr

        self._result = self.visit(expanded_expr)

    def visit(self, expr):
        """
        Visits the given expression nodewise and executes methods based on the current node instance

        :param expr: The expression to be visited
        :type expr: Sympy Expression
        :return: A normalized expression
        """
        if not expr.has(RlpSum):
            return expr

        if isinstance(expr, Mul):
            return self.visit_mul(expr)
        elif isinstance(expr, RlpSum):
            return self.visit_rlpsum(expr)
        else:
            args = expr.args
            normalized_args = [self.visit(arg) for arg in args]

            return expr.func(*normalized_args)

    def visit_mul(self, mul):
        """
        Visitor Method, which is called in case the current node is a multiplication

        :param mul: The multiplication node to be processed
        :type mul: Sympy Mul
        :return:
        """
        args = mul.args
        for arg in args:
            arg = self.visit(arg)

        mul = Mul(*args)

        non_rlps = []
        rlpsum = None
        for arg in mul.args:
            if isinstance(arg, RlpSum):
                rlpsum = arg
            else:
                non_rlps.append(arg)
        if rlpsum is not None:
            # If we have a term of the kind a*RlpSum(s,q,e), we return RlpSum(s,q,a*e)
            return RlpSum(rlpsum.query_symbols, rlpsum.query, Mul(*(non_rlps + [rlpsum.expression])))
        else:
            return mul

    def visit_rlpsum(self, rlpsum):
        """
         Visitor Method, which is called in case the current node is a rlpsum

         :param rlpsum:
         :type: rlpsum: rlpsum
         :return:
        """
        expr = self.visit(rlpsum.expression)
        rlpsum = RlpSum(rlpsum.query_symbols, rlpsum.query, expr)

        if expr.func is Add:
            query_symbols = rlpsum.query_symbols
            query = rlpsum.query

            # If sum terms is Add, we create a new RlpSum for each argument and flatten
            return Add(*[RlpSum(query_symbols + u.args[0], query & u.args[1], u.args[2]) if u.func is RlpSum
                         else RlpSum(rlpsum.args[0], rlpsum.args[1], u) for u in expr.args])
        else:
            # If not then probably nothing changed
            return rlpsum


class ExpressionGrounder(ImmutableVisitor):
    """
    Grounds a sympy expression into a set of lp variables and the grounded expression for the recursive grounder
    """

    def __init__(self, expr, logkb):
        self.logkb = logkb
        self.lp_variables = set([])

        expanded_expr = expand(expr)
        self._result = self.visit(expanded_expr)

    def visit(self, expr):
        """
        Recursively visits the syntax tree nodes for the given expression and executes a method based on the current properties of the node in the tree.

        :param expr: The Sympy expression the visitor visits.
        :type expr: Sympy Add|Mul|RlpSum|Pow
        :return: The ground expression
        """
        if expr.func in [Mul, Add, Pow]:
            return expr.func(*map(lambda a: self.visit(a), expr.args))

        if expr.func is RlpSum:
            result = self.visit_rlpsum(expr)
            return self.visit(result)

        if isinstance(expr, NumericPredicate) and not expr.isReloopVariable:
            return self.visit_numeric_predicate(expr)

        if expr.func is BooleanPredicate:
            # TODO Evaluate to 0 or 1? Did Martin say: that would be cool?
            raise ValueError("RlpBooleanPredicate is invalid here!")

        return expr

    def visit_rlpsum(self, rlpsum):
        """
        Visitor Method, which is called in case the current node of the syntax tree is an instance of a rlpsum

        :param rlpsum: The current node, which is an instance of a rlpsum
        :type rlpsum: RLPSum
        :return:
        """
        answers = self.logkb.ask(rlpsum.query_symbols, rlpsum.query)
        result = Float(0.0)
        for answer in answers:
            expression_eval_subs = rlpsum.expression
            for index, symbol in enumerate(rlpsum.query_symbols):
                subanswer = answer[index] if not isinstance(answer[index], basestring) \
                    else Symbol(answer[index])

                expression_eval_subs = expression_eval_subs.subs(symbol, subanswer)
                # expression_eval_subs = expression_eval_subs.subs(symbol, answer[index])
            result += expression_eval_subs

        return result

    def visit_numeric_predicate(self, pred):
        """
        Visitor Method, which is called in case the current node of the syntrax tree for a given expression is a numeric predicate

        :param pred: The numeric predicate to be processed
        :type pred: Numeric Predicate
        :return:
        """
        args = pred.args
        if len(args) > pred.arity:
            raise Exception("Too many arguments.")

        if len(args) < pred.arity:
            raise Exception("Not enough arguments")

        for argument in args:
            if isinstance(argument, SubSymbol):
                raise ValueError("Found free symbols while grounding: " + str(pred))

        answers = self.logkb.ask_predicate(pred)
        if answers is None:
            raise ValueError('Predicate is not defined or no result!')

        if len(answers) != 1:
            raise ValueError("The LogKb gives multiple results. Oh!")

        result = answers.pop()

        return float(result[0].name)


class AffineExpressionCompiler(ImmutableVisitor):
    """
    Grounds a sympy expression into a set of lp variables and the grounded expression
    """

    def __init__(self, expr, logkb):
        self.lp_variables = set([])

        expanded_expr = expand(expr)
        self._result = self.visit(expanded_expr)

    def visit(self, expr):
        """
        Recursively visits the syntax tree nodes for the given expression and executes a method based on the current properties of the node in the tree.

        :param expr: The Sympy expression the visitor visits.
        :type expr: Sympy Add|Mul|RlpSum|Pow
        :return: The ground expression
        """
        if expr.func in [Mul, Add, Pow]:
            return expr.func(*map(lambda a: self.visit(a), expr.args))

        if isinstance(expr, NumericPredicate):
            if not expr.isReloopVariable:
                raise ValueError("Not fully grounded")
            else:
                self.lp_variables.add(sstr(expr))

        if expr.func is BooleanPredicate:
            # TODO Evaluate to 0 or 1? Did Martin say: that would be cool?
            raise ValueError("RlpBooleanPredicate is invalid here!")

        return expr

    def visit_rlpsum(self, rlpsum):
        """
        Visitor Method, which is called in case the current node of the syntax tree is an instance of a rlpsum

        :param rlpsum: The current node, which is an instance of a rlpsum
        :type rlpsum: RLPSum
        :return:
        """
        answers = self.logkb.ask(rlpsum.query_symbols, rlpsum.query)
        result = Float(0.0)
        for answer in answers:
            expression_eval_subs = rlpsum.expression
            for index, symbol in enumerate(rlpsum.query_symbols):
                subanswer = answer[index] if not isinstance(answer[index], basestring) \
                    else Symbol(answer[index])

                expression_eval_subs = expression_eval_subs.subs(symbol, subanswer)
                # expression_eval_subs = expression_eval_subs.subs(symbol, answer[index])
            result += expression_eval_subs

        return result

    def visit_numeric_predicate(self, pred):
        """
        Visitor Method, which is called in case the current node of the syntrax tree for a given expression is a numeric predicate

        :param pred: The numeric predicate to be processed
        :type pred: Numeric Predicate
        :return:
        """
        args = pred.args
        if len(args) > pred.arity:
            raise Exception("Too many arguments.")

        if len(args) < pred.arity:
            raise Exception("Not enough arguments")

        for argument in args:
            if isinstance(argument, SubSymbol):
                raise ValueError("Found free symbols while grounding: " + str(pred))

        answers = self.logkb.ask_predicate(pred)
        if answers is None:
            raise ValueError('Predicate is not defined or no result!')

        if len(answers) != 1:
            raise ValueError("The LogKb gives multiple results. Oh!")

        result = answers.pop()

        return float(result[0])

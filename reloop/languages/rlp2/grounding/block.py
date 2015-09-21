from grounder import Grounder
from reloop.languages.rlp2 import *
import scipy as sp
import scipy.sparse
import numpy as np
from ordered_set import OrderedSet
import logging

from sympy.sets import EmptySet

log = logging.getLogger(__name__)


class BlockGrounder(Grounder):
    """
    Provides the tools to ground a given RLP (Objective and Contraints) into their respective lp matrices by using
    grounding each contraint and objective into a 'block' of the matrix and then building the whole lp matrix.
    """

    def __init__(self, logkb):
        """
        Initialize the BlockGrounder by creating new row and column dictionaries and a dictionary for the blocks of the
        matrix.
        :param logkb: The knowledge base used for querying expressions
        :return:
        """
        self.logkb = logkb
        self.col_dicts = {}
        self.row_dicts = {}
        self.blocks = {}

    def ground(self, rlpProblem):
        """
        Resets the status of the row and column dictionaries of the BlockGrounder instance and
        grounds the RLP by grounding the objective and each constraint.
        :param rlpProblem: The instance of the given RLP
        :type rlpProblem: rlpProblem
        """

        self.__init__(self.logkb)

        objective = self.objective_to_matrix(rlpProblem.objective)

        for constraint in rlpProblem.constraints:
            log.debug("\nGrounding: \n %s: %s", constraint_str(constraint), str(constraint))
            self.constraint_to_matrix(constraint)

        a = b = g = h = c = None

        for reloop_variable in rlpProblem.reloop_variables:
            shape = (1, len(self.col_dicts[reloop_variable]))
            if objective.has_key(reloop_variable):
                value = objective[reloop_variable]
                value.resize(shape)
            else:
                value = sp.sparse.dok_matrix(shape)

            if c is not None:
                c = sp.sparse.hstack((c, value))
            else:
                c = value

        for constraint in rlpProblem.constraints:
            log.debug("\nAssembling: %s.", constraint_str(constraint))
            constr_matrix = None

            constr_name = constraint_str(constraint)

            for reloop_variable in rlpProblem.reloop_variables:
                log.debug("\n\tkey: %s.", reloop_variable)
                shape = (len(self.row_dicts[constr_name]), len(self.col_dicts[reloop_variable]))
                if reloop_variable in self.blocks[constr_name]:
                    value = self.blocks[constr_name][reloop_variable]
                    value.resize(shape)
                else:
                    value = sp.sparse.dok_matrix(shape)

                if constr_matrix is not None:
                    constr_matrix = sp.sparse.hstack((constr_matrix, value))
                else:
                    constr_matrix = value

            log.debug("\n\tkey: RHS.")
            constr_vector_shape = (len(self.row_dicts[constr_name]), 1)
            if None.__class__ in self.blocks[constr_name]:
                value = self.blocks[constr_name][None.__class__]
                value.resize(constr_vector_shape)
                constr_vector = value
            else:
                constr_vector = sp.sparse.dok_matrix(constr_vector_shape)

            if isinstance(constraint, ForAll):
                rel = constraint.relation
            elif isinstance(constraint, Rel):
                rel = constraint
            else:
                raise RuntimeError("The constraint is neither a relation nor a forall... what is it then?")
            if isinstance(rel, Equality):
                a = constr_matrix if a is None else sp.sparse.vstack((a, constr_matrix))
                b = constr_vector if b is None else sp.sparse.vstack((b, constr_vector))
            else:
                g = constr_matrix if g is None else sp.sparse.vstack((g, constr_matrix))
                h = constr_vector if h is None else sp.sparse.vstack((h, constr_vector))

        # at some point we had lhs = lhs - rhs, so now we have to put b back on the rhs
        c = rlpProblem.sense * c

        if a is not None and b is not None:
            b *= -1
            b = b.todense()
            a = a.tocoo()
        elif (a is not None and b is None) or (b is not None and a is None):
            raise Exception("This is just wrong")

        if g is not None and h is not None:
            h *= -1
            h = h.todense()
            g = g.tocoo()

        lp = c.todense().T, g, h, a, b

        return lp, self.col_dicts

    def objective_to_matrix(self, objective):
        """
        Grounds the objective of the given RLP into the matrix
        :param objective: The objective of the LP from which the corresponding block is generated from.
        """
        var_blocks = self.expr_to_matrix(objective, OrderedSet(), True, EmptySet())
        return var_blocks

    def constraint_to_matrix(self, constraint):
        """
        Generates the corresponding block in the lp matrix from a given constraint and adds the result to the block dictionary.
        :param constraint: The constraint the corresponding block is generated from.
        """
        constr_name = constraint_str(constraint)

        self.row_dicts[constr_name] = OrderedSet()
        row_dict = self.row_dicts[constr_name]

        if isinstance(constraint, Rel):
            lhs = constraint.lhs - constraint.rhs
            constr_query = True
            constr_query_symbols = EmptySet()
            if isinstance(constraint, GreaterThan):
                lhs *= -1
        elif isinstance(constraint, ForAll):
            lhs = constraint.relation.lhs - constraint.relation.rhs
            if isinstance(constraint.relation, GreaterThan):
                lhs *= -1
            constr_query = constraint.query
            constr_query_symbols = constraint.query_symbols
        else:
            raise Exception("Impossible-to-happen Exception!")

        var_blocks = self.expr_to_matrix(lhs, row_dict, constr_query, constr_query_symbols)

        self.blocks[constr_name] = var_blocks

    def expr_to_matrix(self, expr, row_dict, constr_query, constr_query_symbols):
        """
        First normalizes a given expression with a visitor pattern then queries the knowledge base for the given query
        and assigns the results to their respective row and column index defined the the row and column dictionaries.
        :param expr: The expression to be grounded
        :type expr: Sympy Expression| RLPSum
        :param row_dict: An OrderedSet containing the row indices for the lp matrix for the given expression
        :type row_dict: OrderedSet
        :param constr_query: The query originating from a given constraint
        :type constr_query: Sympy Expression | RLPSum
        :param constr_query_symbols: A Set containing the query symbols for the given constraint query
        :type constr_query_symbols FiniteSet
        :return: A dictionary containing a unique name for the variable and the results returned from the knowledge base.
        """
        expr = Normalizer(expr).result

        if not isinstance(expr, Add):
            summands = [expr]
        else:
            summands = expr.args

        result = {}
        log.debug("\nSummands: %s", str(summands))

        for summand in summands:
            log.debug("\n->summand: %s", str(summand))

            if isinstance(summand, RlpSum):
                summand_query = summand.query
                summand_query_symbols = summand.query_symbols
                coef_query, coef_query_symbols, variable = coefficient_to_query(summand.args[2])
            else:
                summand_query = True
                summand_query_symbols = EmptySet()
                coef_query, coef_query_symbols, variable = coefficient_to_query(summand)

            query_symbols = OrderedSet(constr_query_symbols + summand_query_symbols)

            coef_expr = coef_query_symbols if not isinstance(coef_query_symbols, SubSymbol) else None
            query = constr_query & summand_query & coef_query

            answers = self.logkb.ask(query_symbols, query, coef_expr)
            variable_qs_indices = []
            if variable is not None:
                variable_qs_indices = [query_symbols.index(arg) for arg in variable.args if isinstance(arg, SubSymbol)]
            constr_qs_indices = [query_symbols.index(symbol) for symbol in constr_query_symbols]

            variable_class = variable.__class__
            col_dict = self.col_dicts.get(variable_class, OrderedSet())
            self.col_dicts[variable_class] = col_dict

            #If the query yields no results we don't have to add anything to the matrix
            if len(answers) == 0:
                continue
            expr_index = len(answers[0]) - 1
            sparse_data = []
            for answer in answers:
                column_record = []

                # summand has only one predicate

                # the above is actually wrong. We can have multiple
                # predicates, but only one variable. E.g. cost(X,Y)*flow(X,Y)
                # where flow is the variable --MM
                predicate = None
                for predcandidate in summand.atoms(RlpPredicate):
                    if variable.__class__ == predcandidate.__class__:
                        predicate = predcandidate
                        break
                        # use only subsymbols when they occur, otherwise constants

                # this condition breaks everything, we have to think this through
                # --MM
                # if variable is not None and variable is NumericPredicate:
                j = 0
                if predicate is not None:
                    for arg in predicate.args:
                        if isinstance(arg, SubSymbol):
                            # it seems that in this branch it appends non-strings,
                            # whereas in the other, it appends strings, so this
                            # one produces [1,1], whereas the other could produce
                            # ['1',1] for the same atom and thei fail to unify.
                            # I have added an str() to the append -- MM
                            column_record.append(str(answer[variable_qs_indices[j]]))
                            j += 1
                        else:
                            column_record.append(str(arg))

                col_dict_index = col_dict.add(tuple(column_record))
                row_dict_index = row_dict.add(tuple(answer[i] for i in constr_qs_indices))

                sparse_data.append([np.float(answer[expr_index]), row_dict_index, col_dict_index])

            sparse_data = np.array(sparse_data)
            summand_block = sp.sparse.coo_matrix((sparse_data[:, 0], (sparse_data[:, 1], sparse_data[:, 2]))).todok()

            if variable_class in result:
                shape = (len(row_dict), len(col_dict))
                result[variable_class].resize(shape)
                summand_block.resize(shape)
                result[variable_class] += summand_block
            else:
                result[variable_class] = summand_block

        return result


def coefficient_to_query(expr):
    """
    Generates a logkb query from a given expression
    :param expr: the expression the query is generated from
    :type expr: Sympy Expression | RLPSum
    :return: the query as a sympy expression
    """
    if isinstance(expr, RlpPredicate):
        if (expr.isReloopVariable):
            return [True, Float(1.0), expr]
        else:
            val = VariableSubSymbol(variable_name_for_expression(expr))
            b = boolean_predicate(str(expr.func), len(expr.args) + 1)
            return [b(*(expr.args + tuple([val]))), val, None]
    else:
        query = [True, ]
        query_expr = []
        var_atom = None
        if len(expr.args) == 0:
            return [And(*query), expr, var_atom]
        else:
            for arg in expr.args:
                if arg.has(RlpPredicate):
                    [q, e, v] = coefficient_to_query(arg)
                    if v is not None: var_atom = v
                else:
                    q = True;
                    e = arg
                query.append(q);
                query_expr.append(e)
            return [And(*query), expr.func(*query_expr), var_atom]


def variable_name_for_expression(expr):
    """
    Generates a unique identifier for a given expression
    :param expr: The expression for which the identifier is generated.
    :return: A str unique to the given expression (Memory Address)
    """
    return 'VAL' + str(id(expr))


def constraint_str(constraint):
    """
     Generates a unique identifier for a given constraint
    :param constraint: The constraint for which the identifier is generated.
    :return: A str unique to the given expression (Memory Address)
    """
    return 'CONSTR' + str(id(constraint))

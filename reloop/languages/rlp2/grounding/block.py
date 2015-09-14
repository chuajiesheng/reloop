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

    def __init__(self, logkb):
        self.logkb = logkb
        self.col_dicts = {}
        self.row_dicts = {}
        self.O = {}
        self.T = {}

    def ground(self, rlpProblem):
        """
        Ground the RLP by grounding the objective and each constraint.
        """
        self.constraint_to_matrix(rlpProblem.objective, self.col_dicts, self.row_dicts, self.O)
        log.setLevel(1)
        for constraint in rlpProblem.constraints:
            log.debug("\nGrounding: \n %s: %s", constraint_str(constraint), str(constraint))
            self.constraint_to_matrix(constraint, self.col_dicts, self.row_dicts, self.T)

        G = h = A = b = c = None

        for constr_name in self.O.keys():
            for reloop_variable in rlpProblem.reloop_variables:
                key = reloop_variable
                if self.O[constr_name].has_key(key):
                    value = self.O[constr_name][key]
                    value.resize((len(self.row_dicts[constr_name]), len(self.col_dicts[key])))
                else:
                    value = sp.sparse.dok_matrix((len(self.row_dicts[constr_name]), len(self.col_dicts[key])))
                if c is not None:
                    c = sp.sparse.hstack((c, value))
                else:
                    c = value
        #TODO: figure out the precise var mapping at some point.

        for constraint in rlpProblem.constraints:
            log.debug("\nAssembling: %s.", constraint_str(constraint))
            constr_matrix = None
            constr_vector = None
            constr_name = constraint_str(constraint)

            for reloop_variable in rlpProblem.reloop_variables:
                key = reloop_variable
                log.debug("\n\tkey: %s.", key)
                if key in self.T[constr_name]:
                    value = self.T[constr_name][key]
                    value.resize((len(self.row_dicts[constr_name]), len(self.col_dicts[key])))
                else:
                    value = sp.sparse.dok_matrix((len(self.row_dicts[constr_name]), len(self.col_dicts[key])))
                if constr_matrix is not None:
                    constr_matrix = sp.sparse.hstack((constr_matrix, value)) #TODO: this should not be done like that, assign predicate ranges
                else:
                    constr_matrix = value

            log.debug("\n\tkey: RHS.")
            if None.__class__ in self.T[constr_name]:
                value = self.T[constr_name][None.__class__]
                value.resize((len(self.row_dicts[constr_name]), 1))
                constr_vector = value
            else:
                constr_vector = sp.sparse.dok_matrix((len(self.row_dicts[constr_name]), 1))
            
            if isinstance(constraint, ForAll): 
                rel = constraint.relation
            elif isinstance(constraint, Rel):
                rel = constraint
            else:
                raise RuntimeError("The constraint is neither a relation nor a forall... what is it then?")

            if isinstance(rel, Equality):
                G = constr_matrix if G is None else sp.sparse.vstack((G, constr_matrix))
                h = constr_vector if h is None else sp.sparse.vstack((h, constr_vector))
            else:
                A = constr_matrix if A is None else sp.sparse.vstack((A, constr_matrix))
                b = constr_vector if b is None else sp.sparse.vstack((b, constr_vector))

        if b is not None: b = -b #at some point we had lhs = lhs - rhs, so now we have to put b back on the rhs
        if h is not None: h = -h

        c = rlpProblem.sense * c

        lp = c.todense().T, A.tocoo(), b.todense(), G.tocoo(), h.todense()

        return lp, self.col_dicts

    def constraint_to_matrix(self, constraint, col_dicts, row_dicts, block):

        constr_name = constraint_str(constraint)
        block[constr_name] = {}
        row_dicts[constr_name] = OrderedSet()
        row_dict = row_dicts[constr_name]

        if isinstance(constraint, Rel):
            lhs = constraint.lhs - constraint.rhs
            constr_query = True
            constr_query_symbols = EmptySet()
        elif isinstance(constraint, ForAll):
            lhs = constraint.relation.lhs - constraint.relation.rhs
            if isinstance(constraint.relation, GreaterThan):
                lhs *= -1
            constr_query = constraint.query
            constr_query_symbols = constraint.query_symbols
        else:
            lhs = constraint
            constr_query = True
            constr_query_symbols = EmptySet()

        lhs = Normalizer(lhs).result

        if not isinstance(lhs, Add):
            summands = [lhs]
        else:
            summands = lhs.args

        for summand in summands:
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

            answers = self.logkb.ask(query_symbols,  query, coef_expr)

            variable_qs_indices = []
            if variable is not None:
                variable_qs_indices = [query_symbols.index(arg) for arg in variable.args if isinstance(arg, SubSymbol)]
            constr_qs_indices = [query_symbols.index(symbol) for symbol in constr_query_symbols]

            variable_class = variable.__class__
            col_dict = col_dicts.get(variable_class, OrderedSet())
            col_dicts[variable_class] = col_dict

            expr_index = len(answers[0])-1
            sparse_data = []
            for answer in answers:
                column_record = []

                # summand has only one predicate
                predicate = summand.atoms(NumericPredicate).pop()

                # use only subsymbols when they occur, otherwise constants
                if variable is not None:
                    j = 0
                    for arg in predicate.args:
                        if isinstance(arg, SubSymbol):
                            column_record.append(answer[variable_qs_indices[j]])
                            j += 1
                        else:
                            column_record.append(str(arg))

                col_dict_index = col_dict.add(tuple(column_record))
                row_dict_index = row_dict.add(tuple(answer[i] for i in constr_qs_indices))

                sparse_data.append([np.float(answer[expr_index]), row_dict_index, col_dict_index])

            sparse_data = np.array(sparse_data)

            summand_block = sp.sparse.coo_matrix((sparse_data[:, 0], (sparse_data[:, 1], sparse_data[:, 2]))).todok()

            if variable_class in block[constr_name]:
                shape = (len(row_dict), len(col_dict))
                summand_block.resize(shape)
                block[constr_name][variable_class].resize(shape)
                block[constr_name][variable_class] += summand_block
            else:
                block[constr_name][variable_class] = summand_block


def coefficient_to_query(expr):
    """
    TODO: write me tenderly
    """
    if isinstance(expr, NumericPredicate):
        if(expr.isReloopVariable):
            return [True, Float(1.0), expr]
        else:
            val = VariableSubSymbol(variable_name_for_expression(expr))
            b = boolean_predicate(str(expr.func), len(expr.args)+1)
            return [b(*(expr.args+tuple([val]))), val, None]
    else:
        query = [True,]
        query_expr = []
        var_atom = None
        if len(expr.args) == 0:
            return [And(*query), expr, var_atom]
        else:
            for arg in expr.args:
                if arg.has(NumericPredicate):
                    [q, e, v] = coefficient_to_query(arg)
                    if v is not None: var_atom = v
                else:
                    q = True; e = arg
                query.append(q); query_expr.append(e)
            return [And(*query), expr.func(*query_expr), var_atom]


def variable_name_for_expression(expr):
    return 'VAL' + str(id(expr))

def constraint_str(constraint):
    return 'CONSTR'+str(id(constraint))

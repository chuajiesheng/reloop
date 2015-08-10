from grounder import Grounder
from grounder import PostgresqlConnector
from reloop.languages.rlp2 import *
import scipy as sp
import scipy.sparse
import numpy as np

from sympy.sets import EmptySet

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

        self.constraint_to_matrix(rlpProblem, rlpProblem.objective, self.col_dicts, self.row_dicts, self.O)

        for constraint in rlpProblem.constraints:
            self.constraint_to_matrix(rlpProblem, constraint, self.col_dicts, self.row_dicts, self.T)


        print "stiching stuff back together"

        G = h = A = b = c = None

        block_start = 0
        for constr_name in self.O.keys():
            for reloop_variable in rlpProblem._reloop_variables:
                key = "%s/%s" % reloop_variable
                print key
                if not self.col_dicts[key].has_key("range"):
                    self.col_dicts[key]["range"] = block_start
                    block_start += self.col_dicts[key]["count"]
                if self.O[constr_name].has_key(key):
                    value = self.O[constr_name][key]
                    value.resize((self.row_dicts[constr_name]["count"], self.col_dicts[key]["count"]))
                else:
                    value = sp.sparse.dok_matrix((self.row_dicts[constr_name]["count"], self.col_dicts[key]["count"]))

                if c is not None:
                    c = sp.hstack((c, value))
                else:
                    c = value
        #TODO: figure out the precise var mapping at some point.


        for constraint in rlpProblem.constraints:
            constr_matrix = None
            constr_vector = None
            constr_name = 'CONSTR'+str(id(constraint))
            print constr_name

            for reloop_variable in rlpProblem._reloop_variables:
                key = "%s/%s" % reloop_variable

                if not self.col_dicts[key].has_key("range"):
                    self.col_dicts[key]["range"] = block_start
                    block_start += self.col_dicts[key]["count"]

                if self.T[constr_name].has_key(key):
                    value = self.T[constr_name][key]
                else:
                    value = sp.sparse.dok_matrix((self.row_dicts[constr_name]["count"], self.col_dicts[key]["count"]))
                if constr_matrix is not None:
                    value.resize((self.row_dicts[constr_name]["count"], self.col_dicts[key]["count"]))
                    constr_matrix = sp.hstack((constr_matrix, value)) #TODO: this should not be done like that, assign predicate ranges
                else:
                    constr_matrix = value
            if self.T[constr_name].has_key("b_vec"):
                value = self.T[constr_name]["b_vec"]
                value.resize((self.row_dicts[constr_name]["count"], 1))
                constr_vector = value
            else:
                constr_vector = sp.sparse.dok_matrix((self.row_dicts[constr_name]["count"], 1))

            if isinstance(constraint.relation, Equality):
                G = constr_matrix if G is None else sp.sparse.vstack((G, constr_matrix))
                h = constr_vector if h is None else sp.sparse.vstack((h, constr_vector))
            else:
                A = constr_matrix if A is None else sp.sparse.vstack((A, constr_matrix))
                b = constr_vector if b is None else sp.sparse.vstack((b, constr_vector))

        if b is not None: b = -b #at some point we had lhs = lhs - rhs, so now we have to put b back on the rhs
        if h is not None: h = -h

        c = rlpProblem.sense * c

        return c.todense().T, A.tocoo(), b.todense(), G.tocoo(), h.todense()

    def visit(self, constraint):
        pass


    def constraint_to_matrix(self, rlpProblem, constraint, col_dicts, row_dicts, T):

        constr_name = 'CONSTR'+str(id(constraint))
        T[constr_name] = {}
        row_dicts[constr_name] = {"count":0}


        if isinstance(constraint, Rel):
            lhs = constraint.lhs - constraint.rhs
            constr_query = True
            constr_qsymb = EmptySet()

        elif isinstance(constraint, ForAll):
            lhs = constraint.relation.lhs - constraint.relation.rhs
            if isinstance(constraint.relation, GreaterThan):
                lhs = -1*lhs
            constr_query = constraint.query
            constr_qsymb = constraint.query_symbols
        else:
            lhs = constraint
            constr_query = True
            constr_qsymb = EmptySet()

        lhs = NormalizeVisitor(lhs).result

        if not isinstance(lhs, Add): terms = [lhs]
        else: terms = lhs.args

        row_dict = row_dicts[constr_name]

        for term in terms:

            if isinstance(term, RlpSum):
                term_query = term.query
                term_qsymb = term.query_symbols
                coef_query, coef_qsymb, var_atom = coefficient_to_query(term.args[2])
            else:
                term_query = True
                term_qsymb = EmptySet()
                coef_query, coef_qsymb, var_atom = coefficient_to_query(term)


            qs = constr_qsymb + term_qsymb
            #if isinstance(coef_qsymb, SubSymbol): qs += FiniteSet(coef_qsymb)
            qs = [s for s in qs]

            coeff_expr = coef_qsymb if not isinstance(coef_qsymb, SubSymbol) else None
            q = constr_query & term_query & coef_query

            records = self.logkb.ask(qs,  q, coeff_expr)

            if var_atom is None:
                var_atom = "b_vec"
                col_order = []
            else:
                col_order = [qs.index(var) for var in var_atom.args]

            if col_dicts.has_key(str(var_atom)):
                col_dict = col_dicts[str(var_atom)]
            else:
                col_dict = {"count": 0}
                col_dicts[str(var_atom)] = col_dict

            row_order = [qs.index(var) for var in constr_qsymb]

            data_index = len(records[0])-1

            TT = [
                [unique((rec[i] for i in row_order),row_dict),
                 unique((rec[i] for i in col_order), col_dict),
                 np.float(rec[data_index])]
                for rec in records ]
            TT = np.array(TT)

            D = sp.sparse.coo_matrix((TT[:, 2], (TT[:, 0], TT[:, 1]))).todok()

            if T.has_key(constr_name):
                if T[constr_name].has_key(str(var_atom)):
                    D.resize((row_dict["count"], col_dict["count"]))
                    T[constr_name][str(var_atom)].resize((row_dict["count"], col_dict["count"]))
                    T[constr_name][str(var_atom)] += D
                else:
                    T[constr_name][str(var_atom)] = D
            else:
                T[constr_name] = {}
                T[constr_name][str(var_atom)] = D


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
        query = []
        query_expr = []
        var_atom = None
        for arg in expr.args:
            if arg.has(NumericPredicate):
                [q, e, v] = coefficient_to_query(arg)
                if v is not None: var_atom = v
            else:
                q = True; e = arg
            query.append(q); query_expr.append(e)
        return [And(*query), expr.func(*query_expr), var_atom]

def unique(tup, index_dict):
    s = ",".join([str(u) for u in tup])
    if index_dict.has_key(s):
        return index_dict[s]
    else:
        c = index_dict["count"]
        index_dict[s] = c
        index_dict["count"] = c + 1
        return c

def variable_name_for_expression(expr):
    return 'VAL' + str(id(expr))


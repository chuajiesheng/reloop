from reloop2 import *

class LogKb:
    def ask(self, query_symbols, query):
        raise NotImplementedError

    def ask_predicate(self, predicate):
        raise NotImplementedError

class PyDatalogLogKb(LogKb):

    def ask(self, query_symbols, query):

        helper_predicate = 'helper(' + ','.join([str(v) for v in query_symbols]) + ')'
        tmp = helper_predicate + " <= " + self.transform_query(query)
        pyDatalog.load(tmp)

        answer = pyDatalog.ask(helper_predicate)
        pyEngine.Pred.reset_clauses(pyEngine.Pred("helper", len(query_symbols)))

        return answer

    def ask_predicate(self, predicate):

        query = predicate.name + "("
        query += ','.join(["'" + str(a) + "'" for a in predicate.args])
        query += ", X)"

        answer = pyDatalog.ask(query)
        return answer

    @staticmethod
    def transform_query(query):
        if query.func is And:
            return " &".join([PyDatalogLogKb.transform_query(arg) for arg in query.args])

        if query.func is Not:
            return " ~" + PyDatalogLogKb.transform_query(query.args[0])

        if isinstance(query, RlpBooleanPredicate):
            join = ",".join([str(arg) if isinstance(arg, SubSymbol) else "'" + str(arg) + "'" for arg in query.args])
            return " " + query.name + "(" + join + ")"

        raise NotImplementedError

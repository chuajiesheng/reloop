from reloop2 import *
from pyDatalog import pyDatalog, pyEngine
import psycopg2

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

        if isinstance(query, BooleanPredicate):
            join = ",".join([str(arg) if isinstance(arg, SubSymbol) else "'" + str(arg) + "'" for arg in query.args])
            return " " + query.name + "(" + join + ")"

        raise NotImplementedError

class PostgreSQLKb (LogKb):

    def __init__(self, dbname, user, password):
        connection = psycopg2.connect("dbname="+ dbname + " user="+user + " password="+password)
        self.cursor = connection.cursor()

    def generate_select_clause(self, query_symbols, predicate):

        select_clause = ",".join([predicate + "." + symbol for symbol in query_symbols])
        return select_clause

    def generate_from_clause(self, predicate):
        raise NotImplementedError

    def generate_where_clause(self, query):
        raise NotImplementedError

    def ask_predicate(self, predicate):

        self.cursor.execute("SELECT column_name FROM information_schema.columns where table_name=" + "\'" + predicate.name + "'\'")
        columns = self.cursor.fetchall()

        # Assume desired Values of grounded variables are in the last column of the table
        select_clause = columns.pop()[0].toUpper()
        columns = zip(columns,predicate.args)
        tempquery = []

        for column in columns:
            tempquery.append(str(column[0][0]) + " = " + "\'" +str(column[1][0]) + "\'")

        where_clause = " AND ".join([str(a) for a in predicate.args])
        query = "SELECT " + select_clause + " FROM " + predicate.name + " WHERE " + where_clause
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def ask(self, query_symbols, query):

        predicate = "edge2"
        select_clause = self.generate_select_clause(query_symbols, predicate)
        from_clause = self.generate_from_clause(predicate)
        where_clause = self.generate_where_clause(query)
        query = "SELECT " + select_clause + " FROM " + from_clause + " WHERE " + where_clause

    def transform_query(self, query):

        if query.func is And:
            return " AND ".join([PostgreSQLKb.transform_query(arg) for arg in query.args])

        if query.func is Not:
            position = 0
            self.cursor.execute("SELECT column_name FROM information_schema.columns where table_name=" + "\'" + query.name + "'\'")
            columns = self.cursor.fetchall()

            for arg in query.args:
                if isinstance(arg, SubSymbol):
                    # X != 'a' , Y != 'b'
                    return columns[position] + " != " + "\'" + str(arg) + "\'"
                position += 1

        if isinstance(query, BooleanPredicate):
            position = 0
            self.cursor.execute("SELECT column_name FROM information_schema.columns where table_name=" + "\'" + query.name + "'\'")
            columns = self.cursor.fetchall()
            for arg in query.args:
                if not isinstance(arg, SubSymbol):
                    # X != 'a' , Y != 'b'
                    return columns[position] + " = " + "\'" + str(arg) + "\'"
                position += 1
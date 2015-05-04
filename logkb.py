from twisted.internet.tcp import _AbortingMixin
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

    def __init__(self, dbname, user, password=None):
        connection = psycopg2.connect("dbname="+ str(dbname) + " user="+ str(user) + " password="+ str(password))
        self.cursor = connection.cursor()

    def get_query(self,query,anchor):
        print "SELECT column_name FROM information_schema.columns where table_name=" + "\'" +str(query.name) + "\'"
        self.cursor.execute("SELECT column_name FROM information_schema.columns where table_name=" + "\'" +str(query.name) + "\'")
        columns = self.cursor.fetchall()
        self.cursor.execute("SELECT column_name FROM information_schema.columns where table_name=" + "\'" +str(anchor.name) + "\'")
        anchor_columns = self.cursor.fetchall()

        index = 0
        select = []
        where = []
        inner_join = []
        where_join = []
        anchor_clause=[]

        assert isinstance(query, BooleanPredicate)
        gen_query = ""
        if columns:
            if query.equals(anchor):
                for symbol in anchor.args:
                    if isinstance(symbol, SubSymbol):
                        select.append(query.name + "." + anchor_columns[index][0] + " AS " + str(symbol))
                    else:
                        where.append(str(anchor_columns[index][0]) + " = " + str(symbol))
                    index += 1

                anchor_clause = "SELECT DISTINCT " + ",".join([arg for arg in select]) + " FROM " + anchor.name
                index = 0
            else:
                for symbol in query.args:
                    if isinstance(symbol, SubSymbol):
                        inner_index = 0
                        for anchor_symbol in anchor.args:
                            if anchor_symbol.equals(symbol):
                                inner_join.append(anchor.name + "." + anchor_columns[index][0] + " = " + query.name + "." + columns[index][0])
                                inner_index += 1
                    else:
                        inner_join.append(query.name + "." + columns[index][0] + " = " + str(symbol))


        if anchor_clause:
            return (anchor_clause,where)
        else:
            gen_query = query.name + " ON (" + "AND".join(arg for arg in inner_join) + ")"
            return (gen_query,)

    def ask_predicate(self, predicate):

        self.cursor.execute("SELECT column_name FROM information_schema.columns where table_name=" + "\'" + predicate.name + "'\'")
        columns = self.cursor.fetchall()

        # Assume desired Values of grounded variables are in the last column of the table
        # TODO Compare columns to the symbols of the predicate and query according to their order instaed of assuming the above
        select_clause = columns.pop()[0].toUpper()
        columns = zip(columns,predicate.args)
        tempquery = []

        for column in columns:
            tempquery.append(str(column[0][0]) + " = " + "\'" +str(column[1][0]) + "\'")

        where_clause = " AND ".join([str(a) for a in tempquery])
        query = "SELECT " + select_clause + " FROM " + predicate.name + " WHERE " + where_clause
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def ask(self, query_symbols, query):

        right_joins = []
        inner_joins = []
        if query.func is And:
            for arg in query.args:
                if arg.func is Not:
                    right_joins.append(arg)
                elif isinstance(arg, BooleanPredicate):
                    inner_joins.append(arg)
                else:
                    raise NotImplementedError('The given argument is neither a negation nor a boolean predicate')
        elif query.func is Not:
            raise ValueError
        elif isinstance(query,BooleanPredicate):
            return self.ask_predicate(query)
        else:
            raise NotImplementedError('The given function of the query has not been implemented yet or is not valid')

        if inner_joins:
            anchor = inner_joins[0]
            query_anchor = self.get_query(anchor,anchor)
            conjunction = " INNER JOIN ".join([self.get_query(arg,anchor)[0] for arg in inner_joins])
            if query_anchor[1]:
                conjunction = conjunction + " WHERE " + " AND ".join(arg for arg in query_anchor[1])
            print conjunction

        negation = ""
        if right_joins:
            negation = " EXCEPT( " + " UNION ".join([self.get_query(arg.anchor) for arg in right_joins]) + ")"
            print negation

        query = conjunction + negation

        print query
        self.cursor.execute(query)
        return self.cursor.fetchall()

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
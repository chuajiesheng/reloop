from numpy.numarray.functions import and_
from openpyxl.cell import column_index_from_string
from reloop2 import *
from pyDatalog import pyDatalog, pyEngine
from sets import Set
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

        return answer.answers

    def ask_predicate(self, predicate):

        query = predicate.name + "("
        query += ','.join(["'" + str(a) + "'" for a in predicate.args])
        query += ", X)"

        answer = pyDatalog.ask(query)
        return answer.answers

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

    def ask(self, query_symbols, query):
        negated_predicates = []
        predicates = []
        if query.func is And:
            for arg in query.args:
                if arg.func is Not:
                    negated_predicates.append(arg.args[0])
                elif isinstance(arg, BooleanPredicate):
                    predicates.append(arg)
                else:
                    raise ValueError('The given query is not in DNF')
        elif query.func is Not:
            raise ValueError("This nothing! Or the universe! We don't know!")
        elif query.func is Or:
            raise NotImplementedError("Next version")
        elif isinstance(query, BooleanPredicate):
            predicates.append(query)
        else:
            raise NotImplementedError('The given function of the query has not been implemented yet or is not valid')

        column_for_symbols_where = self.get_columns_for_symbols(query_symbols, predicates)
        column_for_symbols_notexists = self.get_columns_for_symbols(query_symbols, negated_predicates)

        query = "SELECT DISTINCT " + ", ".join([value[0][0] + "." + value[0][1] + " AS " + str(key) for key, value in column_for_symbols_where.items()])
        tables = Set([value[0][0] for key, value in column_for_symbols_where.items()])
        query += " FROM " + ", ".join([str(value) for value in tables])

        and_clause = False
        query += " WHERE "
        for symbol, value in column_for_symbols_where.items():
            if and_clause:
                query += " AND "

            if len(value) > 0:
                and_clause = True
            else:
                and_clause = False
            reference_column = value[0][0] + "." + value[0][1]
            query += " AND ".join([reference_column + " = " + rel + "." + col for rel, col in value])

        query += self.and_clause_for_constants(predicates, and_clause)

        and_clause = False
        for symbol, value in column_for_symbols_notexists.items():
            for rel, col in value:
                if len(value) > 0:
                    and_clause = True
                else:
                    and_clause = False
                query += " AND NOT EXISTS (SELECT * FROM " + rel + " WHERE "
                reference_column = column_for_symbols_where[symbol][0][0]
                query += " AND ".join([reference_column + "." + col + " = " + reltmp + "." + col for reltmp, col in value if reltmp == rel])
                query += self.and_clause_for_constants(negated_predicates, and_clause)

                query += ")"

        print query
        self.cursor.execute(query)
        values = self.cursor.fetchall()
        print values
        return values

    def ask_predicate(self, predicate):

        self.cursor.execute("SELECT column_name FROM information_schema.columns where table_name=" + "\'" + predicate.name + "\'")
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

    def and_clause_for_constants(self, predicates, and_clause_added):
        query = ""
        for predicate in predicates:
            for index, arg in enumerate(predicate.args):
                if not isinstance(arg, SubSymbol):
                    if and_clause_added:
                        query += " AND "
                    else:
                        and_clause_added = True
                    query += predicate.name + "." + self.get_column_names(predicate.name)[index] + " = " + "'" +str(arg) + "'"

        return query

    def get_columns_for_symbols(self, query_symbol, predicates):
        column_for_symbols = {key: [] for key in query_symbol}
        for predicate in predicates:
            column_names = self.get_column_names(predicate.name)

            for index, arg in enumerate(predicate.args):
                if isinstance(arg, SubSymbol):
                    column_for_symbols[arg].append((predicate.name, column_names[index]))

        return column_for_symbols

    def get_column_names(self, relation_name):
        query = "SELECT column_name FROM information_schema.columns where table_name=" + "'" + relation_name + "'"
        print(query)
        self.cursor.execute(query)
        return [item[0] for item in self.cursor.fetchall()]


from reloop2 import *
from pyDatalog import pyDatalog, pyEngine
from sets import Set
import psycopg2

class LogKb:
    """
    Interface for various LogKBs. Provides basic functionality for every LogKB to be implemented.
    """
    def ask(self, query_symbols, logical_query):
        """
        Constructs a query for the given LogKB and returns the List/Set of given answers from the LogKB

        :param query_symbols: The symbols to be queried for.
        :param logical_query: The logical query, which is to be transformed into a query fitting the LogKB
        :return: A List of elements, which satisfy the query
        """
        raise NotImplementedError

    def ask_predicate(self, predicate):
        """
        Queries the LogKB for a specific Value for given constants.
        For Example : cost('a','b') = 50

        :param predicate: The predicate to be queried for
        :return: The Value associated with the predicate
        """
        raise NotImplementedError


class PyDatalogLogKb(LogKb):

    def ask(self, query_symbols, logical_query):
        """
        Builds a pyDataLog program from the logical_query and loads it. Then executes the query for the query_symbols.

        :param query_symbols: The symbols to be queried.
        :type query_symbols: list(SubSymbol)
        :param logical_query:
        :type:
        :return:
        """

        helper_predicate = 'helper(' + ','.join([str(v) for v in query_symbols]) + ')'
        tmp = helper_predicate + " <= " + self.transform_query(logical_query)
        pyDatalog.load(tmp)

        answer = pyDatalog.ask(helper_predicate)
        pyEngine.Pred.reset_clauses(pyEngine.Pred("helper", len(query_symbols)))

        return answer.answers

    def ask_predicate(self, predicate):
        """
        Queries PyDataLog for the given predicate by constructing a query fitting the pyDataLog Syntax.

        :param predicate: The predicate to be quried for
        :return: The Value of the given predicate if it exists in the Database, None otherwise.
        """
        query = predicate.name + "("
        query += ','.join(["'" + str(a) + "'" for a in predicate.args])
        query += ", X)"

        answer = pyDatalog.ask(query)
        print "PREDICATE : " + str(predicate) + " QUERY " + str(query) + " ANSWER " + str(answer)
        return answer.answers

    @staticmethod
    def transform_query(logical_query):
        """
        Recursively builds the logical_query string from the given logical logical_query,by evaluating

        :param logical_query: Type changes depending on the recursive depth and the depth of the expression.
                              The logical query, needed for the pyDataLog program string.
        :type logical_query: Boolean, BooleanPredicate
        :return: The complete Body for loading the program into pyDataLog.
        """

        print "TYPE :" + str(type(logical_query))
        if logical_query.func is And:
            return " &".join([PyDatalogLogKb.transform_query(arg) for arg in logical_query.args])

        if logical_query.func is Not:
            return " ~" + PyDatalogLogKb.transform_query(logical_query.args[0])

        if isinstance(logical_query, BooleanPredicate):
            join = ",".join([str(arg) if isinstance(arg, SubSymbol) else "'" + str(arg) + "'" for arg in logical_query.args])
            return " " + logical_query.name + "(" + join + ")"

        raise NotImplementedError

class PostgreSQLKb (LogKb):

    def __init__(self, dbname, user, password=None):
        """

        Opens a connection to the specified database and stores a cursor object for the class to access at runtime.

        :param dbname: The name of the Database to connect to
        :param user: Database User
        :param password: The password for the given user if applicable
        """
        connection = psycopg2.connect("dbname="+ str(dbname) + " user="+ str(user) + " password="+ str(password))
        self.cursor = connection.cursor()

    def ask(self, query_symbols, logical_query):
        """
        Builds a PostgreSQL query from a given logical query and its query_symbols by implicitly joining over all given predicates.

        :param query_symbols: see :func:`~logkb.LogKB.ask`
        :param query:         see :func:`~logkb.LogKB.ask`
        :return: The answers, which satisfy the executed query on the database
        """
        negated_predicates = []
        predicates = []
        if logical_query.func is And:
            for arg in logical_query.args:
                if arg.func is Not:
                    negated_predicates.append(arg.args[0])
                elif isinstance(arg, BooleanPredicate):
                    predicates.append(arg)
                else:
                    raise ValueError('The given query is not in DNF')
        elif logical_query.func is Not:
            raise ValueError("This nothing! Or the universe! We don't know!")
        elif logical_query.func is Or:
            raise NotImplementedError("Next version")
        elif isinstance(logical_query, BooleanPredicate):
            predicates.append(logical_query)
        else:
            raise NotImplementedError('The given function of the query has not been implemented yet or is not valid')

        column_for_symbols_where = self.get_columns_for_symbols(query_symbols, predicates)
        column_for_symbols_notexists = self.get_columns_for_symbols(query_symbols, negated_predicates)

        query = "SELECT DISTINCT "
        query += ", ".join([value[0][0] + "." + value[0][1] + " AS " + str(key) for key, value in column_for_symbols_where.items()])
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

        print "QUERY : " + query
        self.cursor.execute(query)
        values = self.cursor.fetchall()
        print "VALUES : " + str(values)
        return values

    def ask_predicate(self, predicate):
        """
        Queries a value from the database for a given predicate.
        The predicate only has constants as symbols and the value per definition has to be in the last column of the table.
        Such that a query "cost('a','b') implicitly queries for SELECT z FROM cost WHERE x = 'a' AND y = 'b'
        with z here being the third column of the table.

        :param predicate: The predicate to be queried for
        :type predicate: BooleanPredicate
        :return: The Value associated with the predicate taken from the database
        """
        columns = self.get_column_names(predicate.name)
        query = "SELECT " + str(columns[len(columns)-1][0]) + \
                " FROM "  + str(predicate.name) + \
                " WHERE " + \
                " AND ".join([str(columns[index][0]) + "="  + "'" + str(arg) + "'" for index, arg in enumerate(predicate.args) ])
        print query

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def and_clause_for_constants(self, predicates, and_clause_added):
        """
        Iterates over a list of given predicates and returns the where-clause for constants.

        :param predicates: The given predicates. E.g. : edge(X,'a'), edge ('a','c')
        :type predicate: List(BooleanPredicate)
        :param and_clause_added: Indicates if there was been an and-clause beforehand to correctly concantenate the querystring
        :type and_clause_added: Boolean
        :return: The SQL conjunctions for the given predicates
        """
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
        """

        :param query_symbol: The Symbols to be queried for (Keys)
        :type query_symbol: List(SubSymbol)
        :param predicates: The predicates, where the symbols might occur (Values)
        :type predicates:List(BooleanPredicate)
        :return: A dictionary, which maps from the given query_symbols to the corresponding predicates in which the symbols occur.
        """
        column_for_symbols = {key: [] for key in query_symbol}
        for predicate in predicates:
            column_names = self.get_column_names(predicate.name)

            for index, arg in enumerate(predicate.args):
                if isinstance(arg, SubSymbol):
                    column_for_symbols[arg].append((predicate.name, column_names[index]))

        return column_for_symbols

    def get_column_names(self, relation_name):
        """
        Convenience function to get the name of the columns for a given table.

        :param relation_name: The name of the table
        :type relation_name: str
        :return: A list consisting of the column names.
        """
        query = "SELECT column_name FROM information_schema.columns where table_name=" + "'" + relation_name + "'"
        self.cursor.execute(query)
        return [item[0] for item in self.cursor.fetchall()]


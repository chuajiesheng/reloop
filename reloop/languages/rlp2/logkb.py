from rlp import *
import logging
from ordered_set import OrderedSet

try:
    from pyDatalog import pyDatalog, pyEngine

    pydatalog_available = True
except ImportError:
    pydatalog_available = False

try:
    import psycopg2

    psycopg2_available = True
except ImportError:
    psycopg2_available = False

try:
    from problog import *

    prolog_available = True
except ImportError:
    prolog_available = False

assert psycopg2_available or pydatalog_available or prolog_available, 'Import Error : Please install any one of our interface Knowledgebases to proceed. Currently available are PostgreSQL and Pydatalog.'
log = logging.getLogger(__name__)


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
    def __init__(self):
        assert pydatalog_available, "Import Error: PyDatalog is not installed on your machine. To use our PyDatalog interface please install pydatalog"

    def ask(self, query_symbols, logical_query, coeff_expr = None):
        """
        Builds a pyDataLog program from the logical_query and loads it. Then executes the query for the query_symbols.

        :param query_symbols: The symbols to be queried.
        :type query_symbols: list(SubSymbol)
        :param logical_query:
        :type:
        :return:
        """
        helper_len = 0
        tmp = None

        if coeff_expr is None:
            helper_len = len(query_symbols)
            helper_predicate = 'helper(' + ','.join([str(v) for v in query_symbols]) + ')'
            tmp = helper_predicate + " <= " + self.transform_query(logical_query)
        else:
            helper_len = len(query_symbols)+1
            syms = OrderedSet(query_symbols)
            syms.add('COEFF_EXPR')
            helper_predicate = 'helper(' + ','.join([str(v) for v in syms]) +')'
            index_query = self.transform_query(logical_query)
            coeff_query = "(COEFF_EXPR == " + str(coeff_expr) + ")"
            if index_query is None:
                tmp = helper_predicate + " <= " + coeff_query
            else:
                tmp = helper_predicate + " <= " + " & ".join([index_query,coeff_query])
        log.debug("pyDatalog query: " + tmp)
        pyDatalog.load(tmp)
        answer = pyDatalog.ask(helper_predicate)
        pyEngine.Pred.reset_clauses(pyEngine.Pred("helper", helper_len))

        if answer is None:
            return []
        return answer.answers

    def ask_predicate(self, predicate):
        """
        Queries PyDataLog for the given predicate by constructing a query fitting the pyDataLog Syntax.

        :param predicate: The predicate to be quried for
        :return: The Value of the given predicate if it exists in the Database, None otherwise.
        """
        query = predicate.name + "("
        query += ','.join([ str(a) if not isinstance(a, Symbol) else "\'" + str(a) + "\'" \
                                    for a in predicate.args])
        query += ", X)"
        answer = pyDatalog.ask(query)

        if answer is None:
            return None
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
        if logical_query == True:
            return None

        if logical_query.func is And:
            return " &".join([PyDatalogLogKb.transform_query(arg) for arg in logical_query.args])

        if logical_query.func is Not:
            return " ~" + PyDatalogLogKb.transform_query(logical_query.args[0])

        if isinstance(logical_query, BooleanPredicate):
            join = ",".join([str(arg) if isinstance(arg, SubSymbol) else str(arg)  for arg in logical_query.args])
            return " " + logical_query.name + "(" + join + ")"



        raise NotImplementedError


class PostgreSQLKb(LogKb):
    """
    A Logical Knowledge Base based on a PostgreSQL database.
    """

    def __init__(self, dbname, user, password=None):
        """

        Opens a connection to the specified database and stores a cursor object for the class to access at runtime.

        :param dbname: The name of the Database to connect to
        :param user: Database User
        :param password: The password for the given user if applicable
        """

        assert psycopg2_available, "Import Error : It seems like psycopg2 is currently not installed or available on your machine. To proceed please install psycopg2"

        connection = psycopg2.connect("dbname=" + str(dbname) + " user=" + str(user) + " password=" + str(password))
        self.cursor = connection.cursor()
        self.recursive = True

    def ask(self, query_symbols, logical_query, coeff_expr = None):
        """
        Builds a PostgreSQL query from a given logical query and its query_symbols by implicitly joining over all given predicates.

        :param query_symbols: see :func:`~logkb.LogKB.ask`
        :param query:         see :func:`~logkb.LogKB.ask`
        :return: The answers, which satisfy the executed query on the database
        """
        logical_query = simplify(logical_query)

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
        elif isinstance(logical_query, BooleanTrue):
            #there is no logical query here, hence we must be grounding a 
            #single number here, e.g. the rhs of a non-forall-quantified constraint
            return [[coeff_expr]]
        else:
            raise NotImplementedError('The given function of the query has not been implemented yet or is not valid')

        column_for_symbols_where = self.get_columns_for_symbols(query_symbols, predicates)
        column_for_symbols_notexists = self.get_columns_for_symbols(query_symbols, negated_predicates)
        column_for_symbols_all = self.get_columns_for_symbols(logical_query.atoms(Symbol), predicates + negated_predicates)

        expr_as_string = str(coeff_expr)
        for symbol, columns in column_for_symbols_all.items():
            if isinstance(symbol, VariableSubSymbol):
                expr_as_string = expr_as_string.replace(str(symbol), columns[0][0] + "." + columns[0][1])

        query = "SELECT DISTINCT "

        query += ", ".join([value[0][0] + "." + value[0][1] + " AS " + str(key) for key, value in column_for_symbols_where.items()] + [expr_as_string])
        column_table_tuple_list = [value for key, value in column_for_symbols_where.items()]
        tables = set([item[0] for sublist in column_table_tuple_list for item in sublist])

        for table in tables:
            queryy = "select exists(select * from information_schema.tables where table_name='" + table + "')"
            self.cursor.execute(queryy)
            if self.cursor.fetchone()[0] is False:
                raise ValueError ("Error : the table " + str(table) + " does not exist in the specified database and therefore can not be queried.")

        query += " FROM " + ", ".join([str(value).lower() for value in tables])

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
            query += " AND ".join([reference_column + " = " + rel.lower()  + "." + col for rel, col in value])

        query += self.and_clause_for_constants(predicates, and_clause)

        and_clause = False
        for symbol, value in column_for_symbols_notexists.items():
            for rel, col in value:
                if len(value) > 0:
                    and_clause = True
                else:
                    and_clause = False
                query += " AND NOT EXISTS (SELECT * FROM " + rel.lower() + " WHERE "
                reference_column = column_for_symbols_where[symbol][0][0]
                query += " AND ".join([reference_column + "." + col + " = " + reltmp.lower()  + "." + col for reltmp, col in value if reltmp == rel])
                query += self.and_clause_for_constants(negated_predicates, and_clause)

                query += ")"

        self.cursor.execute(query)
        values = self.cursor.fetchall()

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
        query = "SELECT " + str(columns[len(columns) - 1][0]) + \
                " FROM " + str(predicate.name.lower()) + \
                " WHERE " + \
                " AND ".join([str(columns[index][0]) + "=" + "'" + str(arg) + "'" for index, arg in enumerate(predicate.args)])

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
                    query += predicate.name.lower() + "." + self.get_column_names(predicate.name)[index] + " = " + "'" + str(arg) + "'"

        return query

    def get_columns_for_symbols(self, query_symbol, predicates):
        """
        Creates a dictionary from symbols and predicates with Key, Value pairs of query_symbols,predicates , where
        Symbol is the Key to its occurances in the predicates.

        :param query_symbol: The Symbols to be queried for (Keys)
        :type query_symbol: List(SubSymbol)
        :param predicates: The predicates, where the symbols might occur (Values)
        :type predicates: List(BooleanPredicate)
        :return: A dictionary, which maps from the given query_symbols to the corresponding predicates in which the symbols occur.
        """
        column_for_symbols = {key: [] for key in query_symbol}
        for predicate in predicates:
            column_names = self.get_column_names(predicate.name)

            for index, arg in enumerate(predicate.args):
                if isinstance(arg, SubSymbol):
                    # We only want those symbols, that appear in the query
                    if column_for_symbols.has_key(arg):
                        column_for_symbols[arg].append((predicate.name, column_names[index]))

        return column_for_symbols

    def get_column_names(self, relation_name):
        """
        Convenience function to get the name of the columns for a given table.

        :param relation_name: The name of the table
        :type relation_name: str
        :return: A list consisting of the column names.
        """
        query = "SELECT column_name FROM information_schema.columns where table_name=" + "'" + relation_name.lower() + "' ORDER BY ordinal_position ASC"
        self.cursor.execute(query)
        ans = [item[0] for item in self.cursor.fetchall()]
        return ans

class PrologKB(LogKb):

    def __init__(self, prolog):
        from pyswip import Prolog
        assert isinstance(prolog,Prolog)

        self.prolog = prolog

    def ask_predicate(self, predicate):

        result =    list(self.prolog.query(predicate.name +\
                    "(" +\
                    ",".join([str(arg) for index, arg in enumerate(predicate.args)]) +\
                    ",X)"))

        answer=[]
        for dictionary in result:
            for key, value in dictionary.items():
                answer.append((value,))
        return answer

    def ask(self, query_symbols, logical_query):
        """
        Builds a Prolog program from the logical_query and queries for it. Then executes the query for the query_symbols.
        :param query_symbols: The symbols to be queried.
        :type query_symbols: list(SubSymbol)
        :param logical_query:
        :type:
        :return:[(a,b),(a,c)]
        """
        query = ProbLogKB.transform_query(logical_query)
        prolog_answer = list(self.prolog.query(query))
        answers = []
        for dictionary in prolog_answer:
            assert isinstance(dictionary,dict)
            res=[]
            for query_symbol in query_symbols:
                res.append(dictionary.get(str(query_symbol)))
            answers.append(tuple(res))
        return answers

class ProbLogKB(LogKb):

    def __init__(self, file_path):
        file = open(file_path, "r")
        self.knowledge = file.read()
        file.close()

    def execute(self, query):
        #import subprocess
        #proc = subprocess.Popen(["/home/danny/Workspace/Reloop/saucywrapper/problog/problog-cli.py", "prob","-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        problog_prog = self.knowledge + "\n".join(query)
        import StringIO
        import sys

        s = StringIO.StringIO(problog_prog)
        sys.stdin = s
        import problog.tasks.probability as problog

        result = problog.execute(filename = "-")[1]
        sys.stdin = sys.__stdin__

        return result




    def ask(self, query_symbols, logical_query, coeff_expr = None):

        if coeff_expr is None:
            lhs_rule = 'helper(' + ','.join([str(v) for v in query_symbols]) + ')'
            rule = lhs_rule + ":-" + self.transform_query(logical_query) + "."
            query = "query(" + lhs_rule +")."
        else:
            syms = OrderedSet(query_symbols)
            syms.add('COEFF_EXPR')
            lhs_rule = 'helper(' + ','.join([str(v) for v in syms]) +')'
            index_query = self.transform_query(logical_query)
            coeff_query = "COEFF_EXPR = " + str(coeff_expr) + ""
            query = "query(" + lhs_rule +")."
            if index_query is None:
                rule = lhs_rule + " :- " + coeff_query + "."
            else:
                rule = lhs_rule + " :- " + " , ".join([index_query,coeff_query]) + "."

        answer = self.execute([rule, query])

        answer_args = []
        for key in answer.keys():
            answer_args.append(key.args)

        # Query yields no result
        if answer.values()[0] == 0.0:
            return []

        for t in answer_args:
            for term in t:
                if term.functor == '\'-\'':
                    term.functor = '-' + str(term.args[0])

        result = [tuple(map(lambda t: t.functor, t)) for t in answer_args]
        return result

    def ask_predicate(self, predicate):

        answer = self.execute(["query(" + predicate.name +\
                    "(" +\
                    ",".join([str(arg) for index, arg in enumerate(predicate.args)]) +\
                    ",X))."])

        answer_args = []
        for key in answer.keys():
            answer_args.append(key.args)

        result = [(answer_args[0][-1].functor,)]
        return result

    @staticmethod
    def transform_query(logical_query):
        """
        Recursively builds the logical_query string from the given logical logical_query,by evaluating
        :param logical_query: Type changes depending on the recursive depth and the depth of the expression.
                              The logical query, needed for the pyDataLog program string.
        :type logical_query: Boolean, BooleanPredicate
        :return: The complete Body for loading the program into pyDataLog.
        """
        if logical_query.func is And:
            return ", ".join([ProbLogKB.transform_query(arg) for arg in logical_query.args])
        if logical_query.func is Not:
            return " not(" + ProbLogKB.transform_query(logical_query.args[0]) +")"
        if isinstance(logical_query, BooleanPredicate):
            join = ",".join([str(arg) if isinstance(arg, SubSymbol) else str(arg)  for arg in logical_query.args])
            return " " + logical_query.name + "(" + join + ")"
        raise NotImplementedError

import unittest
from reloop.languages.rlp.grounding.recursive import RecursiveGrounder
from reloop.solvers.lpsolver import CvxoptSolver
from examples.RLP import maxflow_example


class TestLogKB(unittest.TestCase):
    def test_pydatalog_ask_predicate(self):
        from pyDatalog import pyDatalog
        import random
        from reloop.languages.rlp.rlp import Symbol
        from reloop.languages.rlp.rlp import RlpPredicate
        from reloop.languages.rlp.logkb import PyDatalogLogKb

        logkb = PyDatalogLogKb()
        pred = RlpPredicate("test_predicate", 1)
        pred.name = "test_predicate"

        print("Testing PyDatalog Float Predicates...")
        float_test_data = random.random()
        pyDatalog.assert_fact("test_predicate", 'a', float_test_data)
        pred._args = (Symbol('a'),)
        test_query_answer = logkb.ask_predicate(pred)
        self.assertEqual(float_test_data, test_query_answer[0][0],
                         "The result of the query : " + str(
                             test_query_answer) + " was not equal to the previously randomly generated number: " + str(
                             float_test_data))
        print("...OK")

        print("Testing PyDatalog Integer Predicates...")
        integer_test_data = random.randint(1, 100)
        pred._args = (Symbol('b'),)
        pyDatalog.assert_fact("test_predicate", 'b', integer_test_data)
        test_query_answer = logkb.ask_predicate(pred)

        self.assertEqual(integer_test_data, test_query_answer[0][0],
                         "The result of the query : " + str(
                             test_query_answer) + " was not equal to the previously randomly generated number: " + str(
                             integer_test_data))
        print("...OK")

        print("Testing for no occurences in the Database...")
        pred._args = (Symbol('c'),)
        none_result = logkb.ask_predicate(pred)
        self.assertEqual(None, none_result, "The result should have been None but was " + str(none_result))
        print("...OK")

    def test_postgres_ask_predicate(self):
        import random
        from reloop.languages.rlp.logkb import PostgreSQLKb
        from reloop.languages.rlp.rlp import Symbol
        from reloop.languages.rlp.rlp import RlpPredicate

        logkb = PostgreSQLKb("danny", "danny", "")


        integer_test_data = random.randint(1, 100)
        float_test_data = random.random()
        logkb.cursor.execute("DROP TABLE IF EXISTS unittest_int")
        logkb.cursor.execute("DROP TABLE IF EXISTS unittest_float")
        logkb.cursor.execute("CREATE TABLE unittest_int (x varchar(5), z INTEGER NOT NULL);")
        logkb.cursor.execute("CREATE TABLE unittest_float (x varchar(5), z FLOAT NOT NULL);")
        logkb.cursor.execute("INSERT INTO unittest_int values('a', {0}),('b',{1});".format(integer_test_data, float_test_data))
        logkb.cursor.execute("INSERT INTO unittest_float values('a', {0}),('b',{1});".format(integer_test_data, float_test_data))
        logkb.connection.commit()

        pred = RlpPredicate("unittest", 1)
        pred.name = "unittest_int"

        pred._args = (Symbol('a'),)
        int_result = logkb.ask_predicate(pred)

        pred.name = "unittest_float"
        pred._args = (Symbol('b'),)
        float_res = logkb.ask_predicate(pred)

        print("Testing Integer and Float for PostgreSQL...")
        self.assertAlmostEqual(float_test_data, float_res[0][0], msg="The inserted data was " + str(float_test_data) + " but was returned as " + str(float_res[0][0]) + " by the PostgresKB.")
        self.assertEqual(integer_test_data,int_result[0][0], "The inserted data was " + str(integer_test_data) + " but was returned as " + str(int_result) + " by the PostgresKB.")
        print("...OK")

        pred.name = "not_existing_predicate"
        none_result = logkb.ask_predicate(pred)
        self.assertEqual(None,none_result, "Not None")

        pred.name = "unittest_int"
        pred._args = (Symbol('not_existing_arg'),)
        no_arg_result = logkb.ask_predicate(pred)

        pred.name = "not_existing_predicate"
        no_arg_no_pred_result = logkb.ask_predicate(pred)

        self.assertEqual(None, none_result, "Result was expected to be None but was " + str(none_result) + " instead.")
        self.assertEqual([], no_arg_result, "Result was expected to be an empty List but was " + str(no_arg_result) + " instead.")
        self.assertEqual(None, no_arg_no_pred_result, "Result was expected to be None but was " + str(no_arg_no_pred_result) + " instead.")
        print("Cleaning up...")
        logkb.cursor.execute("DROP TABLE IF EXISTS unittest_int")
        logkb.cursor.execute("DROP TABLE IF EXISTS unittest_float")
        logkb.connection.commit()
        logkb.connection.close()
        print("...done.")

    def test_pydatalog_ask(self):
        from reloop.languages.rlp.logkb import PyDatalogLogKb
        from pyDatalog import pyDatalog

        #permute all parameters of the method for profit, but only once at a time
        logkb = PyDatalogLogKb()
        query_symbols = None
        logical_query = None
        coeff_expr = None

        result = logkb.ask(query_symbols,logical_query,coeff_expr)




if __name__ == '__main__':
    unittest.main()

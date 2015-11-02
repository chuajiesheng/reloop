import unittest

class PyDatalogLogKBTest(unittest.TestCase):
    def setUp(self):
        from reloop.languages.rlp.logkb import PyDatalogLogKb
        from pyDatalog import pyDatalog
        import random
        from reloop.languages.rlp.rlp import RlpPredicate

        self.logkb = PyDatalogLogKb()
        self.predicate = RlpPredicate("test_predicate", 1)
        self.predicate.name = "test_predicate"
        self.float_test_data = random.random()
        self.integer_test_data = random.randint(1, 100)
        pyDatalog.assert_fact("test_predicate", 'b', self.integer_test_data)
        pyDatalog.assert_fact("test_predicate", 'a', self.float_test_data)

    def tearDown(self):
        from pyDatalog import pyDatalog
        pyDatalog.clear()


class PyDataLogKBFloatNumericPredicateTestCase(PyDatalogLogKBTest):
    def runTest(self):
        from reloop.languages.rlp.rlp import Symbol

        print("Testing PyDatalog Float Predicates...")
        self.predicate._args = (Symbol('a'),)
        test_query_answer = self.logkb.ask_predicate(self.predicate)
        self.assertEqual(self.float_test_data, test_query_answer[0][0],
                         "The result of the query : " + str(
                             test_query_answer) + " was not equal to the previously randomly generated number: " + str(
                             self.float_test_data))
        print("...OK")


class PyDataLogKBIntegerNumericPredicateTestCase(PyDatalogLogKBTest):
    def runTest(self):
        from reloop.languages.rlp.rlp import Symbol

        print("Testing PyDatalog Integer Predicates...")
        self.predicate._args = (Symbol('b'),)

        test_query_answer = self.logkb.ask_predicate(self.predicate)

        self.assertEqual(self.integer_test_data, test_query_answer[0][0],
                         "The result of the query : " + str(
                             test_query_answer) + " was not equal to the previously randomly generated number: " + str(
                             self.integer_test_data))
        print("...OK")


class PyDataLogKBNotExistingPredicateTestCase(PyDatalogLogKBTest):
    def runTest(self):
        from reloop.languages.rlp.rlp import Symbol
        print("Testing for no occurences in the Database...")
        self.predicate._args = (Symbol('c'),)
        none_result = self.logkb.ask_predicate(self.predicate)
        self.assertEqual(None, none_result, "The result should have been None but was " + str(none_result))
        print("...OK")

class PostgreSQLLogKBTest(unittest.TestCase):
    def setUp(self):
        import random
        from reloop.languages.rlp.logkb import PostgreSQLKb
        from reloop.languages.rlp.rlp import RlpPredicate
        from reloop.languages.rlp.rlp import RlpPredicate

        self.logkb = PostgreSQLKb("danny", "danny", "")
        self.integer_test_data = random.randint(1, 100)
        self.float_test_data = random.random()

        self.logkb.cursor.execute("DROP TABLE IF EXISTS unittest_int")
        self.logkb.cursor.execute("DROP TABLE IF EXISTS unittest_float")
        self.logkb.cursor.execute("CREATE TABLE unittest_int (x varchar(5), z INTEGER NOT NULL);")
        self.logkb.cursor.execute("CREATE TABLE unittest_float (x varchar(5), z FLOAT NOT NULL);")
        self.logkb.cursor.execute("INSERT INTO unittest_int values('a', {0}),('b',{1});".format(self.integer_test_data, self.float_test_data))
        self.logkb.cursor.execute("INSERT INTO unittest_float values('a', {0}),('b',{1});".format(self.integer_test_data, self.float_test_data))

        self.predicate = RlpPredicate("unittest", 1)
        self.logkb.connection.commit()

    def tearDown(self):
        self.logkb.cursor.execute("DROP TABLE IF EXISTS unittest_int")
        self.logkb.cursor.execute("DROP TABLE IF EXISTS unittest_float")
        self.logkb.connection.commit()
        self.logkb.connection.close()


class PostgreSQLKBIntegerNumericPredicateTestCase(PostgreSQLLogKBTest):

    def runTest(self):
        from reloop.languages.rlp.rlp import Symbol

        self.predicate.name = "unittest_int"
        self.predicate._args = (Symbol('a'),)
        int_result = self.logkb.ask_predicate(self.predicate)
        self.assertEqual(self.integer_test_data, int_result[0][0], "The inserted data was " + str(self.integer_test_data) + " but was returned as " + str(int_result) + " by the PostgresKB.")


class PostgreSQLKBFloatNumericPredicateTestCase(PostgreSQLLogKBTest):

    def runTest(self):
        from reloop.languages.rlp.rlp import Symbol

        self.predicate.name = "unittest_float"
        self.predicate._args = (Symbol('b'),)
        float_res = self.logkb.ask_predicate(self.predicate)

        print("Testing Float predicates for PostgreSQL...")
        self.assertAlmostEqual(self.float_test_data, float_res[0][0], msg="The inserted data was " + str(self.float_test_data) + " but was returned as " + str(float_res[0][0]) + " by the PostgresKB.")
        print("...OK")


class PostgreSQLKBNotExistingPredicateTestCase(PostgreSQLLogKBTest):

    def runTest(self):
        self.predicate.name = "not_existing_predicate"
        none_result = self.logkb.ask_predicate(self.predicate)
        self.assertEqual(None, none_result, "The result of the query for postgrs was expected to be None, but returned" + str(none_result))


class PostgreSQLNotExistingArgumentTestCase(PostgreSQLLogKBTest):

    def runTest(self):
        from reloop.languages.rlp.rlp import Symbol

        self.predicate.name = "unittest_int"
        self.predicate._args = (Symbol('not_existing_arg'),)
        no_arg_result = self.logkb.ask_predicate(self.predicate)
        self.assertEqual([], no_arg_result, "Result was expected to be an empty List but was " + str(no_arg_result) + " instead.")


class PostgreSQLNotExistingTableTestCase(PostgreSQLLogKBTest):

    def runTest(self):
        self.predicate.name = "not_existing_predicate"
        no_arg_no_pred_result = self.logkb.ask_predicate(self.predicate)
        self.assertEqual(None, no_arg_no_pred_result, "Result was expected to be None but was " + str(no_arg_no_pred_result) + " instead.")

class PyDatalogAskTestCase(PyDatalogLogKBTest):
    def runTest(self):
        from reloop.languages.rlp.logkb import PyDatalogLogKb

        #permute all parameters of the method for profit, but only once at a time
        logkb = PyDatalogLogKb()
        query_symbols = None
        logical_query = None
        coeff_expr = None

        result = logkb.ask(query_symbols,logical_query,coeff_expr)




if __name__ == '__main__':
    unittest.main()

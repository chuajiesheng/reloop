import abc


class Grounder():
    """
    Interfaces the implementation of available grounding strategies by providing the essential methods for the grounder
    to work properly. This is an abstract class and should be handled as such. Addtionally implemented grounding strategies
    should inherit from this class.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def ground(self, rlpProblem):
        """
        Grounds a relation linear program by applying a defined grounding strategy. The result is then used to formulate
        the lp problem, which is passed to the lpsolver.

        :param rlpProblem: The problem to be grounded
        :return: The linear program
        """
        raise NotImplementedError("")


class PostgresqlConnector():
    def __init__(self, db_name, db_user, db_password=None):
        """
        Opens a connection to the specified database and stores a cursor object for the class to access at runtime.

        :param dbname: The name of the Database to connect to
        :param user: Database User
        :param password: The password for the given user if applicable
        """
        import psycopg2

        connection = psycopg2.connect(
            "dbname=" + str(db_name) + " user=" + str(db_user) + " password=" + str(db_password))
        self.cursor = connection.cursor()

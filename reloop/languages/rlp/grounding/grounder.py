import abc


class Grounder():
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def ground(self, rlpProblem):
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

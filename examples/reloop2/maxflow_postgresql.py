import psycopg2
from logkb import *
from lp import *
import maxflow_example

# Initialize Database with necessary Tables and Values
db_name = raw_input("Please specifiy the name of your Database: ")
db_user = raw_input("Pease specify the Username for the Database: ")
db_password = raw_input("Specify the password if applicable: ")
connection = psycopg2.connect("dbname=" + str(db_name) + " user=" + str(db_user) + " password=" + str(db_password))
cursor = connection.cursor()

# Drop Tables
cursor.execute("DROP TABLE IF EXISTS node ")
cursor.execute("DROP TABLE IF EXISTS edge")
cursor.execute("DROP TABLE IF EXISTS cost")
cursor.execute("DROP TABLE IF EXISTS source")
cursor.execute("DROP TABLE IF EXISTS target")
connection.commit()

# Insert data
cursor.execute("CREATE TABLE node (x varchar(5));")
cursor.execute("INSERT INTO node values('a'),('b'),('c'),('d'),('e'),('f'),('g');")

cursor.execute("CREATE TABLE edge (x varchar(5), y varchar(5));")
cursor.execute("INSERT INTO edge values('a','b'),('a','c'),('b','d'),('b','e'),('c','d'),('c','f'),('d','e'),('d','f'),('e','g'),('f','g');")

cursor.execute("CREATE TABLE cost (x varchar(5), y varchar(5), z INTEGER NOT NULL);")
cursor.execute("INSERT INTO cost values('a','b',50),('a','c',100),('b','d',40),('b','e',20),('c','d',60),('c','f',20),('d','e',50),('d','f',60),('e','g',70),('f','g',70);")

cursor.execute("CREATE TABLE source (x varchar(5));")
cursor.execute("INSERT INTO source values('a');")

cursor.execute("CREATE TABLE target (x varchar(5));")
cursor.execute("INSERT INTO target values('g');")

connection.commit()
cursor.close()
connection.close()

maxflow_example.maxflow(PostgreSQLKb(db_name, db_user, db_password), Pulp)



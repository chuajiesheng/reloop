import psycopg2
from reloop.languages.rlp2.logkb import *
from reloop.languages.rlp2.lp import *
import getpass
import maxflow_example


"""
Execute this file if you want to read data for a maxflow problem from a plain text file
If you do not want to input your database credentials every time you run the file please feel free to change
db_name, db_user and db_password as well as the path accordingly.
Also feel free to change the table names and the table_prefix, but be careful.
Currently you will also have to change the names in maxflow_example.py as well.
Default prefix: "file_"

For further examples on the formatting on the input files please see the filename extension  .max

   n a s       (source)
   n g t       (target)
   n a
   n b         (nodes)
   a a c 20
   a a b 50    (edges and cap)
"""

table_prefix = "file_"

# Initialize Database with necessary Tables and Values
db_name = raw_input("Please specifiy the name of your Database: ")
db_user = raw_input("Pease specify the Username for the Database: ")
db_password = getpass.getpass("Enter your password (Leave blank if None): ")
connection = psycopg2.connect("dbname=" + str(db_name) + " user=" + str(db_user) + " password=" + str(db_password))
cursor = connection.cursor()

# Drop Tables
cursor.execute("DROP TABLE IF EXISTS " + table_prefix + "node")
cursor.execute("DROP TABLE IF EXISTS " + table_prefix + "edge")
cursor.execute("DROP TABLE IF EXISTS " + table_prefix + "cost")
cursor.execute("DROP TABLE IF EXISTS " + table_prefix + "source")
cursor.execute("DROP TABLE IF EXISTS " + table_prefix + "target")
connection.commit()

cursor.execute("CREATE TABLE " + table_prefix + "node (x varchar(255));")

cursor.execute("CREATE TABLE " + table_prefix + "edge (x varchar(255), y varchar(255));")
" +  + "
cursor.execute("CREATE TABLE " + table_prefix + "cost (x varchar(255), y varchar(255), z INTEGER NOT NULL);")
cursor.execute("CREATE TABLE " + table_prefix + "source (x varchar(255));")

cursor.execute("CREATE TABLE " + table_prefix + "target (x varchar(255));")

connection.commit()
path = raw_input("Please specify a path for a maxflow file")
file = open(path, "r")

count = 0
for line in file:
    temp = line.split()
    if temp[0] == "n" and len(temp) == 3:
        if temp[2] == 's':
            cursor.execute("INSERT INTO " + table_prefix + "source values('" + temp[1] + "')")
        elif temp[2] == 't':
            cursor.execute("INSERT INTO " + table_prefix + "target values('" + temp[1] + "')")
    elif temp[0] == "n":
        cursor.execute("INSERT INTO " + table_prefix + "node values('" + temp[1] + "')")
    if temp[0] == "a":
        cursor.execute("INSERT INTO " + table_prefix + "edge values('" + temp[1] + "'" + "," + "'" + temp[2] + "')")
        cursor.execute(
            "INSERT INTO " + table_prefix + "cost values('" + temp[1] + "'" + "," + "'" + temp[2] + "' , " + temp[
                3] + ")")
    else:
        continue
    count += 1
    if count % 10000 == 0:
        print "Reading File Please Wait ...\n " + str(count) + " Lines were read so far."
    connection.commit()

cursor.close()
connection.close()
file.close()

model = maxflow_example.maxflow(PostgreSQLKb(db_name, db_user, db_password), Pulp, table_prefix)

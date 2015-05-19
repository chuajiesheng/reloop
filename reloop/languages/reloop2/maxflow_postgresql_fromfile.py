import psycopg2
from logkb import *
from lp import *
import maxflow_example

table_prefix = "file_"

# Initialize Database with necessary Tables and Values
db_name = raw_input("Please specifiy the name of your Database: ")
db_user = raw_input("Pease specify the Username for the Database: ")
db_password = raw_input("Specify the password if applicable: ")
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

# s designates the source and t the target , a indicates edges and cost  [[node21,node22]cost]
#n 1 s
#n 2 t
#a 3 2 999999
#a 4 2 999999
#a 5 2 999999
#a 6 2 999999

count = 0
for line in file:
    temp = line.split()
    if len(temp) >= 3:
        if temp[0] == "n" and temp[2] == "s":
            cursor.execute("INSERT INTO " + table_prefix + "source values('" + temp[1] + "')")
        if temp[0] == "n" and temp[2] == "t":
            cursor.execute("INSERT INTO " + table_prefix + "target values('" + temp[1] + "')")

        if temp[0] == "a" :
            cursor.execute("INSERT INTO " + table_prefix + "node values('" + temp[1] + "')")
            cursor.execute("INSERT INTO " + table_prefix + "node values('" + temp[2] + "')")
            cursor.execute("INSERT INTO " + table_prefix + "edge values('" + temp[1] + "'" + "," + "'" + temp[2] + "')")
            cursor.execute("INSERT INTO " + table_prefix + "cost values('" + temp[1] + "'" + "," + "'" +  temp[2] + "' , " + temp[3]  + ")")
        else:
            continue
        count += 1
        if count % 10000 == 0:
            print "Reading File Please Wait ...\n " + str(count) + " Lines were read so far."

    connection.commit()

cursor.execute("CREATE TABLE tmp (x varchar(10));")
connection.commit()
cursor.execute("INSERT INTO tmp SELECT DISTINCT * FROM " + table_prefix + "node;")
connection.commit()
cursor.execute("DROP TABLE " + table_prefix + "node;")
cursor.execute("ALTER TABLE tmp RENAME TO " + table_prefix + "node;")
connection.commit()
cursor.close()
connection.close()

model = maxflow_example.maxflow(PostgreSQLKb(db_name, db_user, db_password), Pulp)

__author__ = 'danny'

import psycopg2
from logkb import *
from lp import *
import time


#----------------------------------------------------------
# SQL Testing


#----------------------------------------------------------
# Initialize Database with necessary Tables and Values
dbname = raw_input("Please specifiy the name of your Database: ")
dbname = "dbname=" + str(dbname)
user = "user="+ raw_input("Please specify the Username for the Database: ")
password = "password=" + raw_input("Specify the password if applicable: ")
connection =  psycopg2.connect(dbname + " " + user + " " + password)
cursor = connection.cursor()


#----------------------------------------------------------
# Close Connection and Drop Tables
cursor.execute("DROP TABLE IF EXISTS node2 ")
cursor.execute("DROP TABLE IF EXISTS edge2")
cursor.execute("DROP TABLE IF EXISTS cost2")
cursor.execute("DROP TABLE IF EXISTS source2")
cursor.execute("DROP TABLE IF EXISTS target2")
connection.commit()

cursor.execute("CREATE TABLE node2 (x varchar(255));")

cursor.execute("CREATE TABLE edge2 (x varchar(255), y varchar(255));")

cursor.execute("CREATE TABLE cost2 (x varchar(255), y varchar(255), z INTEGER NOT NULL);")

cursor.execute("CREATE TABLE source2 (x varchar(255));")

cursor.execute("CREATE TABLE target2 (x varchar(255));")

connection.commit()

file = open("/home/danny/Downloads/Maxflow/maxflow.max" ,"r")

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
        if temp[0] == "n" and temp[2] == "s" :
            cursor.execute("INSERT INTO source2 values('" + temp[1] + "')")
        if temp[0] == "n" and temp[2] == "t" :
            cursor.execute("INSERT INTO target2 values('" + temp[1] + "')")

        if temp[0] == "a" :
            cursor.execute("INSERT INTO node2 values('" + temp[1] + "')")
            cursor.execute("INSERT INTO node2 values('" + temp[2] + "')")
            cursor.execute("INSERT INTO edge2 values('" + temp[1] + "'" + "," + "'" + temp[2] + "')")
            cursor.execute("INSERT INTO cost2 values('" + temp[1]+ "'" + "," + "'" +  temp[2] + "' , " + temp[3]  + ")")
        else:
            continue
        count += 1
        if count % 10000 == 0:
            print "Reading File Please Wait ...\n " + str(count) + " Lines were read so far."

    connection.commit()

cursor.execute("CREATE TABLE tmp (x varchar(10));")
connection.commit()
cursor.execute("INSERT INTO tmp SELECT DISTINCT * FROM node2;")
connection.commit()
cursor.execute("DROP TABLE node2;")
cursor.execute("ALTER TABLE tmp RENAME TO node2;")
connection.commit()

start = time.time()
# Linear Program definition

model = RlpProblem("traffic flow LP in the spirit of page 329 in http://ampl.com/BOOK/CHAPTERS/18-network.pdf",
                   LpMaximize, PostgreSQLKb("danny","danny"), Pulp)

print "\nBuilding a relational variant of the " + model.name

# declarations
X, Y, Z = sub_symbols('X', 'Y', 'Z')

flow = numeric_predicate("flow", 2)
cost = numeric_predicate("cost2", 2)

model.add_reloop_variable(flow)

source = boolean_predicate("source2", 1)
target = boolean_predicate("target2", 1)
edge = boolean_predicate("edge2", 2)
node = boolean_predicate("node2", 1)

# objective
model += RlpSum([X, Y], source(X) & edge(X, Y), flow(X, Y))

# constraints for flow preservation
outFlow = RlpSum([X, ], edge(X, Z), flow(X, Z))
inFlow = RlpSum([Y, ], edge(Z, Y), flow(Z, Y))

model += ForAll([Z, ], node(Z) & ~source(Z) & ~target(Z), inFlow |eq| outFlow)

# upper and lower bound constraints
model += ForAll([X, Y], edge(X, Y), flow(X, Y) |ge| 0)
model += ForAll([X, Y], edge(X, Y), flow(X, Y) |le| cost(X, Y))

print "The model has been built:"
print(model)

model.solve()

print "\nThe model has been solved: " + model.status() + "."

sol = model.get_solution()

end = time.time()

print "The solutions for the flow variables are:\n"
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        print key+" = "+str(value)

total = 0
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        total += value

print "\n Time needed for the grounding and solving: " + str(end - start) + " s."
print "\nThus, the maximum flow entering the traffic network at node a is "+str(sol["flow(a, b)"]+sol["flow(a, c)"])+" cars per hour."
print "\nThe total flow in the traffic network is "+str(total)+" cars per hour."
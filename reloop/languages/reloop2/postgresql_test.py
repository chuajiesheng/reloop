import psycopg2
from logkb import *
from lp import *

#----------------------------------------------------------
# SQL Testing


#----------------------------------------------------------
# Initialize Database with necessary Tables and Values
connection =  psycopg2.connect("dbname=danny user=danny")
cursor = connection.cursor()

#----------------------------------------------------------
# Close Connection and Drop Tables
cursor.execute("DROP TABLE IF EXISTS node ")
cursor.execute("DROP TABLE IF EXISTS edge")
cursor.execute("DROP TABLE IF EXISTS cost")
cursor.execute("DROP TABLE IF EXISTS source")
cursor.execute("DROP TABLE IF EXISTS target")
connection.commit()

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


# Linear Program definition

model = RlpProblem("traffic flow LP in the spirit of page 329 in http://ampl.com/BOOK/CHAPTERS/18-network.pdf",
                   LpMaximize, PostgreSQLKb("danny","danny"), Pulp)

print "\nBuilding a relational variant of the " + model.name

# declarations
X, Y, Z = sub_symbols('X', 'Y', 'Z')

flow = numeric_predicate("flow", 2)
cost = numeric_predicate("cost", 2)

model.add_reloop_variable(flow)

source = boolean_predicate("source", 1)
target = boolean_predicate("target", 1)
edge = boolean_predicate("edge", 2)
node = boolean_predicate("node", 1)

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

print "The solutions for the flow variables are:\n"
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        print key+" = "+str(value)

total = 0
for key, value in sol.iteritems():
    if "flow" in key and value > 0:
        total += value

print "\nThus, the maximum flow entering the traffic network at node a is "+str(sol["flow(a, b)"]+sol["flow(a, c)"])+" cars per hour."
print "\nThe total flow in the traffic network is "+str(total)+" cars per hour."

#----------------------------------------------------------
# Actual Testing

#cursor.execute("""SELECT * FROM cost""")
#name = "cost"
#rows = cursor.fetchall()
#print rows
#for row in rows:
#    print "  ", row[0] , row[1] , row[2]
#
#query = "SELECT column_name FROM information_schema.columns where table_name=" + name
#cursor.execute("""SELECT column_name FROM information_schema.columns where table_name=\'cost\'""")
#
#columns = cursor.fetchall()
#print columns
#rlpvar = columns.pop()

#print rlpvar[0]
#
#args = [('a',),('b',)]

#columns = zip(columns,args)
#tmpquery = []
#print columns
#for column in columns:
#    tmpquery.append(str(column[0][0]) + " = " + "\'" +str(column[1][0]) + "\'")

#print tmpquery

#tmpquery = " AND ".join([ str(a) for a in tmpquery])

#query = "SELECT " + rlpvar[0] + " FROM " + name + " WHERE " +   tmpquery
#cursor.execute(query)
#print cursor.fetchall()

#----------------------------------------------------------
# Close Connection
connection.commit()
cursor.close()
connection.close()

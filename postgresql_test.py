import psycopg2

#----------------------------------------------------------
# SQL Testing


#----------------------------------------------------------
# Initialize Database with necessary Tables and Values
connection =  psycopg2.connect("dbname=danny user=danny")
cursor = connection.cursor()

cursor.execute("CREATE TABLE nodes (x varchar(5));")
cursor.execute("INSERT INTO nodes values('a'),('b'),('c'),('d'),('e'),('f'),('g');")

cursor.execute("CREATE TABLE edges (x varchar(5), y varchar(5));")
cursor.execute("INSERT INTO edges values('a','b'),('a','c'),('b','d'),('b','e'),('c','d'),('c','f'),('d','e'),('d','f'),('e','g'),('f','g');")

cursor.execute("CREATE TABLE cost (x varchar(5), y varchar(5), z INTEGER NOT NULL);")
cursor.execute("INSERT INTO cost values('a','b',50),('a','c',100),('b','d',40),('b','e',20),('c','d',60),('c','f',20),('d','e',50),('d','f',60),('e','g',70),('f','g',70);")

cursor.execute("CREATE TABLE source (x varchar(5));")
cursor.execute("INSERT INTO source values('a');")

cursor.execute("CREATE TABLE target (x varchar(5));")
cursor.execute("INSERT INTO target values('g');")

connection.commit()


#----------------------------------------------------------
# Actual Testing

cursor.execute("""SELECT * FROM cost""")
name = "cost"
rows = cursor.fetchall()
print rows
for row in rows:
    print "  ", row[0] , row[1] , row[2]

query = "SELECT column_name FROM information_schema.columns where table_name=" + name
cursor.execute("""SELECT column_name FROM information_schema.columns where table_name=\'cost\'""")

columns = cursor.fetchall()
print columns
rlpvar = columns.pop()

print rlpvar[0]

args = [('a',),('b',)]

columns = zip(columns,args)
tmpquery = []
print columns
for column in columns:
    tmpquery.append(str(column[0][0]) + " = " + "\'" +str(column[1][0]) + "\'")

print tmpquery

tmpquery = " AND ".join([ str(a) for a in tmpquery])

query = "SELECT " + rlpvar[0] + " FROM " + name + " WHERE " +   tmpquery
cursor.execute(query)
print cursor.fetchall()

#----------------------------------------------------------
# Close Connection and Drop Tables
cursor.execute("DROP TABLE nodes")
cursor.execute("DROP TABLE edges")
cursor.execute("DROP TABLE cost")
cursor.execute("DROP TABLE source")
cursor.execute("DROP TABLE target")
connection.commit()
cursor.close()
connection.close()

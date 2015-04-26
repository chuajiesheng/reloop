import psycopg2

#----------------------------------------------------------
# SQL Testing

connection =  psycopg2.connect("dbname=danny user=danny password=dark160891")
cursor = connection.cursor()
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
import psycopg2
from reloop.languages.rlp2.logkb import *
from reloop.languages.rlp2.lp import *
import getpass
import maxflow_example

"""
Execute this file if the tables you need for solving the problem are already available in the specified database
If you chose a different prefix than "_file" four your tables please change the table_prefix accordingly
Default prefix: "file_"
"""

table_prefix = "file_"

# Initialize Database with necessary Tables and Values
db_name = raw_input("Please specifiy the name of your Database: ")
db_user = raw_input("Pease specify the Username for the Database: ")
db_password = getpass.getpass("Enter your password (Leave blank if None): ")

model = maxflow_example.maxflow(PostgreSQLKb(db_name, db_user, db_password), Pulp, table_prefix)

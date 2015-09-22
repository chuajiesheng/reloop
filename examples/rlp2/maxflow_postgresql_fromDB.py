from reloop.languages.rlp2.grounding.block import *
from reloop.solvers.lpsolver import *
import getpass
import maxflow_example


"""
Execute this file if the tables you need for solving the problem are already available in the specified database
"""


# Initialize Database with necessary Tables and Values
#db_name = raw_input("Please specifiy the name of your Database: ")
#db_user = raw_input("Pease specify the Username for the Database: ")
#db_password = getpass.getpass("Enter your password (Leave blank if None): ")

db_name= "reloop"
db_user = "reloop2"
db_password="reloop"
logkb = PostgreSQLKb(db_name, db_user, db_password)
grounder = BlockGrounder(logkb)
model = maxflow_example.maxflow(grounder, CvxoptSolver())

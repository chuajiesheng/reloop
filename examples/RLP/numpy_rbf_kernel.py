import psycopg2
import numpy as np
import time
db_name = "cora_300"
user = "danny"
password = "danny"
connection = psycopg2.connect("dbname=" + db_name + " user=" + user + " password=" + password)
cursor = connection.cursor()
cursor.execute("DROP TABLE IF EXISTS rbf_values;")
cursor.execute("CREATE TABLE rbf_values (paper1_id int , paper2_id int, rbf_value float );")
path = raw_input("Please specify a path for a cora data file: ")
file = open("../crazy/reldata/" + path, "r")

print ("Starting Kernel Computation")
def rbf_kernel(x, y, gamma=0.01):
    res = np.linalg.norm(x-y) ** 2
    res *= -1 * gamma
    return np.exp(res)

bin_vectors = {}
start = time.time()
for index, line in enumerate(file):
    temp = line.split(",")
    paper_id = temp[0]
    bin_vector = np.array(np.int32(temp[1:len(temp)-1]))
    bin_vectors[paper_id] = bin_vector

rbf_values = {}

i = 0
for paper_id, bin_vector in bin_vectors.iteritems():
    rbf_values[paper_id] = {}
    for paper_id2, bin_vector2 in bin_vectors.iteritems():
        rbf_values[paper_id][paper_id2] = rbf_kernel(bin_vector, bin_vector2)


end = time.time()
print("Time needed to compute the rbf kernel: " + str(end-start))

values = []
print ("Finished computing Kernel Values")
for p_id, k_values in rbf_values.iteritems():
    for paper_id, kernel_value in k_values.iteritems():
        values.append((p_id, paper_id, kernel_value))
    i = i + 1
    print(str(i) + " Paper_IDs verarbeitet")


cursor.execute("INSERT INTO rbf_values VALUES " +  ",".join([ "(" + str(p_id) + ", " + str(paper_id) + ", " + str(kernel_value) + ")" for p_id, paper_id, kernel_value in values]) + ";")
#cursor.execute("CREATE INDEX paper_idx ON rbf_values USING btree (paper1_id, paper2_id);")

connection.commit()
connection.close()
file.close()
exit()

// fc.h: numpy arrays from cython , double*
#include <vector>
using namespace std;

vector<double> fc( int N, const double a[], const long int b[], const long int c[], double z[] );
vector<size_t> equitablePartitionSaucyV2(const size_t mvertices, const size_t medges, const double data[], const size_t rown[], const size_t coln[], const size_t b[], int cIters = 0, int coarsest=1);
#include <limits>
#include <vector>
#include <pyublas/numpy.hpp>
#include <boost/python/class.hpp>
#include <boost/python/module.hpp>
#include <boost/python/operators.hpp>
#include <boost/python/def.hpp>
#include <boost/python/pure_virtual.hpp>
#include <boost/python/errors.hpp>
#include <boost/python/wrapper.hpp>
#include <boost/python/call.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <boost/python/suite/indexing/map_indexing_suite.hpp>
#include <boost/python/docstring_options.hpp>
#include <boost/python/enum.hpp>
#include <boost/python/numeric.hpp>
#include <boost/functional/hash.hpp>
#include <boost/unordered_map.hpp>
#include <boost/unordered_set.hpp>
#include <boost/math/special_functions/factorials.hpp>
#include <boost/math/special_functions/binomial.hpp>
#include <math.h>
#include <algorithm>
#include "_generate.h"
#include "saucy.h"
#include "amorph.h"
#include "util.h"
#include "platform.h"

#define DEBUG 0
//#include "amorph.h"
//#include "util.h"
//#include "platform.h"
//#include <numpy/ndarrayobject.h>

using namespace boost::python;
using namespace std;

struct iequal_to
    : std::binary_function<std::vector <size_t>, std::vector <size_t>, bool>
{
    bool operator()(std::vector <size_t> const& x,
        std::vector <size_t> const& y) const
    {
        return std::equal(x.begin(), x.end(), y.begin());
    }
};

struct ihash: std::unary_function<std::vector <size_t>, std::size_t>
{
    std::size_t operator()(std::vector <size_t> const& x) const
    {
        return boost::hash_range(x.begin(), x.end());;
    }
};

bool myComp (std::vector<size_t>* c1, std::vector<size_t>* c2);
bool myEqual (std::vector<size_t>* c1, std::vector<size_t>*  c2);
void recolor(std::vector< std::vector< std::vector <size_t>* >* >  colorSig, std::vector< size_t >* newWlColors );
size_t makeInd(const size_t* tupind, size_t wldim, int nvertices);
void getInd(size_t* tuple, size_t wldim, int nvertices, size_t tNo);
void computeIsotype(const size_t* tupind, size_t wldim, pyublas::numpy_vector<int> ncolors, pyublas::numpy_vector<int> ecolors, pyublas::numpy_vector<int> sprows, pyublas::numpy_vector<int> spcols, size_t* typeArray);
pyublas::numpy_vector<int> kWeisfeilerLehman(pyublas::numpy_vector<int> ncolors, pyublas::numpy_vector<int> ecolors, pyublas::numpy_vector<int> sprows, pyublas::numpy_vector<int> spcols, int wldim = 1 );
pyublas::numpy_vector<int> kwlEquitablePartitionSaucy(std::vector<size_t> data, std::vector<size_t> rown, std::vector<size_t> coln, std::vector<size_t> b, int cIters = 0, int coarsest=1 );
int gen_perm_rep_lex_init(const size_t n);
int gen_perm_rep_lex_next(size_t *vector, const size_t n);
int gen_comb_norep_lex_init(size_t *vector, const size_t n, const size_t k);
int gen_comb_norep_lex_next(size_t *vector, const size_t n, const size_t k);

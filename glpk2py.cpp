#include <limits>
#include <vector>
#include <pyublas/numpy.hpp>
#include <boost/python.hpp>
#include <numpy/arrayobject.h>
#include "numpy/arrayscalars.h"
#include "numpy/npy_math.h"
//#include "npy_config.h"
//#include "numpy/npy_3kcompat.h"
// #include <boost/python/class.hpp>
// #include <boost/python/module.hpp>
// #include <boost/python/operators.hpp>
// #include <boost/python/def.hpp>
// #include <boost/python/pure_virtual.hpp>
// #include <boost/python/errors.hpp>
// #include <boost/python/wrapper.hpp>
// #include <boost/python/call.hpp>
// #include <boost/python/suite/indexing/vector_indexing_suite.hpp>
// #include <boost/python/suite/indexing/map_indexing_suite.hpp>
// #include <boost/python/docstring_options.hpp>
// #include <boost/python/enum.hpp>
// #include <boost/python/numeric.hpp>
#include <boost/functional/hash.hpp>
#include <math.h>
#include <algorithm>
#define DEBUG 0


#include <stdio.h>            /* C input/output                       */
#include <stdlib.h>           /* C standard library                   */
#include <glpk.h>             /* GNU GLPK linear/mixed integer solver */

using namespace boost::python;
using namespace std;
enum filetype {
  MPS = 0,
  LP = 1
};
enum bounds {UPPER=GLP_UP, LOWER=GLP_LO, EQUAL=GLP_FX, UNBOUND=GLP_FR}; // ax < b, ax > b, ax = b, ax < 0
enum scaling {GEOMMEAN=GLP_SF_GM, EQUILIB=GLP_SF_EQ};

glp_prob *lp = NULL;
int numrows, numcols; 



void openLP(const std::string & fname, int format) {
  cout << fname << endl;
  lp = glp_create_prob();
  switch (format) {
    case MPS: 
      glp_read_mps(lp, GLP_MPS_FILE, NULL, (char*) fname.c_str());
      break;
    case LP:
      glp_read_lp(lp, NULL, (char*) fname.c_str());
      break;
  }
  numrows = glp_get_num_rows(lp);
  numcols = glp_get_num_cols(lp);
}


void closeLP(void) {
  if (lp) {
    glp_delete_prob(lp);
    glp_free_env();
    numrows = 0;
    numcols = 0;
  }
}
pyublas::numpy_array<double> getMatrix(bounds boundquery, int scaled) {

  assert(lp != NULL);

  pyublas::numpy_array<double>::iterator itera, iterb;
  int len = 0;

  std::vector<int> indvec (numcols+1);
  std::vector<double> datavec (numcols+1);
  

  int nonzero = glp_get_num_nz(lp);
  npy_intp dims[] = {4,0};
  int d = nonzero + numcols + 1;
  dims[1] = d; // we return variable bounds as constraints, hence the numcols.

  pyublas::numpy_array<double> sparsematrix(2,dims);

  itera = sparsematrix.begin() + 1;
  iterb = itera + 3*d;
  /*incredibly, glpk array indices start from 1...*/
  int foundrows = 0;
  int boundtype = 0;
  vector globalindvec; 
  vector globaldatavec; 

  if ((boundquery == EQUAL) || (boundquery == UNBOUND)) boundtype = 1;
  for (int i = 1; i <= numrows; i++) {
    int rowtype = glp_get_row_type(lp,i);
    if ( ( (boundtype == 1) &&   (rowtype == boundquery) ) \
      || ( (boundtype == 0) && ( (rowtype == GLP_DB) || (rowtype == boundquery) ) ) ) {


      std::fill(datavec.begin(), datavec.end(), 0); std::fill(indvec.begin(), indvec.end(), 0);
      len = glp_get_mat_row(lp, i, indvec.data(), datavec.data());
      if (!len) {
        printf("WARNING!! Zero elements in row %s of type \n", glp_get_row_name(lp,i));
        continue;
      }
      if (scaled){
        for (int p=1; p<=len; p++) {
          double tmp = *(datavec.begin()+p);
          tmp = glp_get_rii(lp,i)*tmp*glp_get_sjj(lp,*(indvec.begin()+p));
          *(datavec.begin()+p) = tmp;
        }
      }
      globalindvec.append(indvec)
      std::copy(indvec.begin() + 1, indvec.begin()+len+1, itera);
     /* for (std::vector<int>::iterator it = indvec.begin()+1; it <= indvec.begin() + len; it++) cout << *it;
      cout << endl;*/
      std::fill(itera+d, d+itera+len, foundrows);
      std::copy(datavec.begin() + 1, datavec.begin()+len+1, itera+2*d);
      
      double r = 1;
      if (scaled) r = glp_get_rii(lp,i);
      if  ((boundquery == EQUAL) || (boundquery == UPPER) ) { 
       *iterb = glp_get_row_ub(lp, i);
      } else if (rowtype == LOWER) *iterb = glp_get_row_lb(lp, i);

      itera += len;
      iterb++;
      foundrows++;
    }
    
  }
  //variable bounds as constraints.
  for (int i = 1; i <= numcols; i++) {
    int coltype = glp_get_col_type(lp,i);
    //if variable is unbounded, we don't want to return anything
    if ( ( (boundquery == EQUAL) &&  (coltype == boundquery) ) \
      || ( (boundtype == 0) && ( (coltype == GLP_DB) || (coltype == boundquery) ) ) ) {
      *itera = i;
      *(itera + d) = foundrows;
      *(itera + 2*d) = 1;
      double r = 1;
      //if (scaled) r = glp_get_rii(lp,i);
      //**************TODO: FIGURE OUT HOW TO FIX THE SCALING OF COLUMN BOUNDS***********
      if  ((boundquery == EQUAL) || (boundquery == UPPER) ) { 
        *iterb = r*glp_get_col_ub(lp, i);
      } else if (boundquery == LOWER) {
        *iterb = r*glp_get_col_lb(lp, i);
      }

      itera++;
      iterb++;
      foundrows++;


    }
  }
  sparsematrix[0] = numcols;
  sparsematrix[d] = foundrows;
  sparsematrix[2*d] = itera - sparsematrix.begin() - 1;
  sparsematrix[3*d] = iterb - sparsematrix.begin() - 3*d - 1;

  //itera = sparsematrix.begin();
  //for (  pyublas::numpy_array<double>::iterator tmp = iter; tmp < iter + 50; tmp++) cout << *tmp;
  return sparsematrix;
}

pyublas::numpy_vector<double> getObjective(int scaled) {
  assert(lp != NULL);
  pyublas::numpy_vector<double> objective(numcols);
  pyublas::numpy_vector<double>::iterator itera;
  itera = objective.begin();

  for (int i = 1; i <= numcols; i++) {
    double s = 1;
    if (scaled) s = glp_get_sjj(lp,i);
    *itera = s*glp_get_obj_coef(lp, i);
    itera++;
  }
  /*for (pyublas::numpy_vector<double>::iterator iterb = objective.begin(); iterb < objective.end(); iterb++) {
    cout << *iterb << ", ";
  }
  */
  if (glp_get_obj_dir(lp) == GLP_MIN) {
    return -1*objective;
  } else {
    return objective;
  }
}

void doScaling(scaling sctype) {
  assert(lp != NULL);
  glp_scale_prob(lp, sctype);
}

void solve() {
  assert(lp != NULL);
  glp_simplex(lp, NULL);
}


BOOST_PYTHON_MODULE(glpk2py)
{
  numeric::array::set_module_and_type( "numpy", "ndarray");
  enum_<bounds>("bounds")
        .value("UPPER", UPPER)
        .value("LOWER", LOWER)
        .value("EQUAL", EQUAL)
        .value("UNBOUND", UNBOUND);
  enum_<scaling>("scaling")
        .value("GEOMMEAN", GEOMMEAN)
        .value("EQUILIB", EQUILIB);
    
  def("getMatrix", getMatrix);
  def("openLP", openLP);
  def("closeLP", closeLP);
  def("getObjective", getObjective);
  def("doScaling", doScaling);
  def("solve", solve);
  //def("getB", getB);
  //def("getScale", doAndGetScale);

}
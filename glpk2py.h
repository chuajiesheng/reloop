#include <limits>
#include <vector>
//#include <pyublas/numpy.hpp>
#include <boost/python.hpp>
#include <numpy/arrayobject.h>
#include "numpy/arrayscalars.h"
#include "numpy/npy_math.h"
#include <boost/functional/hash.hpp>
#include <math.h>
#include <algorithm>
#define DEBUG 0


#include <stdio.h>            /* C input/output                       */
#include <stdlib.h>           /* C standard library                   */
#include <glpk.h>             /* GNU GLPK linear/mixed integer solver */


enum filetype {
  MPS = 0,
  LP = 1
};
enum bounds {UPPER=GLP_UP, LOWER=GLP_LO, EQUAL=GLP_FX, UNBOUND=GLP_FR}; // ax < b, ax > b, ax = b, ax < 0
enum scaling {GEOMMEAN=GLP_SF_GM, EQUILIB=GLP_SF_EQ};

void openLP(const std::string & fname, int format);
void closeLP(void);
std::vector<double> getMatrix(bounds boundquery, int scaled);
std::vector<double> getObjective(int scaled);
void doScaling(scaling sctype);
void solve();

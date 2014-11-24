#include "glpk2py.h"
#include <limits>
#include <vector>
#include <numpy/arrayobject.h>
#include "numpy/arrayscalars.h"
#include "numpy/npy_math.h"
#include <iostream>
#include <math.h>
#include <algorithm>
#define DEBUG 0


#include <stdio.h>            /* C input/output                       */
#include <stdlib.h>           /* C standard library                   */
#include <glpk.h>             /* GNU GLPK linear/mixed integer solver */

using namespace std;

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
   cout << "end" << endl;
}


void closeLP(void) {
  if (lp) {
    glp_delete_prob(lp);
    glp_free_env();
    numrows = 0;
    numcols = 0;
  }
}
 
vector<double> getMatrixUpper(int scaled) {
  bounds boundquery = UPPER;
  assert(lp != NULL);
  vector<double>::iterator itera, iterb;
  int len = 0;

  std::vector<int> indvec (numcols+1);
  std::vector<double> datavec (numcols+1);
  

  int nonzero = glp_get_num_nz(lp);
  //npy_intp dims[] = {4,0};
  int dims[] = {4,0};
  int d = nonzero + numcols + 1;
  dims[1] = d; // we return variable bounds as constraints, hence the numcols.

  vector<double> sparsematrix;
  sparsematrix.resize(dims[1]*dims[0],0);

  itera = sparsematrix.begin() + 1;
  iterb = itera + 3*d;
  /*incredibly, glpk array indices start from 1...*/
  int foundrows = 0;
  int boundtype = 0;

  //if ((boundquery == EQUAL) || (boundquery == UNBOUND)) boundtype = 1;
  for (int i = 1; i <= numrows; i++) {
    int rowtype = glp_get_row_type(lp,i);
    if ( ( (boundtype == 0) && ( (rowtype == GLP_DB) || (rowtype == boundquery) ) ) ) {


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
      std::copy(indvec.begin() + 1, indvec.begin()+len+1, itera);
     /* for (std::vector<int>::iterator it = indvec.begin()+1; it <= indvec.begin() + len; it++) cout << *it;
      cout << endl;*/
      std::fill(itera+d, d+itera+len, foundrows);
      std::copy(datavec.begin() + 1, datavec.begin()+len+1, itera+2*d);
      
      double r = 1;
      if (scaled) r = glp_get_rii(lp,i);
      if  ( (boundquery == UPPER) ) { 
       *iterb = glp_get_row_ub(lp, i);
      }

      itera += len;
      iterb++;
      foundrows++;
    }
    
  }
  //variable bounds as constraints.
  for (int i = 1; i <= numcols; i++) {
    int coltype = glp_get_col_type(lp,i);
    //if variable is unbounded, we don't want to return anything
    if ( ( (boundtype == 0) && ( (coltype == GLP_DB) || (coltype == boundquery) ) ) ) {
      *itera = i;
      *(itera + d) = foundrows;
      *(itera + 2*d) = 1;
      double r = 1;
      //if (scaled) r = glp_get_rii(lp,i);
      //**************TODO: FIGURE OUT HOW TO FIX THE SCALING OF COLUMN BOUNDS***********
      if  ( (boundquery == UPPER) ) { 
        *iterb = r*glp_get_col_ub(lp, i);
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
  //for (  vector<double>::iterator tmp = iter; tmp < iter + 50; tmp++) cout << *tmp;
  return sparsematrix;
}

vector<double> getMatrixLower(int scaled) {
  bounds boundquery = LOWER;
  assert(lp != NULL);
  vector<double>::iterator itera, iterb;
  int len = 0;

  std::vector<int> indvec (numcols+1);
  std::vector<double> datavec (numcols+1);
  

  int nonzero = glp_get_num_nz(lp);
  //npy_intp dims[] = {4,0};
  int dims[] = {4,0};
  int d = nonzero + numcols + 1;
  dims[1] = d; // we return variable bounds as constraints, hence the numcols.

  vector<double> sparsematrix;
  sparsematrix.resize(dims[1]*dims[0],0);

  itera = sparsematrix.begin() + 1;
  iterb = itera + 3*d;
  /*incredibly, glpk array indices start from 1...*/
  int foundrows = 0;
  int boundtype = 0;

  for (int i = 1; i <= numrows; i++) {
    int rowtype = glp_get_row_type(lp,i);
    if ( (boundtype == 0) && ( (rowtype == GLP_DB) || (rowtype == boundquery) ) ) {


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
      std::copy(indvec.begin() + 1, indvec.begin()+len+1, itera);
     /* for (std::vector<int>::iterator it = indvec.begin()+1; it <= indvec.begin() + len; it++) cout << *it;
      cout << endl;*/
      std::fill(itera+d, d+itera+len, foundrows);
      std::copy(datavec.begin() + 1, datavec.begin()+len+1, itera+2*d);
      
      double r = 1;
      if (scaled) r = glp_get_rii(lp,i);
      if (rowtype == LOWER){
         *iterb = glp_get_row_lb(lp, i);
      }

      itera += len;
      iterb++;
      foundrows++;
    }
    
  }
  //variable bounds as constraints.
  for (int i = 1; i <= numcols; i++) {
    int coltype = glp_get_col_type(lp,i);
    //if variable is unbounded, we don't want to return anything
    if ( (boundtype == 0) && ( (coltype == GLP_DB) || (coltype == boundquery) ) ) {
      *itera = i;
      *(itera + d) = foundrows;
      *(itera + 2*d) = 1;
      double r = 1;
      //if (scaled) r = glp_get_rii(lp,i);
      //**************TODO: FIGURE OUT HOW TO FIX THE SCALING OF COLUMN BOUNDS***********
      if (boundquery == LOWER) {
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
  //for (  vector<double>::iterator tmp = iter; tmp < iter + 50; tmp++) cout << *tmp;
  return sparsematrix;
}

vector<double> getMatrixEqual(int scaled) {
  bounds boundquery = EQUAL;
  assert(lp != NULL);
  vector<double>::iterator itera, iterb;
  int len = 0;

  std::vector<int> indvec (numcols+1);
  std::vector<double> datavec (numcols+1);
  

  int nonzero = glp_get_num_nz(lp);
  //npy_intp dims[] = {4,0};
  int dims[] = {4,0};
  int d = nonzero + numcols + 1;
  dims[1] = d; // we return variable bounds as constraints, hence the numcols.

  vector<double> sparsematrix;
  sparsematrix.resize(dims[1]*dims[0],0);

  itera = sparsematrix.begin() + 1;
  iterb = itera + 3*d;
  /*incredibly, glpk array indices start from 1...*/
  int foundrows = 0;
  int boundtype = 0;

  if ((boundquery == EQUAL) || (boundquery == UNBOUND)) boundtype = 1;
  for (int i = 1; i <= numrows; i++) {
    int rowtype = glp_get_row_type(lp,i);
    if ( ( (boundtype == 1) &&   (rowtype == boundquery) ) )  {


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
      std::copy(indvec.begin() + 1, indvec.begin()+len+1, itera);
     /* for (std::vector<int>::iterator it = indvec.begin()+1; it <= indvec.begin() + len; it++) cout << *it;
      cout << endl;*/
      std::fill(itera+d, d+itera+len, foundrows);
      std::copy(datavec.begin() + 1, datavec.begin()+len+1, itera+2*d);
      
      double r = 1;
      if (scaled) r = glp_get_rii(lp,i);
      if  (boundquery == EQUAL) { 
       *iterb = glp_get_row_ub(lp, i);
      }

      itera += len;
      iterb++;
      foundrows++;
    }
    
  }
  //variable bounds as constraints.
  for (int i = 1; i <= numcols; i++) {
    int coltype = glp_get_col_type(lp,i);
    //if variable is unbounded, we don't want to return anything
    if ( ( (boundquery == EQUAL) &&  (coltype == boundquery) ) ) {
      *itera = i;
      *(itera + d) = foundrows;
      *(itera + 2*d) = 1;
      double r = 1;
      //if (scaled) r = glp_get_rii(lp,i);
      //**************TODO: FIGURE OUT HOW TO FIX THE SCALING OF COLUMN BOUNDS***********
      if  (boundquery == EQUAL) { 
        *iterb = r*glp_get_col_ub(lp, i);
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
  //for (  vector<double>::iterator tmp = iter; tmp < iter + 50; tmp++) cout << *tmp;
  return sparsematrix;
}

vector<double> getMatrixUnbound(int scaled) {
  bounds boundquery = UNBOUND;
  assert(lp != NULL);
  vector<double>::iterator itera, iterb;
  int len = 0;

  std::vector<int> indvec (numcols+1);
  std::vector<double> datavec (numcols+1);
  

  int nonzero = glp_get_num_nz(lp);
  //npy_intp dims[] = {4,0};
  int dims[] = {4,0};
  int d = nonzero + numcols + 1;
  dims[1] = d; // we return variable bounds as constraints, hence the numcols.

  vector<double> sparsematrix;
  sparsematrix.resize(dims[1]*dims[0],0);

  itera = sparsematrix.begin() + 1;
  iterb = itera + 3*d;
  /*incredibly, glpk array indices start from 1...*/
  int foundrows = 0;
  int boundtype = 0;
 
  if ((boundquery == EQUAL) || (boundquery == UNBOUND)) boundtype = 1;
  for (int i = 1; i <= numrows; i++) {
    int rowtype = glp_get_row_type(lp,i);
    if ( ( (boundtype == 1) &&   (rowtype == boundquery) ) ) {


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
      std::copy(indvec.begin() + 1, indvec.begin()+len+1, itera);
     /* for (std::vector<int>::iterator it = indvec.begin()+1; it <= indvec.begin() + len; it++) cout << *it;
      cout << endl;*/
      std::fill(itera+d, d+itera+len, foundrows);
      std::copy(datavec.begin() + 1, datavec.begin()+len+1, itera+2*d);
      
      double r = 1;
      if (scaled) r = glp_get_rii(lp,i);
      if (rowtype == LOWER){
         *iterb = glp_get_row_lb(lp, i);
      }

      itera += len;
      iterb++;
      foundrows++;
    }
    
  }
  
  sparsematrix[0] = numcols;
  sparsematrix[d] = foundrows;
  sparsematrix[2*d] = itera - sparsematrix.begin() - 1;
  sparsematrix[3*d] = iterb - sparsematrix.begin() - 3*d - 1;

  //itera = sparsematrix.begin();
  //for (  vector<double>::iterator tmp = iter; tmp < iter + 50; tmp++) cout << *tmp;
  return sparsematrix;
}

vector<double> getMatrix(bounds boundquery,int scaled) {
  assert(lp != NULL);
  vector<double>::iterator itera, iterb;
  int len = 0;

  std::vector<int> indvec (numcols+1);
  std::vector<double> datavec (numcols+1);
  

  int nonzero = glp_get_num_nz(lp);
  //npy_intp dims[] = {4,0};
  int dims[] = {4,0};
  int d = nonzero + numcols + 1;
  dims[1] = d; // we return variable bounds as constraints, hence the numcols.

  vector<double> sparsematrix;
  sparsematrix.resize(dims[1]*dims[0],0);

  itera = sparsematrix.begin() + 1;
  iterb = itera + 3*d;
  /*incredibly, glpk array indices start from 1...*/
  int foundrows = 0;
  int boundtype = 0;
  //vector globalindvec; 
  //vector globaldatavec; 

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
      //globalindvec.append(indvec)
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


vector<double> getObjective(int scaled) {
  assert(lp != NULL);
  vector<double> objective(numcols);
  vector<double>::iterator itera;
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
    transform(objective.begin(),objective.end(),objective.begin(),bind1st(multiplies<int>(),-1));
    return objective;
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


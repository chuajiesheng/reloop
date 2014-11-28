/*! \file */ 

#include <limits>
#include <vector>
#include<iostream>
#include<assert.h>
#include <math.h>
#include <algorithm>
#define DEBUG 0


#include <stdio.h>            /* C input/output                       */
#include <stdlib.h>           /* C standard library                   */
#include <glpk.h>             /* GNU GLPK linear/mixed integer solver */

///TODO
///
enum filetype {
  MPS = 0,  ///< TODO
  LP = 1    ///< TODO
};
/// TODO
///
enum bounds {
    UPPER=GLP_UP, ///< TODO
    LOWER=GLP_LO, ///< TODO
    EQUAL=GLP_FX, ///< TODO
    UNBOUND=GLP_FR///< TODO
}; // ax < b, ax > b, ax = b, ax < 0

///TODO
///
enum scaling {
    GEOMMEAN=GLP_SF_GM, ///< TODO
    EQUILIB=GLP_SF_EQ   ///< TODO
};

///@brief Opens a specified LP by calling the constructor of the GLPK solver.
///@param fname The name of the file to be opened
///@param format The filetype of given file either MPS or LP are valid (see enum filetype)
///
void openLP(const std::string & fname, int format);

///@brief Closes the given LP by deallocating memory
///
///
///
void closeLP(void);

///@brief Calculates properties of a given LP depending on the bounds Flag
///@param boundquery A Flag, which indicates which matrix is going to be calculated
///@param scaled An integer, which indicates a scaled matrix(LP)
///@return A Vector (structure) equivalent to a matrix with 4 rows
std::vector<double> getMatrix(bounds boundquery, int scaled);

///@brief Calculates the objective of a given LP
///@param scaled An integer, which indicates a scaled matrix(LP)
///@return The objective of a given LP as vector
///
std::vector<double> getObjective(int scaled);

///@brief Scales the given LP
///@param sctype A Flag, which indicates which scaling type is to be used
///
void doScaling(scaling sctype);

///@brief Solves the given LP with an off-the-shelf LP-Solver e.g. Gnu glpk
///
///
///
void solve();



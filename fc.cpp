// fc.cpp: numpy arrays from cython to std::vector<double>

#include "fc.h"
#include <stdio.h>
#include <cstring>
#include <iostream>
#include <vector>
#include <map>
#include <iterator>
#include <cassert>
#include <math.h>
#include <algorithm>
#include "_generate.h"
#include "saucy.h"
#include "amorph.h"
#include "util.h"
#include "platform.h"
extern void add_edge(int a, int b, int *adj, int *edg);
extern int dupe_check(int n, int *adj, int *edg);
extern void amorph_print_automorphism( int n, const int *gamma, int nsupp, const int *support,
        struct amorph_graph *g, char *marks);
extern void amorph_graph_free(struct amorph_graph *g);
extern int saucy_with_graph(struct amorph_graph *g, int smode, int qmode, int rep, int coarsest, int* result); 
extern int init_fixadj1(int n, int *adj);
extern void init_fixadj2(int n, int e, int *adj);

using namespace std;

vector<double> fc( int N, const double a[], const long int b[], const long int c[], double z[] ){
    printf("This C++-Function assigns some values to an empty vector and returns it to Python Code \n");
     
     double d[sizeof(a)];

     int count = 0;
     cout << "sizeof z" << sizeof(a) << endl;
     vector<double> result (sizeof(z),0); 
     cout << "Building std::Vector<double> in C++ function ... "; 
     for(vector<double>::iterator i = result.begin(); i != result.end(); i++){	
        cout << endl << "***" << count << "****" << endl;
		*i = a[count] + count + 0.123456 ;
		cout << "[" << *i << "]" << " ";
		d[count] = a[count];
		count ++;
	}
       cout << endl;
       cout << "Values from Python Numpy Arrays :" << endl;
     for(int i = 0 ; i <= sizeof(a) ; i++){
	cout << "a : [" << a[i] << "]";	
	cout << " b : [" << b[i] << "]";	
	cout << " c : [" << c[i] << "]" << endl;	
	}
     cout << endl;
     return result;
}
vector<size_t> equitablePartitionSaucyV2(const size_t mvertices, const size_t medges, const double data[], const size_t rown[], const size_t coln[], const size_t b[], int cIters, int coarsest)
{
    size_t Aijd;
    double Aij;
    double bb;
    size_t ncols;
    bool diagfound = false;
    std::vector<size_t> row;
    std::vector<size_t> tmpdiag;
    std::vector<size_t> diag;
    std::vector<double> tuple;
    int* result;

    std::map<std::vector<double>, int> colorMap;
    map<std::vector<double>, int>::iterator colorsIter;
    std::map<size_t, size_t> varRepr;
    map<size_t, size_t >::iterator mapIter;

    //scan once to find the values for the diagonal entries and keep them in a dense vector
    //if this turns out to be too much memory, there are other options
    diag.clear();


    //printf("saucy: ping 1\n");
    /* Initialize Saucy datastructure */
    struct amorph_graph *g = NULL;
    int tmpe, i, j, oldi, p, k, colorcount, *aout, *eout, *ain, *ein, *colors;

    int overestN = medges + mvertices; // we replace the colored edges by vertices
    int overestE = medges * 2; // for every new colored edge-vertex we have 2 uncolored edges
    int n = 0;
    
    oldi = -1;
    int digraph = 0;
    g = (struct amorph_graph *) malloc(sizeof(struct amorph_graph));
    aout = (int *) calloc(digraph ? (2*overestN+2) : (overestN+1), sizeof(int));
    eout = (int *) malloc(2 * overestE * sizeof(int));
    colors = (int *) malloc(overestN * sizeof(int));

    memset(colors,0,overestN * sizeof(int) );
    //if (!g || !aout || !eout || !colors) goto out_free;

    ain = aout;
    ein = eout;

    //printf("saucy: graph tmpe: %d, tmpn: %d \n", overestE, overestN);
    colorMap.clear();
    colorcount = 0;
    int e = 0;
    for(p = 0; p < medges; ++p) {
        int tmpcol;
        i = coln[p]; j = rown[p];
        if ( i == j ) {
            tuple.clear();
            tuple.push_back(b[j]);
            tuple.push_back(data[p]);
            colorsIter = colorMap.find(tuple);
            if (colorsIter == colorMap.end()) {
                tmpcol = colorcount++;
                colorMap[tuple] = tmpcol;
            } else {
                tmpcol = colorMap[tuple];
            }
            colors[i] = tmpcol;
            //printf("node i=%d j=%d: col=%d\n",i,j,tmpcol);
         } else if (i<j) {
            //printf("i,j,e : %d %d %d\n",j,i,e);
            tuple.clear();
            tuple.push_back(data[p]);
            colorsIter = colorMap.find(tuple);
            if (colorsIter == colorMap.end()) {
                tmpcol = colorcount++;
                colorMap[tuple] = tmpcol;
            } else {
                tmpcol = colorMap[tuple];
            }
            colors[mvertices + e] = tmpcol;
            //printf("edge i=%d j=%d: col=%d, e=%d, colorindex:%d\n",i,j,tmpcol,e,mvertices + e);
            ++aout[i]; ++ain[mvertices + e];
            ++aout[mvertices + e]; ++ain[j];
            e++; 
         }
        }
    n = mvertices + e;
    e *= 2;
//  for(p = 0; p< n; p++) printf("node %d adj %d\n", p, aout[p]);
    init_fixadj1(n, aout);
//  for(p = 0; p< n; p++) printf("node %d adj %d\n", p, aout[p]);
    tmpe = 0;
    for(p = 0; p < medges; ++p) {
        i = coln[p]; j = rown[p];
        if (i<j) {
            eout[aout[i]++] = mvertices + tmpe;
            ein[ain[mvertices + tmpe]++] = i;
            eout[aout[mvertices + tmpe]++] = j;
            ein[ain[j]++] = mvertices + tmpe;
            tmpe++;
        }
    }
    init_fixadj2(n, 2 * e, aout);

    printf("nodes %d\n", n);
    printf("edges %d\n", e);
    //printf("saucy: colors\n");
    //for (p=0; p<n; p++) printf("node %d col %d\n", p, colors[p]);
    g->sg.n = n;
    g->sg.e = e;
    g->sg.adj = aout;
    g->sg.edg = eout;
    g->colors = colors;
    g->consumer = amorph_print_automorphism;
    g->free = amorph_graph_free;
    g->stats = NULL;
    if (dupe_check(mvertices+e+1, aout, eout)) printf("dupe check failed?\n");
    result = (int *) malloc(n * sizeof(int));
    saucy_with_graph(g, 1, 0, 1, coarsest, result);


    cout << "building block matrix" << endl;
    std::vector<size_t> res(n);
    varRepr.clear();
    i = 0;
    for (p = 0; p<n; ++p) {
        size_t hashval = result[p];
        size_t newcol;
        mapIter = varRepr.find(hashval);
        if (mapIter == varRepr.end()) {
            varRepr[hashval] = i;
            newcol = i;
            ++i;
        } else {
            newcol = varRepr[hashval];
        }
        res[p] = newcol;
    }
    return res;
                        }

    //Attention: here b is supposed to indicate a coloring, i.e. it should contain all integers 0...p
    /* {
    size_t ncols;
    bool diagfound = false;
    std::vector<size_t> row;
    std::vector<size_t> tmpdiag;
    std::vector<size_t> diag;
    std::vector<double> tuple;
    size_t* result;

    std::map<std::vector<double>, size_t> colorMap;
    map<std::vector<double>, size_t>::iterator colorsIter;
    std::map<size_t, size_t> varRepr;
    map<size_t, size_t >::iterator mapIter;

    //scan once to find the values for the diagonal entries and keep them in a dense vector
    //if this turns out to be too much memory, there are other options
    diag.clear();


    //printf("saucy: ping 1\n");
    struct amorph_graph *g = NULL;
    int tmpe, i, j, oldi, p, k, colorcount, *aout, *eout, *ain, *ein, *colors;

    int overestN = medges + mvertices; // we replace the colored edges by vertices
    int overestE = medges * 2; // for every new colored edge-vertex we have 2 uncolored edges
    int n = 0;
    
    oldi = -1;
    int digraph = 0;
    g = (struct amorph_graph *) malloc(sizeof(struct amorph_graph));
    aout = (int *) calloc(digraph ? (2*overestN+2) : (overestN+1), sizeof(int));
    eout = (int *) malloc(2 * overestE * sizeof(int));
    colors = (int *) malloc(overestN * sizeof(int));

    memset(colors,0,overestN * sizeof(int) );
    //if (!g || !aout || !eout || !colors) goto out_free;

    ain = aout;
    ein = eout;

    //printf("saucy: graph tmpe: %d, tmpn: %d \n", overestE, overestN);
    colorcount = 0;
    for (i = 0; i < mvertices; i++) {
        colors[i] = b[i];
        if (b[i] > colorcount) colorcount = b[i];
    }
    colorcount++;
    
    int e = 0;
    for(p = 0; p < medges; ++p) {
        i = coln[p]; j = rown[p];
            {
            colors[mvertices + e] = data[p] + colorcount;
            // printf("edge i=%d j=%d: col=%d, e=%d, index:%d\n",i,j,data[p] + colorcount,e,mvertices + e);
            ++aout[i]; ++ain[mvertices + e];
            ++aout[mvertices + e]; ++ain[j];
            e++; 
         }
        }
    n = mvertices + e;
    e *= 2;
    init_fixadj1(n, aout);
    tmpe = 0;
    for(p = 0; p < medges; ++p) {
        i = coln[p]; j = rown[p];
        eout[aout[i]++] = mvertices + tmpe;
        ein[ain[mvertices + tmpe]++] = i;
        eout[aout[mvertices + tmpe]++] = j;
        ein[ain[j]++] = mvertices + tmpe;
        tmpe++;
    
    }

    init_fixadj2(n, 2 * e, aout);

    printf("nodes %d\n", n);
    printf("edges %d\n", e);
    //printf("saucy: colors\n");
    //for (p=0; p<n; p++) printf("node %d col %d\n", p, colors[p]);
    g->sg.n = n;
    g->sg.e = e;
    g->sg.adj = aout;
    g->sg.edg = eout;
    g->colors = colors;
    g->consumer = amorph_print_automorphism;
    g->free = amorph_graph_free;
    g->stats = NULL;
    if (dupe_check(n, aout, eout)) printf("dupe check failed?\n");
    result = (int *) malloc(n * sizeof(int));
    saucy_with_graph(g, 1, 0, 1, coarsest, result);


    cout << "building block matrix" << endl;
    std::vector<size_t> res(n);
    varRepr.clear();
    i = 0;
    for (p = 0; p<n; ++p) {
        size_t hashval = result[p];
        size_t newcol;
        mapIter = varRepr.find(hashval);
        if (mapIter == varRepr.end()) {
            varRepr[hashval] = i;
            newcol = i;
            ++i;
        } else {
            newcol = varRepr[hashval];
        }
        res[p] = newcol;
    }

    
    // g->free(g);
    return res;
                        }*/

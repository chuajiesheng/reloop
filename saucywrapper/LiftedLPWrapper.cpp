/*
    Copyright (C) 2009
    Babak Ahmadi [babak dot ahmadi at iais dot fraunhofer dot de]
    Fabian Hadiji [fabian dot hadiji at iais dot fraunhofer dot de]
    Kristian Kersting (coordination) [kristian dot kersting at iais dot fraunhofer dot de]

    STREAM Project at
        Fraunhofer IAIS, Sankt Augustin, Germany, and
        KDML, Unversity of Bonn, Germany

    This file is part of libSTREAM.

    libSTREAM is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    libSTREAM is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
 */

#include "LiftedLPWrapper.hpp"
//#include <numpy/ndarrayobject.h>

using namespace boost::python;
using namespace std;
extern void add_edge(int a, int b, int *adj, int *edg);
extern int dupe_check(int n, int *adj, int *edg);
extern void amorph_print_automorphism( int n, const int *gamma, int nsupp, const int *support,
		struct amorph_graph *g, char *marks);
extern void amorph_graph_free(struct amorph_graph *g);
extern int saucy_with_graph(struct amorph_graph *g, int smode, int qmode, int rep, int coarsest, int* result); 
extern int init_fixadj1(int n, int *adj);
extern void init_fixadj2(int n, int e, int *adj);

pyublas::numpy_vector<int> blockMatrixFromDenseArray(pyublas::numpy_vector<double> A,pyublas::numpy_vector<double> b, size_t cIters = 0 )
								{
	assert(A.ndim() == 2);
	size_t n = A.dims()[0];
	assert(A.dims()[1] == n);
	assert(b.size() == n);

	size_t p,i,j, oldi;
	size_t Aijd;
	oldi = -1;
	double Aij;
	size_t ncols;
	size_t diag[n];
	size_t tmpdiag[n];
	size_t row[n];
	std::vector<size_t> tuple;
	std::map<size_t, size_t> varRepr;
	map<size_t, size_t >::iterator mapIter;

	boost::hash<std::vector<size_t> > showMeTheMoney;
	boost::hash<std::vector<size_t> > showMeTheRow;


	//scan once to find the values for the diagonal entries and keep them in a dense vector
	//if this turns out to be too much memory, there are other options
	for(p = 0; p < n; ++p){
		Aij = A.sub(p,p) * b[p];
		diag[p] = *((size_t *) &Aij);
	}
	//	for (uint u = 0; u<diag.size(); u++) cout << diag[u] << " ";
	//okay we have the diagonal, now the real stuff
	bool converged = false;
	size_t iter = 1;
	varRepr.clear();
	cout << "begin other shit" << endl;
	while (!converged) {
		cout << "current iteration: " << iter << endl;
		ncols = varRepr.size();
		cout << "ncols: " << ncols << endl;
		varRepr.clear();
		for(i = 0; i < n; ++i){
			size_t hashval = 0;
			for (j = 0; j<n; ++j) {
				tuple.clear();
				Aij = A.sub(i,j);
				Aijd = *((size_t *) &Aij);
				tuple.push_back(Aijd);
				if (diag[i]>diag[j]) {
					tuple.push_back(diag[i]);
					tuple.push_back(diag[j]);
				} else {
					tuple.push_back(diag[j]);
					tuple.push_back(diag[i]);
				}
				row[j] = showMeTheMoney(tuple);

			}
			sort(row, row+n);
			tmpdiag[i] = boost::hash_range(row, row+n);
			mapIter = varRepr.find(tmpdiag[i]);
			if (mapIter == varRepr.end()) {
				varRepr[tmpdiag[i]] = 1;
			} else {
				mapIter->second += 1;
			}

		}
		for (p = 0;p<n;p++) diag[p] = tmpdiag[p];

		if (iter==cIters) {
			cout << "limit of iterations reached: " << iter << endl;
			break;
		}
		if (ncols == varRepr.size()) {
			converged = true;
			cout << "number of colors after clustering: " << ncols << endl;
		}
		iter++;
		//		for (uint u = 0; u<diag.size(); u++) cout << diag[u] << " ";
	}
	cout << "building block matrix" << endl;
	pyublas::numpy_vector<int> res(n);
	varRepr.clear();
	i = 0;
	for (p = 0; p<n; ++p) {
		size_t hashval = diag[p];
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


pyublas::numpy_vector<int> removeRedundantDenseRows(pyublas::numpy_vector<double> A,pyublas::numpy_vector<double> b) {
	assert(A.ndim() == 2);
	size_t n = A.dims()[0];
	size_t m = A.dims()[1];
	assert(b.size() == n);

	size_t p,i,j, oldi;
	size_t Aijd;
	oldi = -1;
	double Aij;
	size_t ncols;
	size_t rowsig[n];
	std::map<size_t, size_t> varRepr;
	map<size_t, size_t >::iterator mapIter;

	//	boost::hash<std::vector<size_t> > showMeTheMoney;
	//	boost::hash<std::vector<size_t> > showMeTheRow;

	for(i = 0; i < n; ++i) {
		size_t hashvalue = 0;
		for (j = 0; j < m; ++j) {
			boost::hash_combine(hashvalue, A.sub(i,j));
		}
		rowsig[i] = hashvalue;
	}
	vector<size_t> tmp;
	varRepr.clear();
	for(p = 0; p < n; ++p){
		mapIter = varRepr.find(rowsig[p]);
		if (mapIter == varRepr.end()) {
			varRepr[rowsig[p]] = true;
			tmp.push_back(p);
		}
	}
	pyublas::numpy_vector<int> res(tmp.size());
	for (p=0;p<tmp.size();p++){
		res[p] = tmp[p];

	}

	return res;



}
pyublas::numpy_vector<int> removeRedundantSparseRows(pyublas::numpy_vector<double> data, pyublas::numpy_vector<int> rown, pyublas::numpy_vector<int> coln, pyublas::numpy_vector<double> b) {
	size_t k = data.size();
	assert(k == rown.size());
	assert(k == coln.size());
	uint n = b.size();

	size_t p,i,j, oldi;
	size_t Aijd;
	oldi = -1;
	double Aij;
	std::vector<size_t> row;
	std::vector<size_t> rowsig;
	std::vector<size_t> tuple;
	std::map<size_t, bool> varRepr;
	map<size_t, bool >::iterator mapIter;
	boost::hash<std::vector<size_t> > showMeTheMoney;
	for(p = 0; p < k; ++p){
		oldi = rown[p];
		row.clear();
		while (p < k) {
			i = rown[p];
			if (i!=oldi) {
				p--;
				break;
			}
			j = coln[p];
			tuple.clear();
			Aij = data[p];
			Aijd = *((size_t *) &Aij);
			tuple.push_back(Aijd);
			tuple.push_back(j);
			row.push_back(showMeTheMoney(tuple));
			++p;
		}
		tuple.clear();
		Aij = b[oldi];
		Aijd = *((size_t *) &Aij);
		row.push_back(Aijd);
		rowsig.push_back(showMeTheMoney(row));
	}
	std::vector<size_t> tmp;
	tmp.clear();
	varRepr.clear();
	for(p = 0; p < rowsig.size(); ++p){
		mapIter = varRepr.find(rowsig[p]);
		if (mapIter == varRepr.end()) {
			varRepr[rowsig[p]] = true;
			tmp.push_back(p);
		}
	}
	pyublas::numpy_vector<int> res(tmp.size());
	for (p=0;p<tmp.size();p++){
		res[p] = tmp[p];

	}

	return res;



}

pyublas::numpy_vector<double> testSaucy(pyublas::numpy_vector<double> data, pyublas::numpy_vector<int> rown) 
	{
		return data;
	}

pyublas::numpy_vector<int> equitablePartitionSaucyV2(pyublas::numpy_vector<int> data, pyublas::numpy_vector<int> rown, pyublas::numpy_vector<int> coln, pyublas::numpy_vector<int> b, int cIters = 0, int coarsest=1 )
	//Attention: here b is supposed to indicate a coloring, i.e. it should contain all integers 0...p
	{

	int medges = data.size();
	printf("medges %d\n",medges);
	printf("rown %d\n",rown.size());
	printf("coln %d\n",coln.size());
	assert(medges == rown.size());
	assert(medges == coln.size());
	int mvertices = b.size();
	printf("mvertices %d\n",mvertices);

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

	boost::hash<std::vector<size_t> > showMeTheMoney;
	boost::hash<std::vector<double> > hashColor;
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
	pyublas::numpy_vector<int> res(n);
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
						}


//Backup copy***************
pyublas::numpy_vector<int> equitablePartitionSaucy(pyublas::numpy_vector<double> data, pyublas::numpy_vector<int> rown, pyublas::numpy_vector<int> coln, pyublas::numpy_vector<int> b, int cIters = 0, int coarsest=1 )
	{
	int medges = data.size();
	printf("medges %d\n",medges);
	printf("rown %d\n",rown.size());
	printf("coln %d\n",coln.size());
	assert(medges == rown.size());
	assert(medges == coln.size());
	int mvertices = b.size();

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

	boost::hash<std::vector<size_t> > showMeTheMoney;
	boost::hash<std::vector<double> > hashColor;
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
//	for(p = 0; p< n; p++) printf("node %d adj %d\n", p, aout[p]);
	init_fixadj1(n, aout);
//	for(p = 0; p< n; p++) printf("node %d adj %d\n", p, aout[p]);
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
	pyublas::numpy_vector<int> res(n);
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

pyublas::numpy_vector<int> equitablePartitionSaucyUnlabeled(pyublas::numpy_vector<int> coln, pyublas::numpy_vector<int> rown, pyublas::numpy_vector<int> b, int cIters = 0, int coarsest=1 )
	{

	std::map<size_t, size_t> varRepr;
	map<size_t, size_t >::iterator mapIter;

	int i, j, k, n, e, p, *aout, *eout, *ain, *ein, *colors, *result;
	struct amorph_graph *g = NULL;
	int digraph = 0;


	/* Read the sizes */

	e = rown.size();
	n = b.size();
	
	printf("edges %d\n",e);
	printf("rown %d\n",rown.size());
	printf("coln %d\n",coln.size());
	printf("nodes %d\n", n);
	assert(e == rown.size());
	assert(e == coln.size());

	/* Allocate everything */
	g = (struct amorph_graph *) malloc(sizeof(struct amorph_graph));
	aout = (int *)calloc(digraph ? (2*n+2) : (n+1), sizeof(int));
	eout = (int *)malloc(2 * e * sizeof(int));
	colors = (int *)malloc(n * sizeof(int));
	assert(!(!g || !aout || !eout || !colors));

	g->sg.n = n;
	g->sg.e = e;
	g->sg.adj = aout;
	g->sg.edg = eout;
	g->colors = colors;

	ain = aout + (digraph ? n+1 : 0);
	ein = eout + (digraph ? e : 0);

	/* Initial coloring with provided splits */
	for (i = 0; i < n; i++) {
		colors[i] = b[i];
	}

	/* Count the size of each adjacency list */
	for (i = 0; i < e; ++i) {
		// cout << coln[i] << "  -- " << rown[i] << endl;
		j = coln[i]; k = rown[i];
		++aout[j]; ++ain[k];
	}
	//for(i = 0; i< n; i++) printf("node %d adj %d\n", i, aout[i]);
	//printf("=================FIXING===================\n");
	/* Fix that */
	init_fixadj1(n, aout);
	//for(i = 0; i< n; i++) printf("node %d adj %d\n", i, aout[i]);
	if (digraph) init_fixadj1(n, ain);

	/* Insert adjacencies */
	for (i = 0; i < e; ++i) {
		j = coln[i]; k = rown[i];
		if (j == k) printf("index %d is wrong\n",i);
		/* Simple input validation: check vertex values */
		if (j >= n || j < 0) {
			warn("invalid vertex in input: %d", j);
		}
		if (k >= n || k < 0) {
			warn("invalid vertex in input: %d", k);
		}

		eout[aout[j]++] = k;
		ein[ain[k]++] = j;
	}

	/* Fix that too */
	if (digraph) {
		init_fixadj2(n, e, aout);
		init_fixadj2(n, e, ain);
	}
	else {
		init_fixadj2(n, 2 * e, aout);
	}

	/* Check for duplicate edges */
	assert(!dupe_check(n, aout, eout));

	/* Assign the functions */
	g->consumer = amorph_print_automorphism;
	g->free = amorph_graph_free;
	g->stats = NULL;
	result = (int *) malloc(n * sizeof(int));
	saucy_with_graph(g, 1, 0, 1, coarsest, result);


	cout << "building block matrix" << endl;
	pyublas::numpy_vector<int> res(n);
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
	// saucy_free(s);
	// g->free(g);
	return res;

	
}



/*

	int medges = rown.size();
	printf("medges %d\n",medges);
	printf("rown %d\n",rown.size());
	printf("coln %d\n",coln.size());
	assert(medges == rown.size());
	assert(medges == coln.size());
	int mvertices = b.size();

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

	boost::hash<std::vector<size_t> > showMeTheMoney;
	boost::hash<std::vector<double> > hashColor;
	//scan once to find the values for the diagonal entries and keep them in a dense vector
	//if this turns out to be too much memory, there are other options
	diag.clear();


	//printf("saucy: ping 1\n");
	/* Initialize Saucy datastructure */
	/*
	struct amorph_graph *g = NULL;
	int tmpe, i, j, oldi, p, k, colorcount, *aout, *eout, *ain, *ein, *colors;
	
	oldi = -1;
	int digraph = 0;
	g = (struct amorph_graph *) malloc(sizeof(struct amorph_graph));
	aout = (int *) calloc(digraph ? (2*mvertices+2) : (mvertices+1), sizeof(int));
	eout = (int *) malloc(2 * medges * sizeof(int));
	colors = (int *) malloc(mvertices * sizeof(int));

	memset(colors,0,mvertices * sizeof(int) );
	//if (!g || !aout || !eout || !colors) goto out_free;

	ain = aout;
	ein = eout;

	//printf("saucy: graph tmpe: %d, tmpn: %d \n", overestE, overestN);
	colorMap.clear();


	for(p = 0; p < mvertices; ++p) {
		colors[p] = b[p];
	}
	for(p = 0; p < medges; ++p) {
		i = coln[p]; j = rown[p];
		++aout[i]; ++ain[j];
		}
//	for(p = 0; p< n; p++) printf("node %d adj %d\n", p, aout[p]);
	init_fixadj1(mvertices, aout);
//	for(p = 0; p< n; p++) printf("node %d adj %d\n", p, aout[p]);
	for(p = 0; p < medges; ++p) {
		i = coln[p]; j = rown[p];
		if (i<j) {
			eout[aout[i]++] = j;
			ein[ain[j]++] = i;
/*			eout[aout[i]++] = j;
			ein[ain[j]++] = i;*/
			/*
		}
	}
	init_fixadj2(mvertices, medges, aout);

	printf("nodes %d\n", mvertices);
	printf("edges %d\n", medges);
	//printf("saucy: colors\n");
	//for (p=0; p<n; p++) printf("node %d col %d\n", p, colors[p]);
	g->sg.n = mvertices;
	g->sg.e = medges;
	g->sg.adj = aout;
	g->sg.edg = eout;
	g->colors = colors;
	g->consumer = amorph_print_automorphism;
	g->free = amorph_graph_free;
	g->stats = NULL;
	if (dupe_check(mvertices+1, aout, eout)) printf("dupe check failed?\n");
	result = (int *) malloc(mvertices * sizeof(int));
	saucy_with_graph(g, 1, 0, 1, coarsest, result);


	cout << "building block matrix" << endl;
	pyublas::numpy_vector<int> res(mvertices);
	varRepr.clear();
	i = 0;
	for (p = 0; p<mvertices; ++p) {
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
*/

pyublas::numpy_vector<int> blockMatrixFromSparseArray(pyublas::numpy_vector<double> data, pyublas::numpy_vector<int> rown, pyublas::numpy_vector<int> coln, pyublas::numpy_vector<double> b, size_t cIters = 0 )
						{
	size_t k = data.size();
	assert(k == rown.size());
	assert(k == coln.size());
	uint n = b.size();

	size_t p,i,j, oldi;
	size_t Aijd;
	oldi = -1;
	double Aij;
	double bb;
	size_t ncols;
	bool diagfound = false;
	std::vector<size_t> row;
	std::vector<size_t> tmpdiag;
	std::vector<size_t> diag;
	std::vector<size_t> tuple;
	std::map<size_t, size_t> varRepr;
	map<size_t, size_t >::iterator mapIter;

	boost::hash<std::vector<size_t> > showMeTheMoney;
	cout << "blaabnasdfs " << sizeof(size_t) << endl;


	//scan once to find the values for the diagonal entries and keep them in a dense vector
	//if this turns out to be too much memory, there are other options
	diag.clear();
	for(p = 0; p < k; ++p){
		//		cout << "p: " << p  << " diagsize: " << diag.size() << endl;
		diagfound = false;
		while (p < k) {
			i =rown[p];
			//			cout << i << endl;
			if (i-oldi>1) {
				p--;
				break;
			}
			j = coln[p];
			if (i==j) {
				diagfound = true;
				//				Aij = double(*(::npy_float64*)PyArray_GETPTR1(data.ptr(), p));
				//BECAUSE I CAN!!!!
				Aij = data[p];
				bb = b[i];
				Aij*=bb;
				//and this here kids is called shitcasting
				Aijd = *((size_t *) &Aij);
				//				cout << Aijd << endl;
				diag.push_back(Aijd);
			}
			++p;
		}
		if ((!diagfound) || (i-oldi>1)) {
			uint u = 1;
			if (diagfound) u = 2;
			for (uint q=oldi+u;q<i;q++) {
				diag.push_back(0);
			}
		}
		oldi = i-1;


	}
	//	for (uint u = 0; u<diag.size(); u++) cout << diag[u] << " ";
	tmpdiag.clear();
	tmpdiag=diag;
	//okay we have the diagonal, now the real stuff
	bool converged = false;
	size_t iter = 1;
	varRepr.clear();
	cout << "begin other shit" << endl;
	while (!converged) {
		cout << "current iteration: " << iter << endl;
		ncols = varRepr.size();
		cout << "ncols: " << ncols << endl;
		varRepr.clear();
		for(p = 0; p < k; ++p){
			oldi = rown[p];
			row.clear();
			while (p < k) {
				i = rown[p];
				if (i!=oldi) {
					p--;
					break;
				}
				j = coln[p];
				tuple.clear();
				Aij = data[p];
				Aijd = *((size_t *) &Aij);
				tuple.push_back(Aijd);
				if (diag[i]>diag[j]) {
					tuple.push_back(diag[i]);
					tuple.push_back(diag[j]);
				} else {
					tuple.push_back(diag[j]);
					tuple.push_back(diag[i]);
				}
				row.push_back(showMeTheMoney(tuple));
				++p;
			}
			sort(row.begin(), row.end());
			tmpdiag[oldi] = showMeTheMoney(row);
			mapIter = varRepr.find(tmpdiag[oldi]);
			if (mapIter == varRepr.end()) {
				varRepr[tmpdiag[oldi]] = 1;
			} else {
				mapIter->second += 1;
			}

		}
		diag.clear();
		diag = tmpdiag;
		//		tmpdiag.clear();

		if (iter==cIters) {
			cout << "limit of iterations reached: " << iter << endl;
			break;
		}
		if (ncols == varRepr.size()) {
			converged = true;
			cout << "number of colors after clustering: " << ncols << endl;
		}
		iter++;
		//		for (uint u = 0; u<diag.size(); u++) cout << diag[u] << " ";
	}
	cout << "building block matrix" << endl;
	pyublas::numpy_vector<int> res(diag.size());
	varRepr.clear();
	i = 0;
	for (p = 0; p<diag.size(); ++p) {
		size_t hashval = diag[p];
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




pyublas::numpy_vector<int> kwlEquitablePartitionSaucy(std::vector<size_t> data, std::vector<size_t> rown, std::vector<size_t> coln, std::vector<size_t> b, int cIters, int coarsest)
	{
	int medges = data.size();
	printf("medges %d\n",medges);
	printf("rown %d\n",rown.size());
	printf("coln %d\n",coln.size());
	assert(medges == rown.size());
	assert(medges == coln.size());
	int mvertices = b.size();

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

	boost::hash<std::vector<size_t> > showMeTheMoney;
	boost::hash<std::vector<double> > hashColor;
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
//	for(p = 0; p< n; p++) printf("node %d adj %d\n", p, aout[p]);
	init_fixadj1(n, aout);
//	for(p = 0; p< n; p++) printf("node %d adj %d\n", p, aout[p]);
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
	pyublas::numpy_vector<int> res(n);
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

BOOST_PYTHON_MODULE(LiftedLPWrapper)
{
  numeric::array::set_module_and_type( "numpy", "ndarray");
  def("blockMatrixFromSparseArray", blockMatrixFromSparseArray);
  def("removeRedundantSparseRows", removeRedundantSparseRows);
  def("blockMatrixFromDenseArray", blockMatrixFromDenseArray);
  def("equitablePartitionSaucy", equitablePartitionSaucy);
  def("equitablePartitionSaucyUnlabeled", equitablePartitionSaucyUnlabeled);
  def("removeRedundantDenseRows", removeRedundantDenseRows);
  def("removeRedundantDenseRows", removeRedundantDenseRows);
  def("equitablePartitionSaucyV2",equitablePartitionSaucyV2);
  def("kWeisfeilerLehman", kWeisfeilerLehman);

}

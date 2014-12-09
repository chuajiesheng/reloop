#include "LiftedLPWrapper.hpp"
#define DEBUG 0
//#include "amorph.h"
//#include "util.h"
//#include "platform.h"
//#include <numpy/ndarrayobject.h>

using namespace boost::python;
using namespace std;

size_t** binom;
size_t numCombs;
size_t numPerms;



bool myComp (std::vector<size_t>* c1, std::vector<size_t>* c2) {
		/* cout << "\t comparing";
		for (std::vector<size_t>::iterator k = c1->begin(); k < (c1)->end(); ++k) cout << *k << " ";
		cout << " vs";
		for (std::vector<size_t>::iterator k = c2->begin(); k < c2->end(); ++k) cout << *k << " ";  
		cout << "res " << std::lexicographical_compare(c1->begin(), c1->end(), c2->begin(), c2->end()) << endl; */
		return std::lexicographical_compare(c1->begin(), c1->end(), c2->begin(), c2->end());
	}
bool myEqual (std::vector<size_t>* c1, std::vector<size_t>*  c2) {
				return std::equal(c1->begin(), c1->end(), c2->begin());
	}

template<class T> class sorter {
    const std::vector<T> &values;
	public:
    sorter(const std::vector<T> &v) : values(v) {} 
    bool operator()(int a, int b) { 
	/*
	    	for (std::vector< std::vector<size_t>* >::iterator j = values[a]->begin(); j < values[a]->end(); ++j) {
    			for (std::vector<size_t>::iterator k = (*j)->begin(); k < (*j)->end(); ++k) cout << *k << " ";
    			}
	cout << "vs ";
	    	for (std::vector< std::vector<size_t>* >::iterator j = values[b]->begin(); j < values[b]->end(); ++j) {
    			for (std::vector<size_t>::iterator k = (*j)->begin(); k < (*j)->end(); ++k) cout << *k << " ";
    			}
	cout << "res " <<  std::lexicographical_compare(values[a]->begin(), values[a]->end(), values[b]->begin(), values[b]->end(), myComp) << endl;
	*/
    	return std::lexicographical_compare(values[a]->begin(), values[a]->end(), values[b]->begin(), values[b]->end(), myComp);
    }
};


template<class T> std::vector<size_t> order(const std::vector<T> &values)
{
    std::vector<size_t> rv(values.size());
    size_t idx = 0;
    for (std::vector<size_t>::iterator i = rv.begin(); i != rv.end(); i++)
        *i = idx++;
    std::sort(rv.begin(), rv.end(), sorter<T>(values));
    return rv;
}


void recolor(std::vector< std::vector< std::vector <size_t>* >* >  colorSig, std::vector< size_t >* newWlColors ) {
		std::vector<size_t> permutation;
    	permutation = order(colorSig);
		// we start refinement 
		typedef std::vector<size_t>::const_iterator I;
    	if (DEBUG) for (I p = permutation.begin(); p != permutation.end(); ++p) std::cout << *p << " ";
    	if (DEBUG) std::cout << "\n";
    	
    	size_t c=0;
    	//newWlColors.clear(); newWlColors.resize(colorSig.size());
    	for (I p = permutation.begin(); p != permutation.end(); ++p) { 
    		if ( p!=permutation.begin() )  

    			if ( !std::equal(colorSig[*p]->begin(), colorSig[*p]->end(), colorSig[*(p-1)]->begin(), myEqual)  ) { 
    				++c;
/*    				cout << "new col " << c << endl; 
    				for (std::vector< std::vector<size_t>* >::iterator j = colorSig[*(p-1)]->begin(); j < colorSig[*(p-1)]->end(); ++j) {
    					cout << "(";
    					for (std::vector<size_t>::iterator k = (*j)->begin(); k < (*j)->end(); ++k) cout << *k << " ";
    					cout << ")";
    				}
    				cout << endl;
    				for (std::vector< std::vector<size_t>* >::iterator j = colorSig[*p]->begin(); j < colorSig[*p]->end(); ++j) {
    					cout << "(";
    					for (std::vector<size_t>::iterator k = (*j)->begin(); k < (*j)->end(); ++k) cout << *k << " ";
    					cout << ")";
    				}
    				cout << endl;*/
    			}
    		(*newWlColors)[*p] = c;  			
    	}

    	if (DEBUG) {
    		for (std::vector< std::vector<std::vector <size_t>* >* >::iterator i = colorSig.begin(); i < colorSig.end(); ++i) {
    			for (std::vector< std::vector<size_t>* >::iterator j = (*i)->begin(); j < (*i)->end(); ++j) {
    				cout << "(";
    				for (std::vector<size_t>::iterator k = (*j)->begin(); k < (*j)->end(); ++k) cout << *k << " ";
    				cout << ")";
    			}
    			cout << " --->>> " << (*newWlColors)[i - colorSig.begin()] << endl;
    		}
    	}
}






size_t makeInd(const size_t* tupind, size_t wldim, int nvertices) { 
	size_t tuple[wldim];
	size_t permind = 0;
	int gen_result = gen_perm_rep_lex_init(wldim);
	memcpy(tuple, tupind, wldim*sizeof(size_t));
	while(GEN_NEXT == gen_perm_rep_lex_next(tuple, wldim))
 	{
 		permind++;		
	}
	size_t result = 0;
	for (int i = 0; i < wldim ; i ++) {
		result += binom[tuple[i]][wldim - i - 1];
	}
	// cout << "sorted" << result << "permind "<< permind<<endl;

	return permind*numCombs + result;
}


void getInd(size_t* tuple, size_t wldim, int nvertices, size_t tNo) {
	
	size_t sortedtupind,permind = 0;

	permind = floor(tNo / numCombs);
	sortedtupind = tNo % numCombs;
	size_t choice = wldim - 1;
	size_t k = wldim - 1;
	size_t ind = 0;
/*	cout << "tNo " << tNo << "permind " << permind << "sorted " << sortedtupind << endl;

*/	
	// cout << "sorted " << sortedtupind << endl; 
	while (binom[choice][k] < sortedtupind) {
		// cout <<"A: " << binom[choice][k] << endl;
	    choice++;
		// cout << choice << " " << k << endl;
	  }
/*	 cout << "starting choice: " << choice << endl;*/
	do {
/*		cout << choice << " ";
*/		if (binom[choice][k] <= sortedtupind) {
		  sortedtupind -= binom[choice][k--];
/*		  cout << k << " " << endl;
*/		  tuple[k+1] = choice;
		}
	choice--;
	// cout << choice << " " << k << endl;
	} while (choice + 1 > 0);
	// cout << "permind " << permind;

	while (permind + 1 < numPerms) {
 		gen_perm_rep_lex_next(tuple, wldim);
 		permind++;		
	} 

}


/*

	for (int i = 0; i<wldim; ++i) {
		tuple[i] = tNo % nvertices;
		tNo = floor(tNo/nvertices);  
	} */


void computeIsotype(const size_t* tupind, size_t wldim, pyublas::numpy_vector<int> ncolors, pyublas::numpy_vector<int> ecolors, pyublas::numpy_vector<int> sprows, pyublas::numpy_vector<int> spcols, size_t* typeArray) {
	size_t n = ncolors.size();	
	//vertex indices
	// size_t tupind[wldim];
	int iter = 0;

	// getInd(tupind, wldim, n, tNo);
	if (DEBUG) cout << "tu";

	if (DEBUG) for (uint i=0; i<wldim; i++) cout << tupind[i]<<" ";

	//begin filling the isotype
	//node colors
	if (DEBUG) cout << "nc";
	for (uint i = 0; i<wldim; i++) {
		typeArray[i] = ncolors[tupind[i]];
		if (DEBUG) cout << typeArray[i]<<",";   
	}
	//identities
	iter = wldim;
	if (DEBUG) cout << "id";
	uint u = 0;
	for (uint i = 0; i<wldim - 1; i++) {
		for (uint j = i + 1; j<wldim; j++) {
			typeArray[iter + u] = 0;
			if (tupind[i] == tupind[j]) typeArray[iter + u] = 1;
			if (DEBUG) cout <<  typeArray[iter + u] << ",";
			u++;
		}
	}

	iter += u;
	if (DEBUG) cout << "ec";
	//edgecolors
	pyublas::numpy_vector<int>::iterator colsearch,clow,cup,found;
	std::pair<pyublas::numpy_vector<int>::iterator,pyublas::numpy_vector<int>::iterator> bounds;
	u = 0;
	for (uint i = 0; i<wldim; i++) {
		//sprows is sorted
		bounds=std::equal_range (sprows.begin(), sprows.end(), tupind[i]); 
		//cout << "\n row check: ";
		//for (pyublas::numpy_vector<int>::iterator tmp = bounds.first; tmp < bounds.second; tmp ++) cout << *tmp;
		//cout << "\n col check: ";
		clow = bounds.first - sprows.begin() + spcols.begin();
		cup = bounds.second - sprows.begin() + spcols.begin();
		//for (pyublas::numpy_vector<int>::iterator tmp = clow; tmp < cup; tmp ++) cout << *tmp;
		//cout << endl;
		for (uint j = 0; j<wldim; j++) {
			//cout << "s " << tupind[i] << ", " <<tupind[j]<<":";
			if (bounds.first == bounds.second) {
				typeArray[iter+u] = 0;
			} else {
				colsearch = std::lower_bound(clow,cup,tupind[j]);
				if (colsearch!=cup && !(tupind[j]<*colsearch)) {
					//cout << "found "<< *colsearch << " at " << colsearch - spcols.begin() << endl;
					found = colsearch - spcols.begin() + ecolors.begin();
					typeArray[iter+u] = *found;
				} else { 
					typeArray[iter+u] = 0;
				}
			}
			if (DEBUG) cout << typeArray[iter+u] << ",";
			u++;
		}
	}
	if (DEBUG) cout << ".\n"; 
	assert(iter + u -1 == wldim + ceil (wldim*(wldim-1)/2) + wldim*wldim - 1);
	if (DEBUG) for (uint i=0; i<iter + u; ++i) cout << typeArray[i]; 
	if (DEBUG) cout << endl;
}





pyublas::numpy_vector<int> kWeisfeilerLehman(pyublas::numpy_vector<int> ncolors, pyublas::numpy_vector<int> ecolors, pyublas::numpy_vector<int> sprows, pyublas::numpy_vector<int> spcols, int wldim)
	{
		//input dimensions
		size_t nedges = ecolors.size();
		printf("edges %d\n",nedges);
		assert(nedges == spcols.size());
		assert(nedges == sprows.size());
		size_t nvertices = ncolors.size();
		printf("vertices %d\n", nvertices);
		size_t const isosize = (size_t) (wldim + ceil (wldim*(wldim-1)/2) + wldim*wldim);
		boost::unordered_map<std::vector<size_t>,size_t,ihash,iequal_to> cmap;
		boost::unordered_set<size_t> cset;  
		std::vector<size_t>  rows;
		std::vector<size_t>  cols;
		std::vector<size_t>  data;

		//precompute some numbers
		numPerms = static_cast<size_t>(boost::math::factorial<float>(wldim)); // boost is just weird
		numCombs = static_cast<size_t>(boost::math::binomial_coefficient<double>(nvertices, wldim));
		// binom = (size_t *)malloc(sizeof(size_t) * wldim * nvertices);
		binom = (size_t **) malloc( ( nvertices +1 ) * sizeof(size_t *));
		for(int i = 0; i <= nvertices; i++)
			binom[i] = (size_t *) malloc((wldim+1) * sizeof(size_t));

		//we compute a lookup table

		for (int i = 0; i <= nvertices; i++) { //nodes start from 0, j's start from 1
			for (int j = 0; j < wldim; j++) {
				if (i < j + 1)	binom[i][j] = 0; //warning, there may be something fishy here
				else
					binom[i][j] = static_cast<size_t>(boost::math::binomial_coefficient<double>(i, j+1));  
			}
		}
		cout << "done table" << endl;

		//start generating 
		pyublas::numpy_vector<size_t> tupcolors( numPerms*numCombs );
		size_t isotype[isosize];
		std::vector< size_t > colorSig;
		std::vector< size_t > newWlColors; 
		std::vector< size_t > oldWlColors; 
		colorSig.clear(); colorSig.reserve( numPerms*numCombs);
		// fill in initial colors 
		int i;
		size_t maxcol = 0;
		for (i = 0; i <  numPerms*numCombs ; i++) { // numPerms*numCombs
			size_t tupind[wldim];
			size_t swap; 
			getInd(tupind, wldim, nvertices, i);

			//cout << i << " w " << pow(nvertices,wldim) << endl;
			if (DEBUG) cout << "r" << endl;
			computeIsotype(tupind, wldim, ncolors, ecolors, sprows, spcols, isotype);
			std::vector<size_t> tmp(isotype, isotype+isosize);
			
			if (cmap.find(tmp) == cmap.end()) {
				cmap[tmp] = ++maxcol;
				colorSig[i] = maxcol;
			} else colorSig[i] = cmap[tmp];

			//we generate neighbors 
/*			cout << endl << i << "-> [";
			for (int tmpind = 0; tmpind < wldim; tmpind++) cout << tupind[tmpind] << " ";
			cout << "] -> " << makeInd(tupind, wldim, nvertices);*/

			cset.clear(); cset.insert(tupind, tupind+wldim);
			for (size_t k = 0; k < nvertices; k++) {
				if (cset.find(k)!=cset.end()) continue;
				for (size_t j = 0; j < wldim; j++) {
/*
					cout << endl << i << "\t-> [";
					for (int asdf = 0; asdf < wldim; asdf++) cout << tupind[asdf] << " ";
					cout << "] -> ";*/

					swap = tupind[j];
					tupind[j] = k; 
					size_t tmpind = makeInd(tupind, wldim, nvertices);
					if (tmpind < i) {
/*						cout << "\n \t-> [";
						for (int asdf = 0; asdf < wldim; asdf++) cout << tupind[asdf] << " ";
						cout << "] -> " << tmpind;*/
						rows.push_back(i); cols.push_back(j); data.push_back(j);
										}
					tupind[j] = swap;
				} 

				}
			
			// BOOST_FOREACH(size_t i, cset) {
   //  			std::cout<<" "<< i;
			// }
			// cout << endl;
			// for (int j = 0; j<wldim)

				

			// colorSig.push_back(tmp);
			//for (std::vector< size_t >::iterator j = tmp->begin(); j < tmp->end(); j++) cout << *j << " ";
			//cout << endl;
		}

		//newWlColors.resize(colorSig.size());
		kwlEquitablePartitionSaucy(data, rows, cols, colorSig, 0, 1);
		return ncolors;
	/*	// recolor(colorSig, &newWlColors);

		// flush the colorSig vector
		size_t tupnodes[wldim], tmptup[wldim];
		uint iter = 0;
		while (true) {
			cout << "iteration: " << ++iter << endl;
			for (std::vector< std::vector<std::vector <size_t>* >* >::iterator i = colorSig.begin(); i < colorSig.end(); ++i) {
    			for (std::vector< std::vector<size_t>* >::iterator j = (*i)->begin(); j < (*i)->end(); ++j) {
    				(*j) -> clear();
    				delete *j;
    			}
    			(*i)->clear();
    		}	 
			oldWlColors.clear();
			oldWlColors.reserve(newWlColors.size());
		    copy(newWlColors.begin(),newWlColors.end(),back_inserter(oldWlColors));
			for (uint i = 0; i < pow(nvertices,wldim); ++i) {
				getInd(tupnodes, wldim, nvertices, i);
				getInd(tmptup, wldim, nvertices, i);
				for (uint j = 0; j<nvertices; ++j) {
					std::vector<size_t>* tmpcoltup = new std::vector<size_t>;
					for (uint k = 0; k < wldim; ++k) {
						tmptup[k] = j;
						tmpcoltup->push_back( oldWlColors[ makeInd(tmptup, wldim, nvertices) ] );  
						tmptup[k] = tupnodes[k];
					}
					colorSig[i]->push_back(tmpcoltup);
				}
				std::sort(colorSig[i]->begin(), colorSig[i]->end(), myComp);
				colorSig[i]->push_back(new std::vector<size_t>( 1,oldWlColors[i] ) );

			}
			recolor(colorSig, &newWlColors);
			if (std::equal(oldWlColors.begin(), oldWlColors.end(), newWlColors.begin())) { 
				cout << "converged" << endl;
				break;
			}
		}
*/
		/*cout << "********RESULT*********" << endl;
		for (uint i = 0; i < pow(nvertices,wldim); ++i) {
			getInd(tupnodes, wldim, nvertices, i);
			cout << "t:";
			for (uint j = 0; j < wldim; ++j) {
				cout << " " << tupnodes[j]; 
			}
			cout << ":" << newWlColors[i] << endl;
		}*/
/*		std::copy(newWlColors.begin(),newWlColors.end(),tupcolors.begin());

		return tupcolors;
*/	}


int gen_perm_rep_lex_init(const size_t n)
{
//test for special cases
if(n == 0)
 return(GEN_EMPTY);

//initialize: vector must be initialized by the calling process

return(GEN_NEXT);
}

int gen_perm_rep_lex_next(size_t *vector, const size_t n)
{
int j = n - 2; //index
int i = n - 1; //help index
int temp;      //auxiliary element

//find rightmost element to increase
while(j >= 0)
 {
 if(vector[j] < vector[j + 1])
  break;

 j--;
 }

//terminate if all elements are in decreasing order
if(j < 0)
 return(GEN_TERM);

//find i
while(vector[i] <= vector[j])
 i--;

//increase (swap)
temp = vector[j];
vector[j] = vector[i];
vector[i] = temp;

//reverse right-hand elements
for(j += 1, i = n - 1; j < i;  j++, i--)
 {
 temp = vector[j];
 vector[j] = vector[i];
 vector[i] = temp;
 }

return(GEN_NEXT);
}


int gen_comb_norep_lex_init(size_t *vector, const size_t n, const size_t k)
{
int j; //index

//test for special cases
if(k > n)
 return(GEN_ERROR);

if(k == 0)
 return(GEN_EMPTY);

//initialize: vector[0, ..., k - 1] are 0, ..., k - 1
for(j = 0; j < k; j++)
 vector[j] = j;

return(GEN_NEXT);
}

int gen_comb_norep_lex_next(size_t *vector, const size_t n, const size_t k)
{
int j; //index

//easy case, increase rightmost element
if(vector[k - 1] < n - 1)
 {
 vector[k - 1]++;
 return(GEN_NEXT);
 }

//find rightmost element to increase
for(j = k - 2; j >= 0; j--)
 if(vector[j] < n - k + j)
  break;

//terminate if vector[0] == n - k
if(j < 0)
 return(GEN_TERM);

//increase
vector[j]++;

//set right-hand elements
while(j < k - 1)
 {
 vector[j + 1] = vector[j] + 1;
 j++;
 }

return(GEN_NEXT);
}


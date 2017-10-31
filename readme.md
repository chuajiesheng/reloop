# Reloop

Note: This repo was originally hosted at [Bitbucket/Reloop](https://bitbucket.org/reloopdev/reloop).
Please check out [Bitbucket/Reloop Developers](https://bitbucket.org/reloopdev/profile/members) for the list of original authors.

## 1. Prequisites as in requirements.txt

* GNU GLPK Linear/Mixed Integer Solver (`brew install glpk` for MacOS users) 
* Reloop requires Python 2.7+
* Scipy v0.15+
* Numpy v1.9.1+
* Cython v0.21.1+
* Cvxopt v1.1.7+
* [Picos v1.0.1+](http://picos.zib.de/dist/PICOS-1.0.1.tar.gz)
* infix v1.0.0+
* Ordered-Set v1.3.1+
* pyDatalog v0.14.6
* sympy v0.7.6+
* psycopg2 v.2.6.1+
* problog v.2.1.0.5+

If pip is available all prequisites can be installed at once by running

`$ pip install -r requirements.txt --upgrade`

### 1.1 Optional Dependencies
These optional dependencies enable additional knowledge bases for usage. While Problog and SWI-Prolog 
both interface Prolog, psycopg2 interface a postgres database.

* Problog v2.1+
* Psycopg2 v2.6.1+
* SWI-Prolog


## 2. Installation


Once all the prequisites have been installed simply run

`python setup.py build_ext --inplace`

followed by either 

`python setup.py install`

or

`pip install .`

from the root directory of Reloop.

## 3. Examples

For examples on how to use Reloop please see our [Documentation](http://www-ai.cs.uni-dortmund.de/weblab/static/RLP/html/tutorial.html)


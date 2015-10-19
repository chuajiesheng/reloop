.. highlight:: python

Quick Reference
================

Reloop
-----------

This Quick Reference will provide you with an overview about the available language features of Relational Linear Programming. For a more in depth code documentation, please visit our :ref:`reference page<reference>`.

Reloop comes with a powerful modelling language for relational linear programs: RLP. 

RLP aims to bridge the gap between powerful relational reasoning tools and efficient numerical optimization algorithms in a hassle-free way.
When defining a model with RLP, you are able to use logically parameterized definitions for the index sets within arithmetic expressions. 
A 'Logical Knowledge Base' contains all your data and will be queried in order to ground the RLP into a plain LP, that can then be solved by an arbitrary numerical solver. 


.. image:: images/rlp_diagram.png
    :align: center
    :alt: RLP Diagram

RLP and Sympy
--------------
RLP is built on top of Sympy, a Python library for symbolic mathematics. That means you are able to use most of SymPy's features, such as simplification, expansion and functions.


Predicates
...........
Predicates represent relational data inside our model definitions. If your data contains e.g. a relation ``R(String, String, Integer)``, it is possible to define a predicate inside RLP that maps to this specific relation. RLP distinguishes between two types of predicates:

1. **BooleanPredicates** 
   can be used to determine if a tuple is part of the relation. It will return True or False
2. **NumericPredicates**
   can be used to get numerical data from a LogKb for using it in mathematical expressions. It can also be interpreted as a function.


SubSymbols
............

SubSymbols in RLP are placeholders in expressions. They behave similarly to `Sympys Symbols <http://docs.sympy.org/latest/modules/core.html#id17>`_, since SubSymbol subclasses Symbol.
They can only be used inside a `Forall` or `RlpSum` statement, because the Grounder will try to substitute those SubSymbols with answers from the LogKB. 

Queries
........
Queries are logical expressions and can consist of BooleanPredicates and `Boolean Functions <http://docs.sympy.org/0.7.6/modules/logic.html#boolean-functions>`_. They can be built with the standard python operators ``&`` (And), ``|`` (Or) and ``~`` (Not).
Queries are used for 

1. **ForAll** 
   statements: These allow batch constraint generation, based on answers from the LogKB. 
2. **RlpSum** 's
   : A mathematical sum over an answer set from the LogKB.


Constraints
............

While there is no inherent datatype for constraints, we allow instances of `ForAll` that contains a sympy `Relation <http://docs.sympy.org/latest/modules/core.html#module-sympy.core.relational>`_ or directly such relations, which can be added to the model with the ``+=`` operator.

Logical Knowledge Base & Grounding
----------------------------------

When solving a RLP model, Reloop grounds the model definitions into a LP. It compiles the logical queries and queries the Logical Knowledge Base until everything is grounded. That includes nested queries, e.g. a RlpSum inside a ForAll constraint. Currently we provide interfaces to four differenct LogKBs:

1. pyDatalog
2. PostgreSQL
3. SWI Prolog
4. ProbLog


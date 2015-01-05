Glpk2Py
=========================================================
.. cpp:member:: enum glpk2py::filetype
	
    =====  =====  ===========
    Name   Value  Description
    =====  =====  ===========
    MPS      0    Given file is in the MPS format 
    LP       1    Given file is in the LP format  
    =====  =====  ===========

.. cpp:function:: void glpk2py::openLP(const std::string &fname, int format) 

   	:param fname: The name of the file to be opened
	:param format: The filetype of given file either MPS or LP are valid (see enum filetype)
	Opens the LP by creating a glpk problem object and assigning the given file to it \n
	Furthermore extracts the number of columns and rows of the opened LP and assigns the values to global variables

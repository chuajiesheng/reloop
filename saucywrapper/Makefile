CC=g++
CFLAGS=-ansi -fpermissive -Wall -O0 -ggdb -fPIC
PYUPATH=$(shell ./findpyu.py)
PYTHON = /usr/include/python2.7

BOOST_INC = /usr/include
BOOST_LIB = /usr/lib

LDLIBS= -lboost_python -lpython2.7 -lz -lglpk
LPATH = -L$(PYTHON)/config -L$(BOOST_LIB)

TARGET = LiftedLPWrapper

default: LiftedLPWrapper.so glpk2py.so

LiftedLPWrapper.so: main.o saucy.o saucyio.o util.o LiftedLPWrapper.o WL.o 
	g++ -shared -Wl,--export-dynamic \
	main.o saucy.o saucyio.o util.o LiftedLPWrapper.o WL.o $(LPATH) $(LDLIBS) \
	-o LiftedLPWrapper.so

	
saucy : main.o saucy.o saucyio.o util.o

shatter : shatter.o saucy.o saucyio.o util.o

main.o shatter.o saucy.o saucyio.o : saucy.h
main.o shatter.o saucyio.o : amorph.h
main.o shatter.o util.o : util.h
main.o shatter.o saucyio.o : platform.h
LiftedLPWrapper.o: 
	g++ -I. -I$(PYTHON) -I$(BOOST_INC) -I$(PYUPATH) -fPIC -c LiftedLPWrapper.cpp 

WL.o:
	g++ -I. -I$(PYTHON) -I$(BOOST_INC) -I$(PYUPATH) -fPIC -c WL.cpp

glpk2py.o: glpk2py.cpp
	g++ -I. -I$(PYTHON) -I$(BOOST_INC) -I$(PYUPATH) $(CFLAGS) -c glpk2py.cpp

glpk2py.so:  glpk2py.o  
	g++ -shared -Wl,--export-dynamic \
	glpk2py.o $(LPATH) $(LDLIBS) \
	-o glpk2py.so
clean: 
	rm -rf saucy shatter *.o LiftedLPWrapper.*o

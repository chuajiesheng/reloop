#!/usr/bin/env python
from imp import find_module
file, pathname, descr = find_module("pyublas")
from os.path import join
print join(pathname, "include")

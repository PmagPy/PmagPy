#!/usr/bin/env python
from __future__ import print_function
from builtins import range
mylist = [42, 'spam', 'ocelot']
Indices = list(range(0, len(mylist), 1))
for i in Indices:
   print(mylist[i])
print('All done')

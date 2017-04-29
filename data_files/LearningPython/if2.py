#!/usr/bin/env python
from __future__ import print_function
mylist=['jane','doug','denise']
if 'susie' in mylist:
    pass # don't do anything
if 'susie' not in mylist:
   print('call susie and apologize!')
   mylist.append('susie')
elif 'george' in mylist: # if first statement is false, try this one
    print('susie and george both in list') 
else: # if both statements are false, do this:
   print("susie in list but george isn't")

#!/usr/bin/env python
def DoubleOrNothing(variable):
    if variable >= 10: # tests variable against 10
        return 2.0*variable # returns double
    else:  
       return 0.

def main():
    var=raw_input('Enter number:  ')
    result=DoubleOrNothing(float(var))
    if result==0.:
        print 'You get nothing!'
    else:
        print 'You win!  your answer is: ',result
main()





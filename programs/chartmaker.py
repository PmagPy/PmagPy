#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import str
from builtins import range
import sys

def main():
    """
    Welcome to the thellier-thellier experiment automatic chart maker.   
    Please select desired step interval and upper bound for which it is valid.
    e.g.,   
    50 
    500
    10 
    600
    
    a blank entry signals the end of data entry.
    which would generate steps with 50 degree intervals up to 500, followed by 10 degree intervals up to 600.   
    
    chart is stored in:  chart.txt
    """
    print(main.__doc__)
    if '-h' in sys.argv:sys.exit() 
    f=open('chart.txt','w')
    cont,Int,Top,Tzero=1,[],[],[]
    while cont==1:
        try: 
            Int.append(int(input(" Enter desired treatment step interval: <return> to quit ")))
            Top.append(int(input(" Enter upper bound for this interval: ")))
        except:
            cont=0
    low,k,iz=100,0,0
    vline='\t%s\n'%('   |      |        |         |          |       |    |      |')
    hline='______________________________________________________________________________\n'
    f.write('file:_________________    field:___________uT\n\n\n')
    f.write('%s\n'%('               date | run# | zone I | zone II | zone III | start | sp | cool|'))
    f.write(hline)
    f.write('\t%s'%('   0.0'))
    f.write(vline)
    f.write(hline)
    for k in range(len(Top)):
        for t in range(low,Top[k]+Int[k],Int[k]):
            if iz==0:
                Tzero.append(t) # zero field first step
                f.write('%s \t %s'%('Z',str(t)+'.'+str(iz)))
                f.write(vline)
                f.write(hline)
                if len(Tzero)>1:
                   f.write('%s \t %s'%('P',str(Tzero[-2])+'.'+str(2)))
                   f.write(vline)
                   f.write(hline)
                iz=1
                f.write('%s \t %s'%('I',str(t)+'.'+str(iz))) # infield after zero field first
                f.write(vline)
                f.write(hline)

#                f.write('%s \t %s'%('T',str(t)+'.'+str(3))) # print second zero field (tail check)
#                f.write(vline)
#                f.write(hline)

            elif iz==1:
                f.write('%s \t %s'%('I',str(t)+'.'+str(iz))) # infield first step
                f.write(vline)
                f.write(hline)
                iz=0
                f.write('%s \t %s'%('Z',str(t)+'.'+str(iz)))# zero field step (after infield)
                f.write(vline)
                f.write(hline)
        try:
            low=Top[k]+Int[k+1] # increment to next temp step
        except:
            f.close()
    print("output stored in: chart.txt")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
import sys,pmagplotlib
def main():
    """
    NAME
       eqarea.py

    DESCRIPTION
       makes equal area projections from declination/inclination data

    INPUT FORMAT
       takes dec/inc as first two columns in space delimited file
   
    SYNTAX
       eqarea.py [-f FILE]

    OPTIONS
        -i for interactive filename entry
        -f FILE, specify file on command line
        -p save figure and quit
        -fmt [svg,jpg,png,pdf] set figure format [default is svg]
        -s  SIZE specify symbol size - default is 20
        -Lsym  SHAPE  COLOR specify shape and color for lower hemisphere
        -Usym  SHAPE  COLOR specify shape and color for upper hemisphere
          shapes:  's': square,'o': circle,'^,>,v,<': [up,right,down,left] triangle, 'd': diamond, 
                   'p': pentagram, 'h': hexagon, '8': octagon, '+': plus, 'x': cross
          colors:  [b]lue,[g]reen,[r]ed,[c]yan,[m]agenta,[y]ellow,blac[k],[w]hite

    """
    title=""
    files,fmt={},'svg'
    sym={'lower':['o','r'],'upper':['o','w']}
    plot=0
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-p' in sys.argv: plot=1
    if '-fmt'  in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1] 
    if '-s'  in sys.argv:
        ind=sys.argv.index('-s')
        sym['size']=int(sys.argv[ind+1])
    else:
        sym['size']=20
    if '-Lsym'  in sys.argv:
        ind=sys.argv.index('-Lsym')
        sym['lower'][0]=sys.argv[ind+1] 
        sym['lower'][1]=sys.argv[ind+2] 
    if '-Usym'  in sys.argv:
        ind=sys.argv.index('-Usym')
        sym['upper'][0]=sys.argv[ind+1] 
        sym['upper'][1]=sys.argv[ind+2] 
    if '-i' in sys.argv: # ask for filename
        file=raw_input("Enter file name with dec, inc data: ")
        f=open(file,'rU')
        data=f.readlines()
    elif '-f' in sys.argv: # ask for filename
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines()
    DI= [] # set up list for dec inc data
    for line in data:   # read in the data from standard input
        if '\t' in line:
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        if len(rec)>1:
            DI.append([float(rec[0]),float(rec[1])]) # append first two columns as DI pair
#
    EQ={'eq':1}
    pmagplotlib.plot_init(EQ['eq'],5,5)
    pmagplotlib.plotEQsym(EQ['eq'],DI,'Equal Area Plot',sym) # make plot
    if plot==0:pmagplotlib.drawFIGS(EQ) # make it visible
    for key in EQ.keys():
        files[key]=key+'.'+fmt 
    if pmagplotlib.isServer:
        black     = '#000000'
        purple    = '#800080'
        titles={}
        titles['eq']='Equal Area Plot'
        EQ = pmagplotlib.addBorders(EQ,titles,black,purple)
        pmagplotlib.saveP(EQ,files)
    elif plot==1:
        files['eq']=file+'.'+fmt 
        pmagplotlib.saveP(EQ,files)
    else:
        ans=raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
        if ans=="a": pmagplotlib.saveP(EQ,files) 
main()


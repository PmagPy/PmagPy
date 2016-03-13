#!/usr/bin/env python
import sys


import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME 
        plot_magic_keys.py

    DESCRIPTION
        picks out keys and makes and xy plot

    SYNTAX
        plot_magic_keys.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic format file 
        -xkey KEY: specify key for X 
        -ykey KEY: specify key  for Y
        -b xmin xmax ymin ymax, sets bounds

    """
    dir_path="./"
    if '-WD' in sys.argv: 
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        magic_file=dir_path+'/'+sys.argv[ind+1]
    else:
        print main.__doc__
        sys.exit()
    if '-xkey' in sys.argv:
        ind=sys.argv.index('-xkey')
        xkey=sys.argv[ind+1]
        if '-ykey' in sys.argv:
            ind=sys.argv.index('-ykey')
            ykey=sys.argv[ind+1]
    else:
        print main.__doc__
        sys.exit()
    if '-b' in sys.argv:
        ind=sys.argv.index('-b')
        xmin=float(sys.argv[ind+1])
        xmax=float(sys.argv[ind+2])
        ymin=float(sys.argv[ind+3])
        ymax=float(sys.argv[ind+4])
    #
    #
    # get data read in
    X,Y=[],[]
    Data,file_type=pmag.magic_read(magic_file) 
    if len(Data)>0:
        for rec in Data: 
            if xkey in rec.keys() and rec[xkey]!="" and ykey in rec.keys() and rec[ykey]!="":
                try:
                    X.append(float(rec[xkey]))
                    Y.append(float(rec[ykey]))
                except:
                    pass
        FIG={'fig':1}
        pmagplotlib.plot_init(FIG['fig'],5,5)
        if '-b' in sys.argv:
            pmagplotlib.plotXY(FIG['fig'],X,Y,sym='ro',xlab=xkey,ylab=ykey,xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax )
        else:
            pmagplotlib.plotXY(FIG['fig'],X,Y,sym='ro',xlab=xkey,ylab=ykey)
        pmagplotlib.drawFIGS(FIG)
        ans=raw_input(" S[a]ve to save plot, [q]uit, Return to continue:  ")
        if ans=="q": sys.exit()
        if ans=="a":
            files = {}
            for key in FIG.keys():
                files[key]=str(key) + ".svg"
                pmagplotlib.saveP(FIG,files)
        sys.exit()
    else:
        print 'no data to plot'

if __name__ == "__main__":
    main()



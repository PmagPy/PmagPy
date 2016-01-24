#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def spitout(line):
    rec=line.split()
    sundata={}
    sundata["delta_u"]=rec[0] # assign first column to delta_u key in sundec dictionary
    sundata["lat"]=float(rec[1])
    sundata["lon"]=float(rec[2])
    year=rec[3]
    month=rec[4]
    day=rec[5]
    hours=rec[6]
    min=rec[7]
    sundata["date"]=year+":"+month+":"+day+":"+hours+":"+min # put together the date the way dosundec wants it.
    sundata["shadow_angle"]=rec[8]
    dec=pmag.dosundec(sundata) # print out the output from sundec (the magnetic declination)
    print '%7.1f'%(dec) # print out the output from sundec (the magnetic declination)
    return dec
def main():
    """
    NAME
       sundec.py

    DESCRIPTION
       calculates calculates declination from sun   compass measurements

    INPUT FORMAT
       GMT_offset, lat,long,year,month,day,hours,minutes,shadow_angle
       where GMT_offset is the hours to subtract from local time for GMT.

    SYNTAX
       sundec.py [-i][-f FILE] [< filename ]

    OPTIONS
        -i for interactive data entry
        -f FILE to set file name on command line 
         otherwise put data in input format in space delimited file
    OUTPUT:
        declination
 """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines() # read in data from standard input
        for line in data: # step through line by line
            dec=spitout(line)
        sys.exit()
    if '-i' in sys.argv:
        while 1: # repeat this block until program killed
            sundata={}  # dictionary with sundata in it
            print ("Time difference between Greenwich Mean Time (hrs to SUBTRACT from local time to get GMT): ")
            try:
                sundata["delta_u"]=raw_input("<cntl-D> to quit ")
            except:
                print "\n Good-bye\n"
                sys.exit()
            date=""
            date=date+raw_input("Year:  <cntl-D to quit> ")
            date=date+":"+raw_input("Month:  ")
            date=date+":"+raw_input("Day:  ")
            date=date+":"+raw_input("hour:  ")
            date=date+":"+raw_input("minute:  ")
            sundata["date"]=date
            sundata["lat"]=raw_input("Latitude of sampling site (negative in southern hemisphere): ")
            sundata["lon"]=raw_input("Longitude of sampling site (negative for western hemisphere): ")
            sundata["shadow_angle"]=raw_input("Shadow angle: ")
            print '%7.1f'%(pmag.dosundec(sundata)) # call sundec function from pmag module and print
    else:
        data=sys.stdin.readlines() # read in data from standard input
    for line in data: # step through line by line
        dec=spitout(line)

if __name__ == "__main__":
    main()

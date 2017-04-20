#!/usr/bin/env python
files=['aus','eur','mad','nwaf','col','grn','nam','par','eant','ind','neaf','sac','ib']
out=open('../frp.py','w')
out.write("def get_pole(continent,age):\n")
for file in files:
    outstring="    if continent=="+repr(file)+":\n"
    out.write(outstring)
    if file!='ib':
        f=open(file+'_saf.frp','r')
    else:
        f=open('ib_eur.frp','r')
    frp='['
    for line in f.readlines():
        rec=line.split()
        frp=frp+"["+rec[0]+','+rec[1]+','+rec[2]+','+rec[3]+'],'
    outstring="        cont= "+frp[:-1]+']\n'
    out.write(outstring)
    outstring="        for rec in cont:\n "
    out.write(outstring)
    outstring="            if age==int(rec[0]): return [rec[1],rec[2],rec[3]] \n"
    out.write(outstring)
outstring="    if continent=='saf':\n"
out.write(outstring)
f=open('saf.frp','r')
frp='['
for line in f.readlines():
    rec=line.split()
    frp=frp+"["+rec[0]+','+rec[1]+','+rec[2]+','+rec[3]+'],'
outstring="        cont= "+frp[:-1]+']\n'
out.write(outstring)
outstring="        for rec in cont:\n "
out.write(outstring)
outstring="            if age==int(rec[0]): return [rec[1],rec[2],rec[3]] \n"
out.write(outstring)
outstring="    return 'NONE'\n"
out.write(outstring)

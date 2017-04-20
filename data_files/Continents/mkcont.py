#!/usr/bin/env python
files=['af.asc','aus.asc','balt.asc','congo.asc','eur.asc','ind.asc','sam.asc','ant.asc','grn.asc','lau.asc','nam.asc','waf.asc','plates.asc','gond.asc','kala.asc']
out=open('../continents.py','w')
out.write("def get_continent(continent):\n")
for file in files:
    outstring="    if continent=="+repr(file)+":\n"
    out.write(outstring)
    f=open(file,'r')
    cont="["
    for line in f.readlines():
        rec=line.split()
        cont=cont+"["+rec[0]+','+rec[1]+'],'
    outstring="        return "+cont[:-1]+']\n'
    out.write(outstring)

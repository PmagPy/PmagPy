#!/usr/bin/env python
#
import pmag,exceptions,sys
def getfield(line):
    i,field=0,""
    for c in line:
        i+=1
        if c=="{":
            try:
               while line[i]!='}':
                   field+=line[i]
                   i+=1
               break
            except:
                print line
                print i,len(line)
                 
    return field 
def main():
    """
    NAME
        endnote_magic.py

    DESCRIPTION
        Converts an EndNoteExport.txt file (bibtex format) to er_citations.txt format

    SYNTAX
        endnote_magic.py [command line options]

    OPTIONS
        -h prints help messge and quits
        -i allows interactive filename entry
        -f EndNoteFile, specify endnote file on the command line
        -F ErCitation, specify output er_citations.txt file
 
    INPUT
        file must be in the LaTeX .bib format

    DEFAULTS
        ErCitation file:  er_citation.txt
        EndNoteFile:  EndNoteExport.txt
    """
    EndFile,outfile='EndNoteExport.txt','er_citations.txt'
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        EndFile=sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=sys.argv[ind+1]
    if '-i' in sys.argv:
        EndFile=raw_input("EndNoteExport file: [EndNoteExport.txt] ")
        if EndFile=="":EndFile="EndNoteExport.txt"
        outfile=raw_input("output file?  [er_citations.txt] ")
        if outfile=="":outfile="er_citations.txt"
    efile=open(EndFile,'rU')
    #
    # read in references
    #
    Refs,Ref=[],{}
    data=efile.readlines()
    data.append('\n')
    keys=pmag.getkeys('ER_citations')
    for key in keys: Ref[key]="" 
    Ref['citation_label']=""
    for line in data:
        print line
        if line[0]=='\n':
            if Ref['citation_label']!= "": # end of the road for this one - reset
                citation=Ref['er_citation_name']+' '+Ref['year']
                Ref['er_citation_name']=citation
                Refs.append(Ref)
                Ref={}
                for key in keys:Ref[key]="" 
                Ref['citation_label']=""
        if line[0]=="@":
            if "@article{" in line:Ref["citation_type"]="Journal"
            if "@incollection{" in line:Ref["citation_type"]="Edited Book"
            if "@book{" in line:Ref["citation_type"]="Book"
            if "@misc{" in line:Ref["citation_type"]="Ph.D. Thesis"
            if "@phdthesis{" in line:Ref["citation_type"]="Miscellaneous"
            if "citation_type" not in Ref.keys() or Ref["citation_type"]=="":
                print "problem in citation_type ",line
        if "Author =" in line:
            ref= getfield(line)
            authorlist=ref.split(' and ')
            long=""
            for i in range(len(authorlist)):
                long+=authorlist[i]+', '
            long=long[:-2] # take off the terminal comma
            if len(authorlist)>1: # more than one author
                if len(authorlist)==2: # only two
                    long=""
                    long+=authorlist[0]+' and '+authorlist[1]
                    short=authorlist[0].split(',')[0] + " & " + authorlist[1].split(',')[0]
                else:
                    short=authorlist[0].split(',')[0] + ' et al.'
            else: #only one
                short = authorlist[0].split(',')[0]
            Ref["er_citation_name"]=short
            Ref["long_authors"]=long
        if "Title =" in line: Ref["title"]=getfield(line) 
        if "Journal =" in line:
            ref=getfield(line)
            if "Earth Planet. Sci. Lett." in ref:ref="Earth and Planetary Science Letters"
            if "Geochem., Geophys., Geosyst" in ref:ref="Geochemistry, Geophysics, Geosystems"
            if "Geophys. J. Int." in ref:ref="Geophysical Journal International"
            if "J. Geophys." in ref:ref="Journal of Geophysics"
            if "Jour. Geophys. Res." in ref:ref="Journal of Geophysical Research"
            if "Solid Earth" in ref: ref="Journal of Geophysical Research"
            if "Phys. Earth Planet." in ref:ref="Physics of the Earth and Planetary Interiors"
            Ref["journal"]=ref
        if "Volume =" in line:Ref["volume"]=getfield(line)
        if "Pages =" in line:
            ref=getfield(line)
            if "doi" in ref:
                Ref["doi"]=ref
            else:
                Ref["pages"]=ref
        if "Year =" in line:Ref["year"]=getfield(line)
        if "Publisher =" in line:Ref["publisher"]=getfield(line)
        if "Publisher =" in line:Ref["publisher"]=getfield(line)
        if "@" not in line and line[0]!=" " and Ref["citation_label"]=="": # don't overwrite this with junk
            Ref["citation_label"]=line[:-2]
    # export to er_citations file
    pmag.magic_write(outfile,Refs,'er_citations')
    print 'Citations saved in ',outfile 
main()

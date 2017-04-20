def readEQs(infile):
    input=open(infile,'r').readlines()
    EQs=[] # list to put EQ dictionaries in
    linenum=0
    while linenum <len(input):
        if 'event id' in input[linenum]: # new event
            EQ={} # define a dictionary
            linenum+=2 # increment past time-stamp
            while 'param' in input[linenum]:
                record=input[linenum].split('=')
                datakey=record[1].split()[0].strip('"')
                EQ[datakey]=record[2].strip('\n').strip('/>').strip('"')
                linenum+=1 # keep going until </event>
            if '</event>' in input[linenum]: # done with event
                EQs.append(EQ)
        linenum+=1 # look for next event id
    return EQs

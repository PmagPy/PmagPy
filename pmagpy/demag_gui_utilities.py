from re import findall,split

def specimens_comparator(s1,s2):
    sam_sp1 = split(r'[-,.]+',s1)
    sam_sp2 = split(r'[-,.]+',s2)
    for e1,e2 in zip(sam_sp1,sam_sp2):
        for c1,c2 in zip(e1,e2): #sort by letters
            if c1 != c2 and c1.isalpha() and c2.isalpha():
                return ord(c1)-ord(c2)
        l1 = map(int, findall('\d+', e1)) #retrieves numbers from names
        l2 = map(int, findall('\d+', e2))
        for i1,i2 in zip(l1,l2): #sort by numbers
            if i1-i2 != 0:
                return i1-i2
    return 0

def read_LSQ(filepath):
    fin = open(filepath, 'r')
    interps = fin.readlines()
    interps_out = []
    for i,interp in enumerate(interps):
        interps_out.append({})
        enteries = interp.split()
        interps_out[i]['er_specimen_name'] = enteries[0]
        if enteries[1] == 'L':
            interps_out[i]['magic_method_codes'] = 'DE-BFL:DA-DIR-GEO'
        j = 2
        if enteries[j] == "MAG": j+=1
        interps_out[i]['specimen_dec'] = enteries[j]
        interps_out[i]['specimen_inc'] = enteries[j+1]
        j+=4
        bounds = enteries[j].split('-')
        interps_out[i]['measurement_min_index'] = ord(bounds[0])-ord('A')
        interps_out[i]['measurement_max_index'] = ord(bounds[1])-ord('A')
        interps_out[i]['specimen_n'] = enteries[j+1]
        interps_out[i]['specimen_mad'] = enteries[j+2]
    fin.close()
    return interps_out

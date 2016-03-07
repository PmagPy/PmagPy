from re import findall

def specimens_comparator(s1,s2):
    sam_sp1 = s1.split(". -")
    sam_sp2 = s2.split(". -")
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



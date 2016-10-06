import os
from wx import FileDialog
from re import findall,split
from numpy import array,arange,pi,cos,sin
from pmag import dimap,cart2dir,dir2cart
import programs.cit_magic3 as cit_magic
from ipmag import combine_magic
from time import time

def specimens_comparator(s1,s2):
    if type(s1) != str and type(s2) != str: return 0
    elif type(s1) != str: return -1
    elif type(s2) != str: return 1
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

def get_all_inp_files(WD=None):
    if not os.path.isdir(WD): print("directory %s does not exist, aborting"%WD)
    try:
        all_inp_files = []
        for root, dirs, files in os.walk(WD):
            for d in dirs:
                all_inp_files += get_all_inp_files(d)
            for f in files:
                if f.endswith(".inp"):
                     all_inp_files.append(os.path.join(root, f))
        return all_inp_files
    except RuntimeError:
        print("Recursion depth exceded, please use different working directory there are too many sub-directeries to walk")

def read_inp(WD,inp_file_name,magic_files,data_model=2.5):
    inp_file = open(inp_file_name, "r")
    new_inp_file = ""

    if type(magic_files) != dict: magic_files = {}
    if 'measurements' not in magic_files.keys(): magic_files['measurements']=[]
    if 'specimens' not in magic_files.keys(): magic_files['specimens']=[]
    if 'samples' not in magic_files.keys(): magic_files['samples']=[]
    if 'sites' not in magic_files.keys(): magic_files['sites']=[]
    if 'locations' not in magic_files.keys(): magic_files['locations']=[]

    lines = inp_file.read().splitlines()
    if len(lines) < 3: print(".inp file improperly formated"); return
    new_inp_file = lines[0] + "\r\n" + lines[1] + "\r\n"
    [lines.remove('') for i in range(lines.count(''))]
    format = lines[0].strip()
    header = lines[1].split('\t')
    update_files = lines[2:]
    update_data = False
    for i,update_file in enumerate(update_files):
        update_lines = update_file.split('\t')
        if not os.path.isfile(update_lines[0]):
            print("%s not found searching for location of file"%(update_lines[0]))
            sam_file_name = os.path.split(update_lines[0])[-1]
            new_file_path = find_file(sam_file_name, WD)
            if new_file_path == None or not os.path.isfile(new_file_path):
                print("%s does not exist in any subdirectory of %s and will be skipped"%(update_lines[0], WD))
                new_inp_file += update_file+"\r\n"
                continue
            else:
                print("new location for file found at %s"%(new_file_path))
                update_lines[0] = new_file_path
        d = os.path.dirname(update_lines[0])
        name = os.path.basename(os.path.splitext(update_lines[0])[0])
        erspecf = name + "_er_specimens.txt"
        ersampf = name + "_er_samples.txt"
        ersitef = name + "_er_sites.txt"
        erlocf = name + "_locations.txt"
        f = name + ".magic"
        if os.path.join(d,f) in magic_files:
            new_inp_file += update_file+"\r\n"
            continue
        if float(update_lines[-1]) >= os.path.getmtime(update_lines[0]):
            no_changes = True
            #check specimen files for changes
            sam_file = open(update_lines[0])
            sam_file_lines = sam_file.read().splitlines()
            spec_file_paths = map(lambda x: os.path.join(d,x.strip('\r \n')), sam_file_lines[2:])
            for spec_file_path in spec_file_paths:
                if float(update_lines[-1]) < os.path.getmtime(spec_file_path):
                    no_changes=False; break
            if no_changes and os.path.isfile(os.path.join(WD,f)) \
                          and os.path.isfile(os.path.join(WD,erspecf)) \
                          and os.path.isfile(os.path.join(WD,ersampf)) \
                          and os.path.isfile(os.path.join(WD,ersitef)) \
                          and (data_model != 3.0 or os.path.isfile(os.path.join(WD,erlocf))):
                magic_files['measurements'].append(os.path.join(WD,f))
                magic_files['specimens'].append(os.path.join(WD,erspecf))
                magic_files['samples'].append(os.path.join(WD,ersampf))
                magic_files['sites'].append(os.path.join(WD,ersitef))
                magic_files['locations'].append(os.path.join(WD,erlocf))
                new_inp_file += update_file+"\r\n"
                continue
        if len(header) != len(update_lines):
            print("length of header and length of enteries for the file %s are different and will be skipped"%(update_lines[0]))
            new_inp_file += update_file+"\r\n"
            continue
        update_dict = {}
        for head,entry in zip(header,update_lines):
            update_dict[head] = entry
        if format == "CIT":
            CIT_kwargs = {}
            CIT_name = os.path.basename(os.path.splitext(update_dict["sam_path"])[0])

            CIT_kwargs["dir_path"] = WD #reduce(lambda x,y: x+"/"+y, update_dict["sam_path"].split("/")[:-1])
            CIT_kwargs["user"] = ""
            CIT_kwargs["meas_file"] = CIT_name + ".magic"
            CIT_kwargs["spec_file"] = CIT_name + "_er_specimens.txt"
            CIT_kwargs["samp_file"] = CIT_name + "_er_samples.txt"
            CIT_kwargs["site_file"] = CIT_name + "_er_sites.txt"
            CIT_kwargs["loc_file"] = CIT_name + "_locations.txt"
            CIT_kwargs["locname"] = update_dict["location"]
            CIT_kwargs["methods"] = update_dict["field_magic_codes"]
            CIT_kwargs["specnum"] = update_dict["num_terminal_char"]
            CIT_kwargs["avg"] = update_dict["dont_average_replicate_measurements"]
            CIT_kwargs["samp_con"] = update_dict["naming_convention"]
            CIT_kwargs["peak_AF"] = update_dict["peak_AF"]
            CIT_kwargs["magfile"] = os.path.basename(update_dict["sam_path"])
            CIT_kwargs["input_dir_path"] = os.path.dirname(update_dict["sam_path"])
            CIT_kwargs["data_model"] = data_model

            program_ran, error_message = cit_magic.main(command_line=False, **CIT_kwargs)

            measp = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["meas_file"])
            specp = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["spec_file"])
            sampp = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["samp_file"])
            sitep = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["site_file"])
            locp = os.path.join(CIT_kwargs["dir_path"],CIT_kwargs["loc_file"])

            if program_ran:
                update_data = True
                update_lines[-1] = time()
                new_inp_file += reduce(lambda x,y: str(x)+"\t"+str(y), update_lines)+"\r\n"
                magic_files['measurements'].append(measp)
                magic_files['specimens'].append(specp)
                magic_files['samples'].append(sampp)
                magic_files['sites'].append(sitep)
                magic_files['locations'].append(locp)
            else:
                new_inp_file += update_file
                if os.path.isfile(measp) and \
                   os.path.isfile(specp) and \
                   os.path.isfile(sampp) and \
                   os.path.isfile(sitep) and \
                   os.path.isfile(locp):
                    magic_files['measurements'].append(measp)
                    magic_files['specimens'].append(specp)
                    magic_files['samples'].append(sampp)
                    magic_files['sites'].append(sitep)
                    magic_files['locations'].append(locp)

    inp_file.close()
    out_file = open(inp_file_name, "w")
    out_file.write(new_inp_file)
    return update_data

def combine_magic_files(WD,magic_files,data_model=2.5):
    if type(magic_files) != dict: return
    if data_model==3.0:
        if 'measurements' in magic_files.keys():
            combine_magic(magic_files['measurements'], WD+"/measurements.txt")
        if 'specimens' in magic_files.keys():
            combine_magic(magic_files['specimens'], WD+"/specimens.txt")
        if 'samples' in magic_files.keys():
            combine_magic(magic_files['samples'], WD+"/samples.txt")
        if 'sites' in magic_files.keys():
            combine_magic(magic_files['sites'], WD+"/sites.txt")
        if 'locations' in magic_files.keys():
            combine_magic(magic_files['locations'], WD+"/locations.txt")
    else:
        if 'measurements' in magic_files.keys():
            combine_magic(magic_files['measurements'], WD+"/magic_measurements.txt")
        if 'specimens' in magic_files.keys():
            combine_magic(magic_files['specimens'], WD+"/er_specimens.txt")
        if 'samples' in magic_files.keys():
            combine_magic(magic_files['samples'], WD+"/er_samples.txt")
        if 'sites' in magic_files.keys():
            combine_magic(magic_files['sites'], WD+"/er_sites.txt")

def pick_inp(parent,WD):
    dlg = wx.FileDialog(
        parent, message="choose .inp file",
        defaultDir=WD,
        defaultFile="magic.inp",
        wildcard="*.inp",
        style=wx.OPEN
        )
    if dlg.ShowModal() == wx.ID_OK:
        inp_file_name = dlg.GetPath()
    else:
        inp_file_name = None
    dlg.Destroy()
    return inp_file_name

def read_LSQ(filepath):
    fin = open(filepath, 'r')
    interps = fin.read().splitlines()
    interps_out = []
    parse_LSQ_bound = lambda x: ord(x)-ord("A") if ord(x)-ord("A") < 26 else ord(x)-ord("A")-6
    for i,interp in enumerate(interps):
        interps_out.append({})
        enteries = interp.split()
        interps_out[i]['er_specimen_name'] = enteries[0]
        if enteries[1] == 'L':
            interps_out[i]['magic_method_codes'] = 'DE-BFL:DA-DIR-GEO'
        if enteries[1] == 'P':
            interps_out[i]['magic_method_codes'] = 'DE-BFP:DA-DIR-GEO'
        if enteries[1] == 'C':
            interps_out[i]['magic_method_codes'] = 'DE-FM:DA-DIR-GEO'
        j = 2
        if len(enteries) > 9: interps_out[i]['specimen_comp_name'] = enteries[j]; j += 1;
        else: interps_out[i]['specimen_comp_name'] = None
        interps_out[i]['specimen_dec'] = enteries[j]
        interps_out[i]['specimen_inc'] = enteries[j+1]
        j += 4
        bounds = enteries[j].split('-')
        lower = bounds[0]
        upper = bounds[-1]
        if len(bounds[0]) > 1: lower = lower[0]
        if len(bounds[-1]) > 1: upper = upper[-1]
        interps_out[i]['measurement_min_index'] = parse_LSQ_bound(lower)
        interps_out[i]['measurement_max_index'] = parse_LSQ_bound(upper)
        bad_meas = [bounds[k] for k in range(len(bounds)) if len(bounds[k]) > 1]
        for bad_m in bad_meas:
            if bad_m==bounds[-1] and len(bad_m)>2: bad_m = bad_m[:-1]
            elif bad_m==bounds[0] and len(bad_m)>2: bad_m = bad_m[1:]
            fc = parse_LSQ_bound(bad_m[0])
            lc = parse_LSQ_bound(bad_m[-1])
            interps_out[i]['bad_measurement_index'] = []
            for k in range(1,lc-fc):
                interps_out[i]['bad_measurement_index'].append(fc+k)
        interps_out[i]['specimen_n'] = enteries[j+1]
        interps_out[i]['specimen_mad'] = enteries[j+2]
    fin.close()
    return interps_out

def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

def Rotate_zijderveld(Zdata,rot_declination):
    if len(Zdata)==0:
        return([])
    CART_rot=[]
    for i in range(0,len(Zdata)):
        DIR=cart2dir(Zdata[i])
        DIR[0]=(DIR[0]-rot_declination)%360.
        CART_rot.append(array(dir2cart(DIR)))
    CART_rot=array(CART_rot)
    return(CART_rot)

def draw_net(FIG):
    FIG.clear()
    eq=FIG
    eq.axis((-1,1,-1,1))
    eq.axis('off')
    theta=arange(0.,2*pi,2*pi/1000)
    eq.plot(cos(theta),sin(theta),'k',clip_on=False,lw=1)
    #eq.vlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
    #eq.hlines((0,0),(0.9,-0.9),(1.0,-1.0),'k')
    #eq.plot([0.0],[0.0],'+k')

    Xsym,Ysym=[],[]
    for I in range(10,100,10):
        XY=dimap(0.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    for I in range(10,90,10):
        XY=dimap(90.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    for I in range(10,90,10):
        XY=dimap(180.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    for I in range(10,90,10):
        XY=dimap(270.,I)
        Xsym.append(XY[0])
        Ysym.append(XY[1])
    eq.plot(Xsym,Ysym,'k+',clip_on=False,mew=0.5)
    for D in range(0,360,10):
        Xtick,Ytick=[],[]
        for I in range(4):
            XY=dimap(D,I)
            Xtick.append(XY[0])
            Ytick.append(XY[1])
        eq.plot(Xtick,Ytick,'k',clip_on=False,lw=0.5)
    eq.axes.set_aspect('equal')

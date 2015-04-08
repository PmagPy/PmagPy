#!/usr/bin/env python
import pmag,sys,string
def main():
    """ 
    ODP_samples_magic.py
    OPTIONS:
        -f FILE, input csv file
        -Fsa FILE, output er_samples.txt file for updating, default is to overwrite er_samples.txt
    """
    dir_path='.'
    comp_depth_key=""
    if "-WD" in sys.argv:
        ind=sys.argv.index("-WD")
        dir_path=sys.argv[ind+1]
    if "-ID" in sys.argv:
        ind = sys.argv.index("-ID")
        input_dir_path = sys.argv[ind+1]
    else:
        input_dir_path = dir_path
    output_dir_path = dir_path
    if "-h" in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        samp_file=sys.argv[ind+1]
    else:
        print "must specify -f samp_file"
        sys.exit()
    samp_file = input_dir_path+'/'+samp_file
    Samps=[]
    if '-Fsa' in sys.argv:
        ind=sys.argv.index("-Fsa")
        samp_out = output_dir_path+'/'+sys.argv[ind+1]
        Samps,file_type = pmag.magic_read(samp_out)
        print len(Samps), ' read in from: ',samp_out
    else:
        samp_out = output_dir_path+'/er_samples.txt'
    input=open(samp_file,"rU").readlines()
    keys=input[0].replace('\n','').split(',')
    if "CSF-B Top (m)" in keys: 
        comp_depth_key="CSF-B Top (m)"
    elif "Top depth CSF-B (m)" in keys: 
        comp_depth_key="Top depth CSF-B (m)"
    if "Top Depth (m)" in keys:  # incorporate changes to LIMS data model, while maintaining backward compatibility
        depth_key="Top Depth (m)"
    elif "CSF-A Top (m)" in keys:
        depth_key="CSF-A Top (m)"
    elif "Top depth CSF-A (m)" in keys:
        depth_key="Top depth CSF-A (m)"
    if "Text Id" in keys:
        text_key="Text Id"
    elif "Text identifier" in keys:
        text_key="Text identifier"
    if "Sample Date Logged" in keys:
        date_key="Sample Date Logged"
    elif "Sample date logged" in keys:
        date_key="Sample date logged"
    elif "Date sample logged" in keys:
        date_key="Date sample logged"
    ErSamples,samples,format=[],[],'old'
    for line in input[1:]:
        ODPRec,SampRec={},{}
        interval,core="",""
        rec=line.replace('\n','').split(',')
        for k in range(len(keys)):ODPRec[keys[k]]=rec[k].strip('"')
        SampRec['er_sample_alternatives']=ODPRec[text_key]
        if "Label Id" in keys: # old format
            label=ODPRec['Label Id'].split()
            if len(label)>1: 
                interval=label[1].split('/')[0]
                pieces=label[0].split('-')
                core=pieces[2]
            while len(core)<4:core='0'+core # my way
        else: # new format
            format='new'
            pieces=[ODPRec['Exp'],ODPRec['Site']+ODPRec['Hole'],ODPRec['Core']+ODPRec['Type'],ODPRec['Sect'],ODPRec['A/W']]
            interval=ODPRec['Top offset (cm)'].split('.')[0].strip() # only integers allowed!
            core=ODPRec['Core']+ODPRec['Type']
        if core!="" and interval!="":   
            SampRec['magic_method_codes']='FS-C-DRILL-IODP:SP-SS-C:SO-V'
            if format=='old':
                SampRec['er_sample_name']=pieces[0]+'-'+pieces[1]+'-'+core+'-'+pieces[3]+'-'+pieces[4]+'-'+interval
            else:
                SampRec['er_sample_name']=pieces[0]+'-'+pieces[1]+'-'+core+'-'+pieces[3]+'_'+pieces[4]+'_'+interval # change in sample name convention
            SampRec['er_site_name']=SampRec['er_sample_name']
            #pieces=SampRec['er_sample_name'].split('-')
            SampRec['er_expedition_name']=pieces[0]
            SampRec['er_location_name']=pieces[1]
            SampRec['er_citation_names']="This study"
            SampRec['sample_dip']="0"
            SampRec['sample_azimuth']="0"
            SampRec['sample_core_depth']=ODPRec[depth_key]
            if ODPRec['Volume (cc)']!="":
                SampRec['sample_volume']=str(float(ODPRec['Volume (cc)'])*1e-6)
            else:
                SampRec['sample_volume']='1'
            if comp_depth_key!="":
                SampRec['sample_composite_depth']=ODPRec[comp_depth_key]
            dates=ODPRec[date_key].split()
            if '/' in dates[0]: # have a date
                mmddyy=dates[0].split('/')
                yyyy='20'+mmddyy[2] 
                mm=mmddyy[0]
                if len(mm)==1:mm='0'+mm
                dd=mmddyy[1]
                if len(dd)==1:dd='0'+dd
                date=yyyy+':'+mm+':'+dd+':'+dates[1]+":00.00"
            else:
                date=""
            SampRec['sample_date']=date
            ErSamples.append(SampRec)
            samples.append(SampRec['er_sample_name'])
    if len(Samps)>0:
        for samp in Samps:
           if samp['er_sample_name'] not in samples:
               ErSamples.append(samp)
    Recs,keys=pmag.fillkeys(ErSamples)
    pmag.magic_write(samp_out,Recs,'er_samples')
    print 'sample information written to: ',samp_out  
main()

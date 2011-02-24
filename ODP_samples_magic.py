#!/usr/bin/env python
import pmag,sys,string
def main():
    """ 
    ODP_samples_magic.py
    OPTIONS:
        -f FILE, input csv file
        -Fsa FILE, output er_samples.txt file for updating, default is to overwrite er_samples.txt`
    """
    samp_out="er_samples.txt"
    dir_path='.'
    if "-WD" in sys.argv:
        ind=sys.argv.index("-WD")
        dir_path=sys.argv[ind+1]
    if "-h" in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        samp_file=sys.argv[ind+1]
    else:
        print "must specify -f samp_file"
        sys.exit()
    samp_file=dir_path+'/'+samp_file
    Samps=[]
    if '-Fsa' in sys.argv:
        ind=sys.argv.index("-Fsa")
        samp_out=dir_path+'/'+sys.argv[ind+1]
        Samps,file_type=pmag.magic_read(samp_out)
        print len(Samps), ' read in from: ',samp_out
    input=open(samp_file,"rU").readlines()
    keys=input[0].replace('\n','').split(',')
    ErSamples,samples=[],[]
    for line in input[1:]:
        ODPRec,SampRec={},{}
        rec=line.replace('\n','').split(',')
        for k in range(len(keys)):ODPRec[keys[k]]=rec[k]
        SampRec['er_sample_alternatives']=ODPRec['Text Id']
        label=ODPRec['Label Id'].split()
        if len(label)>1 and 'PMAG' not in label[0]:
            interval=label[1].split('/')[0]
            pieces=label[0].split('-')
            core=pieces[2]
            while len(core)<4:core='0'+core
            SampRec['magic_method_codes']='FS-C-DRILL-IODP:FS-SS-C:SO-V'
            SampRec['er_sample_name']=pieces[0]+'-'+pieces[1]+'-'+core+'-'+pieces[3]+'-'+pieces[4]+'-'+interval
            SampRec['er_site_name']=SampRec['er_sample_name']
            pieces=SampRec['er_sample_name'].split('-')
            SampRec['er_expedition_name']=pieces[0]
            SampRec['er_location_name']=pieces[1]
            SampRec['er_citation_names']="This study"
            SampRec['sample_dip']="0"
            SampRec['sample_azimuth']="0"
            SampRec['sample_core_depth']=ODPRec['Top Depth (m)']
            dates=ODPRec['Sample Date Logged'].split()
            mmddyy=dates[0].split('/')
            yyyy='20'+mmddyy[2] 
            mm=mmddyy[0]
            if len(mm)==1:mm='0'+mm
            dd=mmddyy[1]
            if len(dd)==1:dd='0'+dd
            date=yyyy+':'+mm+':'+dd+':'+dates[1]+":00.00"
            SampRec['sample_date']=date
            ErSamples.append(SampRec)
            samples.append(SampRec['er_sample_name'])
    if len(Samps)>0:
        for samp in Samps:
           if samp['er_sample_name'] not in samples:
               ErSamples.append(samp)
    Recs,keys=pmag.fillkeys(ErSamples)
    pmag.magic_write(samp_out,Recs,'er_samples')
    print('sample information written to er_samples.txt')              
main()

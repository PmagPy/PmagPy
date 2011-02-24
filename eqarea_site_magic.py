#!/usr/bin/env python
import sys,pmag
def main():
    """
    NAME
        lnp_magic.py

    DESCRIPTION
       makes equal area projections site by site
         from pmag_specimen formatted file with
         Fisher confidence ellipse using McFadden and McElhinny (1988)
         technique for combining lines and planes

    SYNTAX
        lnp_magic -h [command line options]

    INPUT
       takes magic formatted pmag_specimens file
    
    OUPUT
        prints site_name n_lines n_planes K alpha95 dec inc R

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is 'pmag_specimens.txt'
        -crd [s,g,t]: specify coordinate system, [s]pecimen, [g]eographic, [t]ilt adjusted
                default is specimen
        -fmt [svg,png,jpg] format for plots, default is svg
        -P: do not plot
        -F FILE, specify output file of dec, inc, alpha95 data for plotting with plotdi_a and plotdi_e
        -exc use criteria in pmag_criteria.txt
    """
    dir_path='.'
    FIG={} # plot dictionary
    FIG['eqarea']=1 # eqarea is figure 1
    in_file,plot_key,coord='pmag_specimens.txt','er_site_name',"-1"
    out_file=""
    fmt,plot='svg',1
    Crits=""
    M,N=180.,1
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        in_file=sys.argv[ind+1]
    if '-exc' in sys.argv:
        Crits,file_type=pmag.magic_read(dir_path+'/pmag_criteria.txt')
        for crit in Crits:
            if crit['pmag_criteria_code']=='DE-SPEC':
                M=float(crit['specimen_mad'])
                N=float(crit['specimen_n'])
    if '-F' in sys.argv:
        ind=sys.argv.index("-F")
        out_file=sys.argv[ind+1]
        out=open(dir_path+'/'+out_file,'w')
    if '-crd' in sys.argv:
        ind=sys.argv.index("-crd")
        crd=sys.argv[ind+1]
        if crd=='s':coord="-1"
        if crd=='g':coord="0"
        if crd=='t':coord="100"
    if '-fmt' in sys.argv:
        ind=sys.argv.index("-fmt")
        fmt=sys.argv[ind+1]
    if '-P' in sys.argv:plot=0
# 
    in_file=dir_path+'/'+in_file
    Specs,file_type=pmag.magic_read(in_file)
    sitelist=[]
    for rec in Specs:
        if rec['er_site_name'] not in sitelist: sitelist.append(rec['er_site_name'])
    sitelist.sort()
    if plot==1:
        import pmagplotlib
        EQ={} 
        EQ['eqarea']=1
        pmagplotlib.plot_init(EQ['eqarea'],4,4)
    for site in sitelist:
        print site
        data=[]
        for spec in Specs:
           if 'specimen_tilt_correction' not in spec.keys():spec['specimen_tilt_correction']='-1' # assume unoriented
           if spec['er_site_name']==site:
             if spec['specimen_mad']!="" and spec['specimen_n']!="":
               if spec['specimen_tilt_correction']==coord and float(spec['specimen_mad'])<=M and float(spec['specimen_n'])>=N: 
                   rec={}
                   for key in spec.keys():rec[key]=spec[key]
                   rec["dec"]=float(spec['specimen_dec'])
                   rec["inc"]=float(spec['specimen_inc'])
                   rec["tilt_correction"]=spec['specimen_tilt_correction']
                   data.append(rec)
        if len(data)>2:
            print 'specimen, dec, inc, n_meas/MAD,| method codes '
            for i  in range(len(data)):
                print '%s: %7.1f %7.1f %s / %s | %s' % (data[i]['er_specimen_name'], data[i]['dec'], data[i]['inc'], data[i]['specimen_n'], data[i]['specimen_mad'], data[i]['magic_method_codes'])

            fpars=pmag.dolnp(data,'specimen_direction_type')
            print "\n Site lines planes  kappa   a95   dec   inc"
            print site, fpars["n_lines"], fpars["n_planes"], fpars["K"], fpars["alpha95"], fpars["dec"], fpars["inc"], fpars["R"]
            if out_file!="":
                if float(fpars["alpha95"])<=acutoff and float(fpars["K"])>=kcutoff:
                    out.write('%s %s %s\n'%(fpars["dec"],fpars['inc'],fpars['alpha95']))
            print '% tilt correction: ',coord
            if plot==1:
                pmagplotlib.plotLNP(EQ['eqarea'],site,data,fpars,'specimen_direction_type')
                ans=raw_input("s[a]ve plot, [q]uit, [e]dit specimens, <return> to continue:\n ")
                if ans=="a":
                    files={}
                    files['eqarea']=site+'_'+crd+'_'+'eqarea'+'.'+fmt
                    pmagplotlib.saveP(EQ,files)
                if ans=="q": sys.exit()
                if ans=="e": 
                    spec=raw_input("Enter specimen name to check orientation ")
                    data=pmag.mark_sample(spec,data)
                    print 'not yet available -  stay tuned'
                    sys.exit()
   
        else:
            print 'skipping site - not enough data with specified coordinate system'
         
main()

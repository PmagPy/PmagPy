#!/usr/bin/env python
import pmag,math,sys
def main():
    """
    NAME 
        pmag_results_extract.py

    DESCRIPTION
        make a tab delimited output file from pmag_results table
 
    SYNTAX
        pmag_results_extract.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f RFILE, specify pmag_results table; default is pmag_results.txt
        -fa AFILE, specify er_ages table; default is NONE
        -fsp SFILE, specify pmag_specimens table, default is NONE
        -g include specimen_grade in table - only works for PmagPy generated pmag_specimen formatted files.
        -tex,  output in LaTeX format
    """
    dir_path='.'
    res_file='pmag_results.txt'
    spec_file=''
    age_file=""
    latex=0
    grade=0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        res_file=sys.argv[ind+1]
    if '-fsp' in sys.argv:
        ind = sys.argv.index('-fsp')
        spec_file=sys.argv[ind+1]
    if '-fa' in sys.argv:
        ind = sys.argv.index('-fa')
        age_file=sys.argv[ind+1]
    if '-g' in sys.argv:grade=1
    if '-tex' in sys.argv: 
        latex=1
        outfile='Directions.tex'
        Ioutfile='Intensities.tex'
        Soutfile='SiteNfo.tex'
        Specout='Specimens.tex'
    else:
        latex=0
        outfile='Directions.txt'
        Ioutfile='Intensities.txt'
        Soutfile='SiteNfo.txt'
        Specout='Specimens.txt'
    # read in pmag_results file
    res_file=dir_path+'/'+res_file
    if spec_file!="":spec_file=dir_path+'/'+spec_file
    outfile=dir_path+'/'+outfile
    Ioutfile=dir_path+'/'+Ioutfile
    Soutfile=dir_path+'/'+Soutfile
    Specout=dir_path+'/'+Specout
    f=open(outfile,'w')
    sf=open(Soutfile,'w')
 # do directions first
    if latex==0:
        Soutstring='%s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s\n'%("Site","Samples","Location","Lat. (N)","Long. (E)","Age ","Units","Dip Dir","Dip")
        outstring='%s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s\n'%("Site","Samples",'Comp.',"%TC","Dec.","Inc.","Nl","Np","k    ","R","a95","PLat","PLong")
        f.write(outstring)
        sf.write(Soutstring)
    else:
        f.write('\\begin{table}\n')
        sf.write('\\begin{table}\n')
        f.write('\\begin{tabular}{rrrrrrrrrrrr}\n')
        sf.write('\\begin{tabular}{rrrrrrrr}\n')
        f.write('\hline\n')
        sf.write('\hline\n')
        Soutstring='%s & %s & %s & %s & %s & %s & %s & %s & %s %s\n'%("Site", "Samples","Location","Lat. (N)","Long. (E)","Age ","Units","Dip Dir","Dip",'\\\\')
        outstring='%s & %s & %s & %s & %s & %s & %s & %s & %s & %s & %s & %s & %s %s\n'%("Site", "Samples","Comp.","\%TC","Dec.","Inc.","Nl","Np","k","R","a95","PLat","PLong",'\\\\')
        f.write(outstring)
        sf.write(Soutstring)
        f.write('\hline\n')
        sf.write('\hline\n')
    Sites,file_type=pmag.magic_read(res_file)
    VGPs=pmag.get_dictitem(Sites,'vgp_lat','','F') # get all results with VGPs
    for site in VGPs:
        if len(site['er_site_names'].split(":"))==1:
            if 'er_sample_names' not in site.keys():site['er_sample_names']=''
            if 'pole_comp_name' in site.keys():
               comp=site['pole_comp_name'] 
            else:
               comp="A"
            if 'average_n_lines' not in site.keys():site['average_n_lines']=site['average_nn']
            if 'average_n_planes' not in site.keys():site['average_n_planes']=""
            if latex==0:
                outstring='%s \t %s \t %s \t %s \t %s \t %s\n'%(site["er_site_names"],site["er_sample_names"],site["average_lat"],site["average_lon"],site["average_age"],site["average_age_unit"])
                sf.write(outstring)
                outstring='%s \t %s \t %s \t  %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s \t %s\n'%(site["er_site_names"],site["er_sample_names"],comp,site["tilt_correction"],site["average_dec"],site["average_inc"],site["average_n_lines"],site["average_n_planes"],site["average_k"],site["average_r"],site["average_alpha95"],site["vgp_lat"],site["vgp_lon"])
                f.write(outstring)
            else:
                outstring='%s & %s & %s & %s & %s & %s%s\n'%(site["er_site_names"],site["er_sample_names"],site["average_lat"],site["average_lon"],site["average_age"],site["average_age_unit"],'\\\\')
                sf.write(outstring)
                outstring='%s & %s & %s & %s & %s & %s & %s & %s& %s & %s & %s & %s & %s%s\n'%(site["er_site_names"],site["er_sample_names"],comp,site["tilt_correction"],site["average_dec"],site["average_inc"],site["average_n_lines"],site["average_n_planes"],site["average_k"],site["average_r"],site["average_alpha95"],site["vgp_lat"],site["vgp_lon"],'\\\\')
                f.write(outstring)
    f1=open(Ioutfile,'w') # now do intensities
    if spec_file!="": fsp=open(Specout,'w')
    if latex==0:
        outstring='%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'%("Site","Samples","N_B","B (uT)","s_b","s_b\%","VADM","s_vadm")
        f1.write(outstring)
        if spec_file!="":
            if grade:
                outstring='%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t %s\t%s\n'%("Specimen","MAD","Beta","N","Q","DANG","f\_vds","DRATS","T (C)",'Corrections','Grade')
            else:
                outstring='%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s \t%s\n'%("Specimen","MAD","Beta","N","Q","DANG","f\_vds","DRATS","T (C)",'Corrections')
            fsp.write(outstring)
    else:
        f1.write('\\begin{table}\n')
        f1.write('\\begin{tabular}{rrrrrrr}\n')
        f1.write('\hline\n')
        outstring='%s & %s & %s & %s & %s & %s & %s & %s%s\n'%("Site","Samples","N_B","B (uT)","s_b","s_b\%","VADM","s_vadm","\\\\")
        f1.write(outstring)
        if spec_file!="":
            fsp.write('\\begin{table}\n')
            if grade:
                fsp.write('\\begin{tabular}{rrrrrrrrrrr}\n')
            else:
                fsp.write('\\begin{tabular}{rrrrrrrrrr}\n')
            fsp.write('\hline\n')
            if grade:
                outstring='%s & %s & %s & %s & %s & %s & %s & %s & %s & %s & %s\n'%("Specimen","MAD","Beta","N","Q","DANG","f\_vds","DRATS","T (C)",'Corrections',"Grade\\\\")
            else:
                outstring='%s & %s & %s & %s & %s & %s & %s & %s  & %s & %s\n'%("Specimen","MAD","Beta","N","Q","DANG","f\_vds","DRATS","T (C)",'Corrections\\\\')
            fsp.write(outstring)
            fsp.write('\hline\n')
    VDMs=pmag.get_dictitem(Sites,'vdm','','F')
    for site in VDMs: # do results level stuff
      if len(site['er_site_names'].split(":"))==1:
            if 'average_int_sigma_perc' not in site.keys():site['average_int_sigma_perc']="0"
            if site["average_int_sigma"]=="":site["average_int_sigma"]="0"        
            if site["average_int_sigma_perc"]=="":site["average_int_sigma_perc"]="0"        
            if site["vadm"]=="":site["vadm"]="0"        
            if site["vadm_sigma"]=="":site["vadm_sigma"]="0"        
            if latex==0:
                outstring='%s\t%s\t%s\t%6.2f\t%5.2f\t%5.1f\t%6.2f\t%5.2f \n'%(site["er_site_names"],site["er_sample_names"],site["average_int_n"],1e6*float(site["average_int"]),1e6*float(site["average_int_sigma"]),float(site['average_int_sigma_perc']),1e-21*float(site["vadm"]),1e-21*float(site["vadm_sigma"]))
                f1.write(outstring)
            else:
                outstring='%s & %s & %s & %6.2f\t%5.2f & %5.1f & %6.2f & %5.2f %s\n'%(site["er_site_names"],site["er_sample_names"],site["average_int_n"],1e6*float(site["average_int"]),1e6*float(site["average_int_sigma"]),float(site['average_int_sigma_perc']),1e-21*float(site["vadm"]),1e-21*float(site["vadm_sigma"]),'\\\\')
                f1.write(outstring)
    VADMs=pmag.get_dictitem(Sites,'vadm','','F')
    for site in VADMs: # do results level stuff
      if len(site['er_site_names'].split(":"))==1:
            if 'average_int_sigma_perc' not in site.keys():site['average_int_sigma_perc']="0"
            if site["average_int_sigma"]=="":site["average_int_sigma"]="0"        
            if site["average_int_sigma_perc"]=="":site["average_int_sigma_perc"]="0"        
            if site["vadm"]=="":site["vadm"]="0"        
            if site["vadm_sigma"]=="":site["vadm_sigma"]="0"        
            if latex==0:
                outstring='%s\t%s\t%s\t%6.2f\t%5.2f\t%5.1f\t%6.2f\t%5.2f \n'%(site["er_site_names"],site["er_sample_names"],site["average_int_n"],1e6*float(site["average_int"]),1e6*float(site["average_int_sigma"]),float(site['average_int_sigma_perc']),1e-21*float(site["vadm"]),1e-21*float(site["vadm_sigma"]))
                f1.write(outstring)
            else:
                outstring='%s & %s & %s & %6.2f\t%5.2f & %5.1f & %6.2f & %5.2f %s\n'%(site["er_site_names"],site["er_sample_names"],site["average_int_n"],1e6*float(site["average_int"]),1e6*float(site["average_int_sigma"]),float(site['average_int_sigma_perc']),1e-21*float(site["vadm"]),1e-21*float(site["vadm_sigma"]),'\\\\')
                f1.write(outstring)
    # put specimen level data here!  
    if spec_file!="": 
        Specs,file_type=pmag.magic_read(spec_file)
        for spec in Specs:
            trange= '%i'%(int(float(spec['measurement_step_min'])-273))+'-'+'%i'%(int(float(spec['measurement_step_max'])-273))
            meths=spec['magic_method_codes'].split(':')
            corrections=''
            for meth in meths:
                if 'DA' in meth:corrections=corrections+meth[3:]+':'
            corrections=corrections.strip(':') 
            if corrections.strip()=="":corrections="None"
            if latex==0:
                if grade:
                    outstring='%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'%(spec['er_specimen_name'],spec['specimen_int_mad'],spec['specimen_b_beta'],spec['specimen_int_n'],spec['specimen_q'],spec['specimen_dang'],spec['specimen_fvds'],spec['specimen_drats'],trange,corrections,spec['specimen_grade'])
                else:
                    outstring='%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'%(spec['er_specimen_name'],spec['specimen_int_mad'],spec['specimen_b_beta'],spec['specimen_int_n'],spec['specimen_q'],spec['specimen_dang'],spec['specimen_fvds'],spec['specimen_drats'],trange,corrections)
                fsp.write(outstring)
            else: 
                if grade:
                    outstring='%s & %s & %s & %s & %s & %s & %s & %s & %s & %s & %s \n'%(spec['er_specimen_name'],spec['specimen_int_mad'],spec['specimen_b_beta'],spec['specimen_int_n'],spec['specimen_q'],spec['specimen_dang'],spec['specimen_fvds'],spec['specimen_drats'],trange,corrections,spec['specimen_grade']+'\\\\')
                else:
                    outstring='%s & %s & %s & %s & %s & %s & %s & %s & %s & %s \n'%(spec['er_specimen_name'],spec['specimen_int_mad'],spec['specimen_b_beta'],spec['specimen_int_n'],spec['specimen_q'],spec['specimen_dang'],spec['specimen_fvds'],spec['specimen_drats'],trange,corrections+'\\\\')
                fsp.write(outstring)
    # 
    if latex==1:
        f.write('\hline\n')
        sf.write('\hline\n')
        f1.write('\hline\n')
        f.write('\end{tabular}\n')
        sf.write('\end{tabular}\n')
        f.write('\end{table}\n')
        f1.write('\end{table}\n')
        if spec_file!="":
            fsp.write('\hline\n')
            fsp.write('\end{tabular}\n')
            fsp.write('\end{table}\n')
    f.close()
    sf.close()
    f1.close()
    print 'data saved in: ',outfile,Ioutfile,Soutfile
    if spec_file!="":
        fsp.close()
        print 'specimen data saved in: ',Specout
main()

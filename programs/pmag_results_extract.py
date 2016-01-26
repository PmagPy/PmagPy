#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

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
        -fcr CFILE, specify pmag_criteria table, default is NONE
        -g include specimen_grade in table - only works for PmagPy generated pmag_specimen formatted files.
        -tex,  output in LaTeX format
    """
    dir_path='.'
    res_file='pmag_results.txt'
    crit_file=''
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
    if '-fcr' in sys.argv:
        ind = sys.argv.index('-fcr')
        crit_file=sys.argv[ind+1]
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
        Critout='Criteria.tex'
    else:
        latex=0
        outfile='Directions.txt'
        Ioutfile='Intensities.txt'
        Soutfile='SiteNfo.txt'
        Specout='Specimens.txt'
        Critout='Criteria.txt'
    res_file=dir_path+'/'+res_file
    if crit_file!="":crit_file=dir_path+'/'+crit_file
    if spec_file!="":spec_file=dir_path+'/'+spec_file
# open output files
    outfile=dir_path+'/'+outfile
    Ioutfile=dir_path+'/'+Ioutfile
    Soutfile=dir_path+'/'+Soutfile
    Specout=dir_path+'/'+Specout
    Critout=dir_path+'/'+Critout
    f=open(outfile,'w')
    sf=open(Soutfile,'w')
    fI=open(Ioutfile,'w') 
    cr=open(Critout,'w') 
# set up column headers
    Sites,file_type=pmag.magic_read(res_file)
    if crit_file!="":
        Crits,file_type=pmag.magic_read(crit_file)
    else:
        Crits=[]
    SiteCols=["Site","Location","Lat. (N)","Long. (E)","Age ","Age sigma","Units"]
    SiteKeys=["er_site_names","average_lat","average_lon","average_age","average_age_sigma","average_age_unit"]
    DirCols=["Site",'Comp.',"perc TC","Dec.","Inc.","Nl","Np","k    ","R","a95","PLat","PLong"]
    DirKeys=["er_site_names","pole_comp_name","tilt_correction","average_dec","average_inc","average_n_lines","average_n_planes","average_k","average_r","average_alpha95","vgp_lat","vgp_lon"]
    IntCols=["Site","N","B (uT)","sigma","sigma perc","VADM","VADM sigma"]
    IntKeys=["er_site_names","average_int_n","average_int","average_int_sigma",'average_int_sigma_perc',"vadm","vadm_sigma"]
    AllowedKeys=['specimen_frac','specimen_scat','specimen_gap_max','measurement_step_min', 'measurement_step_max', 'measurement_step_unit', 'specimen_polarity', 'specimen_nrm', 'specimen_direction_type', 'specimen_comp_nmb', 'specimen_mad', 'specimen_alpha95', 'specimen_n', 'specimen_int_sigma', 'specimen_int_sigma_perc', 'specimen_int_rel_sigma', 'specimen_int_rel_sigma_perc', 'specimen_int_mad', 'specimen_int_n', 'specimen_w', 'specimen_q', 'specimen_f', 'specimen_fvds', 'specimen_b_sigma', 'specimen_b_beta', 'specimen_g', 'specimen_dang', 'specimen_md', 'specimen_ptrm', 'specimen_drat', 'specimen_drats', 'specimen_rsc', 'specimen_viscosity_index', 'specimen_magn_moment', 'specimen_magn_volume', 'specimen_magn_mass', 'specimen_int_ptrm_n', 'specimen_delta', 'specimen_theta', 'specimen_gamma', 'sample_polarity', 'sample_nrm', 'sample_direction_type', 'sample_comp_nmb', 'sample_sigma', 'sample_alpha95', 'sample_n', 'sample_n_lines', 'sample_n_planes', 'sample_k', 'sample_r', 'sample_tilt_correction', 'sample_int_sigma', 'sample_int_sigma_perc', 'sample_int_rel_sigma', 'sample_int_rel_sigma_perc', 'sample_int_n', 'sample_magn_moment', 'sample_magn_volume', 'sample_magn_mass', 'site_polarity', 'site_nrm', 'site_direction_type', 'site_comp_nmb', 'site_sigma', 'site_alpha95', 'site_n', 'site_n_lines', 'site_n_planes', 'site_k', 'site_r', 'site_tilt_correction', 'site_int_sigma', 'site_int_sigma_perc', 'site_int_rel_sigma', 'site_int_rel_sigma_perc', 'site_int_n', 'site_magn_moment', 'site_magn_volume', 'site_magn_mass', 'average_age_min', 'average_age_max', 'average_age_sigma', 'average_age_unit', 'average_sigma', 'average_alpha95', 'average_n', 'average_nn', 'average_k', 'average_r', 'average_int_sigma', 'average_int_rel_sigma', 'average_int_rel_sigma_perc', 'average_int_n', 'average_int_nn', 'vgp_dp', 'vgp_dm', 'vgp_sigma', 'vgp_alpha95', 'vgp_n', 'vdm_sigma', 'vdm_n', 'vadm_sigma', 'vadm_n']
    if crit_file!="":
        crit=Crits[0] # get a list of useful keys
        for key in crit.keys():
            if key not in AllowedKeys:del(crit[key])
        for key in crit.keys():
            if crit[key]=='' or eval(crit[key])>1000 or eval(crit[key])==0:del(crit[key]) # get rid of all blank or too big ones or too little ones
        CritKeys=crit.keys()
    if spec_file!="": 
        Specs,file_type=pmag.magic_read(spec_file)
        fsp=open(Specout,'w') # including specimen intensities if desired
        SpecCols=["Site","Specimen","B (uT)","MAD","Beta","N","Q","DANG","f-vds","DRATS","T (C)"]
        SpecKeys=['er_site_name','er_specimen_name','specimen_int','specimen_int_mad','specimen_b_beta','specimen_int_n','specimen_q','specimen_dang','specimen_fvds','specimen_drats','trange']
        Xtra=['specimen_frac','specimen_scat','specimen_gmax']
        if grade:
            SpecCols.append('Grade')
            SpecKeys.append('specimen_grade')
        for x in Xtra:  # put in the new intensity keys if present
            if x in Specs[0].keys():
                SpecKeys.append(x)
                newkey=""
                for k in x.split('_')[1:]:newkey=newkey+k+'_'
                SpecCols.append(newkey.strip('_'))
        SpecCols.append('Corrections')
        SpecKeys.append('corrections')
    Micro=['specimen_int','average_int','average_int_sigma'] # these should be multiplied by 1e6
    Zeta=['vadm','vadm_sigma'] # these should be multiplied by 1e21
    # write out the header information for each output file
    if latex: #write out the latex header stuff
        sep=' & '
        end='\\\\'
        f.write('\\documentclass{article}\n')
        f.write('\\usepackage[margin=1in]{geometry}\n')
        f.write('\\usepackage{longtable}\n')
        f.write('\\begin{document}\n')
        sf.write('\\documentclass{article}\n')
        sf.write('\\usepackage[margin=1in]{geometry}\n')
        sf.write('\\usepackage{longtable}\n')
        sf.write('\\begin{document}\n')
        fI.write('\\documentclass{article}\n')
        fI.write('\\usepackage[margin=1in]{geometry}\n')
        fI.write('\\usepackage{longtable}\n')
        fI.write('\\begin{document}\n')
        if crit_file!="":
            cr.write('\\documentclass{article}\n')
            cr.write('\\usepackage[margin=1in]{geometry}\n')
            cr.write('\\usepackage{longtable}\n')
            cr.write('\\begin{document}\n')
        if spec_file!="": 
            fsp.write('\\documentclass{article}\n')
            fsp.write('\\usepackage[margin=1in]{geometry}\n')
            fsp.write('\\usepackage{longtable}\n')
            fsp.write('\\begin{document}\n')
        tabstring='\\begin{longtable}{'
        fstring=tabstring
        for k in range(len(SiteCols)):fstring=fstring+'r'
        sf.write(fstring+'}\n')
        sf.write('\hline\n')
        fstring=tabstring
        for k in range(len(DirCols)):fstring=fstring+'r'
        f.write(fstring+'}\n')
        f.write('\hline\n')
        fstring=tabstring
        for k in range(len(IntCols)):fstring=fstring+'r'
        fI.write(fstring+'}\n')
        fI.write('\hline\n')
        fstring=tabstring
        if crit_file!="":
            for k in range(len(CritKeys)):fstring=fstring+'r'
            cr.write(fstring+'}\n')
            cr.write('\hline\n')
        if spec_file!="":
            fstring=tabstring
            for k in range(len(SpecCols)):fstring=fstring+'r'
            fsp.write(fstring+'}\n')
            fsp.write('\hline\n')
    else:   # just set the tab and line endings for tab delimited
        sep=' \t '
        end=''
# now write out the actual column headers
    Soutstring,Doutstring,Ioutstring,Spoutstring,Croutstring="","","","",""
    for k in range(len(SiteCols)): Soutstring=Soutstring+SiteCols[k]+sep
    Soutstring=Soutstring.strip(sep) 
    Soutstring=Soutstring+end +'\n'
    sf.write(Soutstring)
    for k in range(len(DirCols)): Doutstring=Doutstring+DirCols[k]+sep
    Doutstring=Doutstring.strip(sep) 
    Doutstring=Doutstring+end +'\n'
    f.write(Doutstring)
    for k in range(len(IntCols)): Ioutstring=Ioutstring+IntCols[k]+sep
    Ioutstring=Ioutstring.strip(sep) 
    Ioutstring=Ioutstring+end +'\n'
    fI.write(Ioutstring)
    if crit_file!="":
        for k in range(len(CritKeys)): Croutstring=Croutstring+CritKeys[k]+sep
        Croutstring=Croutstring.strip(sep) 
        Croutstring=Croutstring+end +'\n'
        cr.write(Croutstring)
    if spec_file!="":
        for k in range(len(SpecCols)): Spoutstring=Spoutstring+SpecCols[k]+sep
        Spoutstring=Spoutstring.strip(sep) 
        Spoutstring=Spoutstring+end +"\n"
        fsp.write(Spoutstring)
    if latex: # put in a horizontal line in latex file
        f.write('\hline\n')
        sf.write('\hline\n')
        fI.write('\hline\n')
        if crit_file!="":cr.write('\hline\n')
        if spec_file!="": fsp.write('\hline\n')
 # do criteria 
    if crit_file!="":
        for crit in Crits: # 
            Croutstring=""
            for key in CritKeys:
                Croutstring=Croutstring+crit[key]+sep
            Croutstring=Croutstring.strip(sep) +end
            cr.write(Croutstring+'\n')
 # do directions 
    VGPs=pmag.get_dictitem(Sites,'vgp_lat','','F') # get all results with VGPs
    VGPs=pmag.get_dictitem(VGPs,'data_type','i','T') # get site level stuff
    for site in VGPs:
        if len(site['er_site_names'].split(":"))==1:
            if 'er_sample_names' not in site.keys():site['er_sample_names']=''
            if 'pole_comp_name' not in site.keys(): site['pole_comp_name']="A"
            if 'average_nn' not in site.keys() and 'average_n' in site.keys():site['average_nn']=site['average_n']
            if 'average_n_lines' not in site.keys():site['average_n_lines']=site['average_nn']
            if 'average_n_planes' not in site.keys():site['average_n_planes']=""
            Soutstring,Doutstring="",""
            for key in SiteKeys:
                if key in site.keys():Soutstring=Soutstring+site[key]+sep
            Soutstring=Soutstring.strip(sep) +end
            sf.write(Soutstring+'\n')
            for key in DirKeys:
                if key in site.keys():Doutstring=Doutstring+site[key]+sep
            Doutstring=Doutstring.strip(sep) +end
            f.write(Doutstring+'\n')
# now do intensities
    VADMs=pmag.get_dictitem(Sites,'vadm','','F')
    VADMs=pmag.get_dictitem(VADMs,'data_type','i','T')
    for site in VADMs: # do results level stuff
        if site not in VGPs:
            Soutstring=""
            for key in SiteKeys:
                if key in site.keys():
                    Soutstring=Soutstring+site[key]+sep
                else: Soutstring=Soutstring + " " + sep
            Soutstring=Soutstring.strip(sep) +end
            sf.write(Soutstring+'\n')
        if len(site['er_site_names'].split(":"))==1 and site['data_type']=='i':
            if 'average_int_sigma_perc' not in site.keys():site['average_int_sigma_perc']="0"
            if site["average_int_sigma"]=="":site["average_int_sigma"]="0"        
            if site["average_int_sigma_perc"]=="":site["average_int_sigma_perc"]="0"        
            if site["vadm"]=="":site["vadm"]="0"        
            if site["vadm_sigma"]=="":site["vadm_sigma"]="0"       
        for key in site.keys(): # reformat vadms, intensities
            if key in Micro: site[key]='%7.1f'%(float(site[key])*1e6)
            if key in Zeta: site[key]='%7.1f'%(float(site[key])*1e-21)
        outstring=""
        for key in IntKeys:
          if key not in site.keys():site[key]=""
          outstring=outstring+site[key]+sep
        outstring=outstring.strip(sep)+end +'\n'
        fI.write(outstring)
#    VDMs=pmag.get_dictitem(Sites,'vdm','','F') # get non-blank VDMs
#    for site in VDMs: # do results level stuff
#      if len(site['er_site_names'].split(":"))==1:
#            if 'average_int_sigma_perc' not in site.keys():site['average_int_sigma_perc']="0"
#            if site["average_int_sigma"]=="":site["average_int_sigma"]="0"        
#            if site["average_int_sigma_perc"]=="":site["average_int_sigma_perc"]="0"        
#            if site["vadm"]=="":site["vadm"]="0"        
#            if site["vadm_sigma"]=="":site["vadm_sigma"]="0"       
#      for key in site.keys(): # reformat vadms, intensities
#            if key in Micro: site[key]='%7.1f'%(float(site[key])*1e6)
#            if key in Zeta: site[key]='%7.1f'%(float(site[key])*1e-21)
#      outstring=""
#      for key in IntKeys:
#          outstring=outstring+site[key]+sep
#      fI.write(outstring.strip(sep)+'\n')
    if spec_file!="": 
        SpecsInts=pmag.get_dictitem(Specs,'specimen_int','','F') 
        for spec in SpecsInts:
            spec['trange']= '%i'%(int(float(spec['measurement_step_min'])-273))+'-'+'%i'%(int(float(spec['measurement_step_max'])-273))
            meths=spec['magic_method_codes'].split(':')
            corrections=''
            for meth in meths:
                if 'DA' in meth:corrections=corrections+meth[3:]+':'
            corrections=corrections.strip(':') 
            if corrections.strip()=="":corrections="None"
            spec['corrections']=corrections
            outstring=""
            for key in SpecKeys:
                if key in Micro: spec[key]='%7.1f'%(float(spec[key])*1e6)
                if key in Zeta: spec[key]='%7.1f'%(float(spec[key])*1e-21)
                outstring=outstring+spec[key]+sep
            fsp.write(outstring.strip(sep)+end+'\n')
    # 
    if latex: # write out the tail stuff
        f.write('\hline\n')
        sf.write('\hline\n')
        fI.write('\hline\n')
        f.write('\end{longtable}\n')
        sf.write('\end{longtable}\n')
        fI.write('\end{longtable}\n')
        f.write('\end{document}\n')
        sf.write('\end{document}\n')
        fI.write('\end{document}\n')
        if spec_file!="":
            fsp.write('\hline\n')
            fsp.write('\end{longtable}\n')
            fsp.write('\end{document}\n')
        if crit_file!="":
            cr.write('\hline\n')
            cr.write('\end{longtable}\n')
            cr.write('\end{document}\n')
    f.close()
    sf.close()
    fI.close()
    print 'data saved in: ',outfile,Ioutfile,Soutfile
    if spec_file!="":
        fsp.close()
        print 'specimen data saved in: ',Specout
    if crit_file!="":
        cr.close()
        print 'Selection criteria saved in: ',Critout

if __name__ == "__main__":
    main()

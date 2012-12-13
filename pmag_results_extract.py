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
    res_file=dir_path+'/'+res_file
    if spec_file!="":spec_file=dir_path+'/'+spec_file
# open output files
    outfile=dir_path+'/'+outfile
    Ioutfile=dir_path+'/'+Ioutfile
    Soutfile=dir_path+'/'+Soutfile
    Specout=dir_path+'/'+Specout
    f=open(outfile,'w')
    sf=open(Soutfile,'w')
    fI=open(Ioutfile,'w') 
# set up column headers
    Sites,file_type=pmag.magic_read(res_file)
    SiteCols=["Site","Samples","Location","Lat. (N)","Long. (E)","Age ","Age sigma","Units"]
    SiteKeys=["er_site_names","er_sample_names","average_lat","average_lon","average_age","average_age_sigma","average_age_unit"]
    DirCols=["Site","Samples",'Comp.',"%TC","Dec.","Inc.","Nl","Np","k    ","R","a95","PLat","PLong"]
    DirKeys=["er_site_names","er_sample_names","comp","tilt_correction","average_dec","average_inc","average_n_lines","average_n_planes","average_k","average_r","average_alpha95","vgp_lat","vgp_lon"]
    IntCols=["Site","Specimens","Samples","N_B","B (uT)","s_b","s_b_perc","VADM","s_vadm"]
    IntKeys=["er_site_names","er_specimen_names","er_sample_names","average_int_n","average_int","average_int_sigma",'average_int_sigma_perc',"vadm","vadm_sigma"]
    if spec_file!="": 
        Specs,file_type=pmag.magic_read(spec_file)
        fsp=open(Specout,'w') # including specimen intensities if desired
        SpecCols=["Site","Specimen","B (uT)","MAD","Beta","N","Q","DANG","f\_vds","DRATS","T (C)"]
        SpecKeys=['er_site_name','er_specimen_name','specimen_int','specimen_int_mad','specimen_b_beta','specimen_int_n','specimen_q','specimen_dang','specimen_fvds','specimen_drats','trange']
        Xtra=['specimen_frac','specimen_scat','specimen_gap_max']
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
        f.write('\\begin{table}\n')
        sf.write('\\begin{table}\n')
        fI.write('\\begin{table}\n')
        if spec_file!="": fsp.write('\\begin{table}\n')
        tabstring='\\begin{tabular}{'
        fstring=tabstring
        for k in range(len(SiteCols)):fstring=fstring+'r'
        f.write(fstring+'}\n')
        f.write('\hline\n')
        fstring=tabstring
        for k in range(len(DirCols)):fstring=fstring+'r'
        sf.write(fstring+'}\n')
        sf.write('\hline\n')
        fstring=tabstring
        for k in range(len(IntCols)):fstring=fstring+'r'
        fI.write(fstring+'}\n')
        fI.write('\hline\n')
        if spec_file!="":
            fstring=tabstring
            for k in range(len(SpecCols)):fstring=fstring+'r'
            fsp.write(fstring+'}\n')
            fsp.write('\hline\n')
            print SpecCols
            raw_input('better?')
    else:   # just set the tab and line endings for tab delimited
        sep=' \t '
        end=''
# now write out the actual column headers
    Soutstring,Doutstring,Ioutstring,Spoutstring="","","",""
    for k in range(len(SiteCols)): Soutstring=Soutstring+SiteCols[k]+sep
    Soutstring=Soutstring+end
    Soutstring=Soutstring.strip(sep) +"\n"
    sf.write(Soutstring)
    for k in range(len(DirCols)): Doutstring=Doutstring+DirCols[k]+sep
    Doutstring=Doutstring+end
    Doutstring=Doutstring.strip(sep) +"\n"
    f.write(Doutstring)
    for k in range(len(IntCols)): Ioutstring=Ioutstring+IntCols[k]+sep
    Ioutstring=Ioutstring+end
    Ioutstring=Ioutstring.strip(sep) +"\n"
    fI.write(Ioutstring)
    if spec_file!="":
        for k in range(len(SpecCols)): Spoutstring=Spoutstring+SpecCols[k]+sep
        Spoutstring=Spoutstring+end
        Spoutstring=Spoutstring.strip(sep) +"\n"
        fsp.write(Spoutstring)
    if latex: # put in a horizontal line in latex file
        f.write('\hline\n')
        sf.write('\hline\n')
        fI.write('\hline\n')
        if spec_file!="": fsp.write('\hline\n')
 # do directions first
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
    for site in VADMs: # do results level stuff
        if site not in VGPs:
            Soutstring=""
            for key in SiteKeys:
                if key in site.keys():Soutstring=Soutstring+site[key]+sep
            Soutstring=Soutstring.strip(sep) +end
            sf.write(Soutstring+'\n')
        if len(site['er_site_names'].split(":"))==1:
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
              outstring=outstring+spec[key]+sep
            fsp.write(outstring.strip(sep)+end+'\n')
    # 
    if latex: # write out the tail stuff
        f.write('\hline\n')
        sf.write('\hline\n')
        fI.write('\hline\n')
        f.write('\end{tabular}\n')
        sf.write('\end{tabular}\n')
        fI.write('\end{tabular}\n')
        f.write('\end{table}\n')
        fI.write('\end{table}\n')
        if spec_file!="":
            fsp.write('\hline\n')
            fsp.write('\end{tabular}\n')
            fsp.write('\end{table}\n')
    f.close()
    sf.close()
    fI.close()
    print 'data saved in: ',outfile,Ioutfile,Soutfile
    if spec_file!="":
        fsp.close()
        print 'specimen data saved in: ',Specout
main()

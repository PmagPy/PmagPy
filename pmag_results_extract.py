#!/usr/bin/env python
# define some variables
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
        -Fi IFILE, specify output file; default is Intensities.txt
        -Fd DFILE, specify output file; default is Directions.txt
        -Fs AFILE, specify output file; default is SiteNfo.txt 
        -tex,  output in LaTeX format
    """
    dir_path='.'
    res_file='pmag_results.txt'
    age_file=""
    latex=0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        res_file=sys.argv[ind+1]
    if '-fa' in sys.argv:
        ind = sys.argv.index('-fa')
        age_file=sys.argv[ind+1]
    if '-Fi' in sys.argv:
        ind = sys.argv.index('-Fi')
        Ioutfile=sys.argv[ind+1]
    if '-Fd' in sys.argv:
        ind = sys.argv.index('-Fd')
        outfile=sys.argv[ind+1]
    if '-Fs' in sys.argv:
        ind = sys.argv.index('-Fs')
        Soutfile=sys.argv[ind+1]
    if '-tex' in sys.argv: 
        latex=1
        outfile='Directions.tex'
        Ioutfile='Intensities.tex'
        Soutfile='SiteNfo.tex'
    else:
        latex=0
        outfile='Directions.txt'
        Ioutfile='Intensities.txt'
        Soutfile='SiteNfo.txt'
    # read in pmag_results file
    res_file=dir_path+'/'+res_file
    outfile=dir_path+'/'+outfile
    Ioutfile=dir_path+'/'+Ioutfile
    Soutfile=dir_path+'/'+Soutfile
    f=open(outfile,'w')
    sf=open(Soutfile,'w')
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
    for site in Sites:
        if site["pmag_result_name"][0:3]=="VGP":
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
    f1=open(Ioutfile,'w')
    if latex==0:
        outstring='%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'%("Site","Samples","N_B","B (uT)","s_b","s_b\%","VADM","s_vadm")
        f1.write(outstring)
    else:
        f1.write('\\begin{table}\n')
        f1.write('\\begin{tabular}{rrrrrrr}\n')
        f1.write('\hline\n')
        outstring='%s & %s & %s & %s & %s & %s & %s & %s%s\n'%("Site","Samples","N_B","B (uT)","s_b","s_b\%","VADM","s_vadm","\\\\")
        f1.write(outstring)
    for site in Sites:
        if site["pmag_result_name"][0:6]=="V[A]DM":
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
    if latex==1:
        f.write('\hline\n')
        sf.write('\hline\n')
        f1.write('\hline\n')
        f.write('\end{tabular}\n')
        sf.write('\end{tabular}\n')
        f.write('\end{table}\n')
        f1.write('\end{table}\n')
    f.close()
    sf.close()
    f1.close()
    print 'data saved in: ',outfile,Ioutfile,Soutfile
main()

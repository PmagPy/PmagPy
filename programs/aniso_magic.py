#!/usr/bin/env python
#  -*- python-indent-offset: 4; -*-
#pylint: disable=invalid-name,wrong-import-position,line-too-long
#import draw
from __future__ import print_function
from builtins import input
from builtins import range
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.new_builder as nb


def save(ANIS,fmt,title):
    files = {}
    for key in list(ANIS.keys()):
        if pmagplotlib.isServer:
            files[key] = title + '_TY:_aniso-' + key + '_.' + fmt
        else:
            files[key] = title.replace('__', '_') + "_aniso-" + key + "." + fmt
    pmagplotlib.saveP(ANIS, files)


def main():
    """
    NAME
        aniso_magic.py

    DESCRIPTION
        plots anisotropy data with either bootstrap or hext ellipses

    SYNTAX
        aniso_magic.py [-h] [command line options]
    OPTIONS
        -h plots help message and quits
        -usr USER: set the user name
        -f AFILE, specify specimens.txt formatted file for input
        -fsa SAMPFILE, specify samples.txt file (required to plot by site)
        -fsi SITEFILE, specify site file (required to include location information)
        -x Hext [1963] and bootstrap
        -B DON'T do bootstrap, do Hext
        -par Tauxe [1998] parametric bootstrap
        -v plot bootstrap eigenvectors instead of ellipses
        -sit plot by site instead of entire file
        -crd [s,g,t] coordinate system, default is specimen (g=geographic, t=tilt corrected)
        -P don't make any plots - just fill in the specimens, samples, sites tables
        -sav don't make the tables - just save all the plots
        -fmt [svg, jpg, eps] format for output images, pdf default
        -gtc DEC INC  dec,inc of pole to great circle [down(up) in green (cyan)
        -d Vi DEC INC; Vi (1,2,3) to compare to direction DEC INC
        -nb N; specifies the number of bootstraps - default is 1000
    DEFAULTS
       AFILE:  specimens.txt
       plot bootstrap ellipses of Constable & Tauxe [1987]
    NOTES
       minor axis: circles
       major axis: triangles
       principal axis: squares
       directions are plotted on the lower hemisphere
       for bootstrapped eigenvector components: Xs: blue, Ys: red, Zs: black
"""
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    #version_num = pmag.get_version()
    verbose = pmagplotlib.verbose
    dir_path = pmag.get_named_arg_from_sys("-WD", ".")
    num_bootstraps = pmag.get_named_arg_from_sys("-nb", 1000)
    #user = pmag.get_named_arg_from_sys("-usr", "")
    ipar = pmag.get_flag_arg_from_sys("-par", true=1, false=0)
    ihext = pmag.get_flag_arg_from_sys("-x", true=1, false=0)
    ivec = pmag.get_flag_arg_from_sys("-v", true=1, false=0)
    iplot = pmag.get_flag_arg_from_sys("-P", true=0, false=1)
    isite = pmag.get_flag_arg_from_sys("-sit", true=1, false=0)
    iboot, vec = 1, 0
    infile = pmag.get_named_arg_from_sys('-f', 'specimens.txt')
    samp_file = pmag.get_named_arg_from_sys('-fsa', 'samples.txt')
    site_file = pmag.get_named_arg_from_sys('-fsi', 'sites.txt')
    #outfile = pmag.get_named_arg_from_sys("-F", "rmag_results.txt")
    fmt = pmag.get_named_arg_from_sys("-fmt", "pdf")
    hpars, bpars = [], []
    CS, crd = -1, 's'
    ResRecs = []
    comp, Dir, PDir = 0, [], []
    if '-B' in args:
        iboot, ihext = 0, 1
    if '-crd' in sys.argv:
        ind = sys.argv.index('-crd')
        crd = sys.argv[ind+1]
        if crd == 'g':
            CS = 0
        if crd == 't':
            CS = 100
    if '-sav' in args:
        plots = 1
        verbose = 0
    else:
        plots = 0
    if '-gtc' in args:
        ind = args.index('-gtc')
        d, i = float(args[ind+1]), float(args[ind+2])
        PDir.append(d)
        PDir.append(i)
    if '-d' in args:
        comp = 1
        ind = args.index('-d')
        vec = int(args[ind+1])-1
        Dir = [float(args[ind+2]), float(args[ind+3])]

    #
    # set up plots
    #
    ANIS = {}
    initcdf, inittcdf = 0, 0
    ANIS['data'], ANIS['conf'] = 1, 2
    if iboot == 1:
        ANIS['tcdf'] = 3
        if iplot == 1:
            inittcdf = 1
            pmagplotlib.plot_init(ANIS['tcdf'], 5, 5)
        if comp == 1 and iplot == 1:
            initcdf = 1
            ANIS['vxcdf'], ANIS['vycdf'], ANIS['vzcdf'] = 4, 5, 6
            pmagplotlib.plot_init(ANIS['vxcdf'], 5, 5)
            pmagplotlib.plot_init(ANIS['vycdf'], 5, 5)
            pmagplotlib.plot_init(ANIS['vzcdf'], 5, 5)
    if iplot == 1:
        pmagplotlib.plot_init(ANIS['conf'], 5, 5)
        pmagplotlib.plot_init(ANIS['data'], 5, 5)
    # read in the data
    fnames = {'specimens': infile, 'samples': samp_file, 'sites': site_file}
    con = nb.Contribution(dir_path, read_tables=['specimens', 'samples', 'sites'],
                          custom_filenames=fnames)
    con.propagate_location_to_specimens()
    spec_container = con.tables['specimens']
    # get only anisotropy records
    spec_df = spec_container.get_records_for_code('AE-', strict_match=False)
    if 'aniso_tilt_correction' not in spec_df.columns:
        spec_df['aniso_tilt_correction'] = None
    orlist = spec_df['aniso_tilt_correction'].dropna().unique()
    if CS not in orlist:
        if len(orlist) > 0:
            CS = orlist[0]
        else:
            CS = -1
        if CS == -1:
            crd = 's'
        if CS == 0:
            crd = 'g'
        if CS == 100:
            crd = 't'
        if verbose:
            print("desired coordinate system not available, using available: ", crd)
    if isite == 1:
        sitelist = spec_df['site'].unique()
        sitelist.sort()
        plt = len(sitelist)
    else:
        plt = 1
    k = 0
    while k < plt:
        site = ""
        loc_name = ""
        sdata, Ss = [], [] # list of S format data
        if isite == 0:
            sdata = spec_df
            if 'location' in sdata.columns:
                loc_name = ':'.join(sdata['location'].unique())
        else:
            site = sitelist[k]
            sdata = spec_df[spec_df['site'] == site]
            if 'location' in sdata.columns:
                loc_name = sdata['location'][0]
        csrecs = sdata[sdata['aniso_tilt_correction'] == CS]
        #anitypes = csrecs['aniso_type'].unique()
        for name in ['citations', 'location', 'site', 'sample']:
            if name not in csrecs:
                csrecs[name] = ""
        Locs = csrecs['location'].unique()
        #Sites = csrecs['site'].unique()
        #Samples = csrecs['sample'].unique()
        #Specimens = csrecs['specimen'].unique()
        #Cits = csrecs['citations'].unique()
        for ind, rec in csrecs.iterrows():
            s = [float(i.strip()) for i in rec['aniso_s'].split(':')]
            if s[0] <= 1.0:
                Ss.append(s) # protect against crap
            # tau,Vdirs=pmag.doseigs(s)
            # do we need fpars somewhere???
            # fpars = pmag.dohext(int(rec["aniso_s_n_measurements"]) -6, float(rec["aniso_s_sigma"]), s)
            # fill in ResRecs (ignoring this for now, grab it from aniso_magic if needed)
        if len(Ss) > 1:
            if pmagplotlib.isServer: # use server plot naming convention
                title = "LO:_" + loc_name + '_SI:_' + site + '_SA:__SP:__CO:_' + crd
            else: # use more readable plot naming convention
                title = "{}_{}_{}".format(loc_name, site, crd)
            bpars, hpars = pmagplotlib.plotANIS(ANIS, Ss, iboot, ihext, ivec, ipar,
                                                title, iplot, comp, vec, Dir, num_bootstraps)
            if len(PDir) > 0:
                pmagplotlib.plotC(ANIS['data'], PDir, 90., 'g')
                pmagplotlib.plotC(ANIS['conf'], PDir, 90., 'g')
            if verbose and plots == 0:
                pmagplotlib.drawFIGS(ANIS)
            if plots == 1:
                save(ANIS,fmt,title)

            if hpars != [] and ihext == 1:
                HextRec = {}
                #for key in ResRec.keys():HextRec[key]=ResRec[key]   # copy over stuff
                HextRec["anisotropy_v1_dec"] = '%7.1f'%(hpars["v1_dec"])
                HextRec["anisotropy_v2_dec"] = '%7.1f'%(hpars["v2_dec"])
                HextRec["anisotropy_v3_dec"] = '%7.1f'%(hpars["v3_dec"])
                HextRec["anisotropy_v1_inc"] = '%7.1f'%(hpars["v1_inc"])
                HextRec["anisotropy_v2_inc"] = '%7.1f'%(hpars["v2_inc"])
                HextRec["anisotropy_v3_inc"] = '%7.1f'%(hpars["v3_inc"])
                HextRec["anisotropy_t1"] = '%10.8f'%(hpars["t1"])
                HextRec["anisotropy_t2"] = '%10.8f'%(hpars["t2"])
                HextRec["anisotropy_t3"] = '%10.8f'%(hpars["t3"])
                HextRec["anisotropy_hext_F"] = '%7.1f '%(hpars["F"])
                HextRec["anisotropy_hext_F12"] = '%7.1f '%(hpars["F12"])
                HextRec["anisotropy_hext_F23"] = '%7.1f '%(hpars["F23"])
                HextRec["anisotropy_v1_eta_semi_angle"] = '%7.1f '%(hpars["e12"])
                HextRec["anisotropy_v1_eta_dec"] = '%7.1f '%(hpars["v2_dec"])
                HextRec["anisotropy_v1_eta_inc"] = '%7.1f '%(hpars["v2_inc"])
                HextRec["anisotropy_v1_zeta_semi_angle"] = '%7.1f '%(hpars["e13"])
                HextRec["anisotropy_v1_zeta_dec"] = '%7.1f '%(hpars["v3_dec"])
                HextRec["anisotropy_v1_zeta_inc"] = '%7.1f '%(hpars["v3_inc"])
                HextRec["anisotropy_v2_eta_semi_angle"] = '%7.1f '%(hpars["e12"])
                HextRec["anisotropy_v2_eta_dec"] = '%7.1f '%(hpars["v1_dec"])
                HextRec["anisotropy_v2_eta_inc"] = '%7.1f '%(hpars["v1_inc"])
                HextRec["anisotropy_v2_zeta_semi_angle"] = '%7.1f '%(hpars["e23"])
                HextRec["anisotropy_v2_zeta_dec"] = '%7.1f '%(hpars["v3_dec"])
                HextRec["anisotropy_v2_zeta_inc"] = '%7.1f '%(hpars["v3_inc"])
                HextRec["anisotropy_v3_eta_semi_angle"] = '%7.1f '%(hpars["e12"])
                HextRec["anisotropy_v3_eta_dec"] = '%7.1f '%(hpars["v1_dec"])
                HextRec["anisotropy_v3_eta_inc"] = '%7.1f '%(hpars["v1_inc"])
                HextRec["anisotropy_v3_zeta_semi_angle"] = '%7.1f '%(hpars["e23"])
                HextRec["anisotropy_v3_zeta_dec"] = '%7.1f '%(hpars["v2_dec"])
                HextRec["anisotropy_v3_zeta_inc"] = '%7.1f '%(hpars["v2_inc"])
                HextRec["magic_method_codes"] = 'LP-AN:AE-H'
                if verbose:
                    print("Hext Statistics: ")
                    print(" tau_i, V_i_D, V_i_I, V_i_zeta, V_i_zeta_D, V_i_zeta_I, V_i_eta, V_i_eta_D, V_i_eta_I")
                    print(HextRec["anisotropy_t1"], HextRec["anisotropy_v1_dec"], end=' ')
                    print(HextRec["anisotropy_v1_inc"], HextRec["anisotropy_v1_eta_semi_angle"], end=' ')
                    print(HextRec["anisotropy_v1_eta_dec"], HextRec["anisotropy_v1_eta_inc"], end=' ')
                    print(HextRec["anisotropy_v1_zeta_semi_angle"], HextRec["anisotropy_v1_zeta_dec"], end=' ')
                    print(HextRec["anisotropy_v1_zeta_inc"])
                    #
                    print(HextRec["anisotropy_t2"],HextRec["anisotropy_v2_dec"], end=' ')
                    print(HextRec["anisotropy_v2_inc"], HextRec["anisotropy_v2_eta_semi_angle"], end=' ')
                    print(HextRec["anisotropy_v2_eta_dec"], HextRec["anisotropy_v2_eta_inc"], end=' ')
                    print(HextRec["anisotropy_v2_zeta_semi_angle"], HextRec["anisotropy_v2_zeta_dec"], end=' ')
                    print(HextRec["anisotropy_v2_zeta_inc"])
                    #
                    print(HextRec["anisotropy_t3"], HextRec["anisotropy_v3_dec"], end=' ')
                    print(HextRec["anisotropy_v3_inc"], HextRec["anisotropy_v3_eta_semi_angle"], end=' ')
                    print(HextRec["anisotropy_v3_eta_dec"], HextRec["anisotropy_v3_eta_inc"], end=' ')
                    print(HextRec["anisotropy_v3_zeta_semi_angle"], HextRec["anisotropy_v3_zeta_dec"], end=' ')
                    print(HextRec["anisotropy_v3_zeta_inc"])
                #HextRec['magic_software_packages']=version_num
                #ResRecs.append(HextRec)
            if bpars != []:
                BootRec = {}
                #for key in ResRec.keys():BootRec[key]=ResRec[key]   # copy over stuff
                BootRec["anisotropy_v1_dec"] = '%7.1f'%(bpars["v1_dec"])
                BootRec["anisotropy_v2_dec"] = '%7.1f'%(bpars["v2_dec"])
                BootRec["anisotropy_v3_dec"] = '%7.1f'%(bpars["v3_dec"])
                BootRec["anisotropy_v1_inc"] = '%7.1f'%(bpars["v1_inc"])
                BootRec["anisotropy_v2_inc"] = '%7.1f'%(bpars["v2_inc"])
                BootRec["anisotropy_v3_inc"] = '%7.1f'%(bpars["v3_inc"])
                BootRec["anisotropy_t1"] = '%10.8f'%(bpars["t1"])
                BootRec["anisotropy_t2"] = '%10.8f'%(bpars["t2"])
                BootRec["anisotropy_t3"] = '%10.8f'%(bpars["t3"])
                BootRec["anisotropy_v1_eta_inc"] = '%7.1f '%(bpars["v1_eta_inc"])
                BootRec["anisotropy_v1_eta_dec"] = '%7.1f '%(bpars["v1_eta_dec"])
                BootRec["anisotropy_v1_eta_semi_angle"] = '%7.1f '%(bpars["v1_eta"])
                BootRec["anisotropy_v1_zeta_inc"] = '%7.1f '%(bpars["v1_zeta_inc"])
                BootRec["anisotropy_v1_zeta_dec"] = '%7.1f '%(bpars["v1_zeta_dec"])
                BootRec["anisotropy_v1_zeta_semi_angle"] = '%7.1f '%(bpars["v1_zeta"])
                BootRec["anisotropy_v2_eta_inc"] = '%7.1f '%(bpars["v2_eta_inc"])
                BootRec["anisotropy_v2_eta_dec"] = '%7.1f '%(bpars["v2_eta_dec"])
                BootRec["anisotropy_v2_eta_semi_angle"] = '%7.1f '%(bpars["v2_eta"])
                BootRec["anisotropy_v2_zeta_inc"] = '%7.1f '%(bpars["v2_zeta_inc"])
                BootRec["anisotropy_v2_zeta_dec"] = '%7.1f '%(bpars["v2_zeta_dec"])
                BootRec["anisotropy_v2_zeta_semi_angle"] = '%7.1f '%(bpars["v2_zeta"])
                BootRec["anisotropy_v3_eta_inc"] = '%7.1f '%(bpars["v3_eta_inc"])
                BootRec["anisotropy_v3_eta_dec"] = '%7.1f '%(bpars["v3_eta_dec"])
                BootRec["anisotropy_v3_eta_semi_angle"] = '%7.1f '%(bpars["v3_eta"])
                BootRec["anisotropy_v3_zeta_inc"] = '%7.1f '%(bpars["v3_zeta_inc"])
                BootRec["anisotropy_v3_zeta_dec"] = '%7.1f '%(bpars["v3_zeta_dec"])
                BootRec["anisotropy_v3_zeta_semi_angle"] = '%7.1f '%(bpars["v3_zeta"])
                BootRec["anisotropy_hext_F"] = ''
                BootRec["anisotropy_hext_F12"] = ''
                BootRec["anisotropy_hext_F23"] = ''
                BootRec["magic_method_codes"] = 'LP-AN:AE-H:AE-BS' # regular bootstrap
                if ipar == 1:
                    BootRec["magic_method_codes"] = 'LP-AN:AE-H:AE-BS-P' # parametric bootstrap
                if verbose:
                    print("Boostrap Statistics: ")
                    print(" tau_i, V_i_D, V_i_I, V_i_zeta, V_i_zeta_D, V_i_zeta_I, V_i_eta, V_i_eta_D, V_i_eta_I")
                    print(BootRec["anisotropy_t1"], BootRec["anisotropy_v1_dec"], end=' ')
                    print(BootRec["anisotropy_v1_inc"], BootRec["anisotropy_v1_eta_semi_angle"], end=' ')
                    print(BootRec["anisotropy_v1_eta_dec"], BootRec["anisotropy_v1_eta_inc"], end=' ')
                    print(BootRec["anisotropy_v1_zeta_semi_angle"], BootRec["anisotropy_v1_zeta_dec"], end=' ')
                    print(BootRec["anisotropy_v1_zeta_inc"])
                    #
                    print(BootRec["anisotropy_t2"], BootRec["anisotropy_v2_dec"], BootRec["anisotropy_v2_inc"], end=' ')
                    print(BootRec["anisotropy_v2_eta_semi_angle"], BootRec["anisotropy_v2_eta_dec"], end=' ')
                    print(BootRec["anisotropy_v2_eta_inc"], BootRec["anisotropy_v2_zeta_semi_angle"], end=' ')
                    print(BootRec["anisotropy_v2_zeta_dec"], BootRec["anisotropy_v2_zeta_inc"])
                    #
                    print(BootRec["anisotropy_t3"], BootRec["anisotropy_v3_dec"], BootRec["anisotropy_v3_inc"], end=' ')
                    print(BootRec["anisotropy_v3_eta_semi_angle"], BootRec["anisotropy_v3_eta_dec"], end=' ')
                    print(BootRec["anisotropy_v3_eta_inc"], BootRec["anisotropy_v3_zeta_semi_angle"], end=' ')
                    print(BootRec["anisotropy_v3_zeta_dec"], BootRec["anisotropy_v3_zeta_inc"])
                #BootRec['magic_software_packages'] = version_num
                ResRecs.append(BootRec)
            k += 1
            goon = 1
            while goon == 1 and iplot == 1 and verbose:
                if iboot == 1:
                    print("compare with [d]irection ")
                print(" plot [g]reat circle,  change [c]oord. system, change [e]llipse calculation,  s[a]ve plots, [q]uit ")
                if isite == 1:
                    print("  [p]revious, [s]ite, [q]uit, <return> for next ")
                ans = input("")
                if ans == "q":
                    sys.exit()
                if ans == "e":
                    iboot, ipar, ihext, ivec = 1, 0, 0, 0
                    e = input("Do Hext Statistics  1/[0]: ")
                    if e == "1":
                        ihext = 1
                    e = input("Suppress bootstrap 1/[0]: ")
                    if e == "1":
                        iboot = 0
                    if iboot == 1:
                        e = input("Parametric bootstrap 1/[0]: ")
                        if e == "1":
                            ipar = 1
                        e = input("Plot bootstrap eigenvectors:  1/[0]: ")
                        if e == "1":
                            ivec=1
                        if iplot == 1:
                            if inittcdf == 0:
                                ANIS['tcdf'] = 3
                                pmagplotlib.plot_init(ANIS['tcdf'], 5, 5)
                                inittcdf = 1
                    bpars, hpars = pmagplotlib.plotANIS(ANIS, Ss, iboot, ihext, ivec, ipar, title, iplot,
                                                        comp, vec, Dir, num_bootstraps)
                    if verbose and plots == 0:
                        pmagplotlib.drawFIGS(ANIS)
                if ans == "c":
                    print("Current Coordinate system is: ")
                    if CS == -1:
                        print(" Specimen")
                    if CS == 0:
                        print(" Geographic")
                    if CS == 100:
                        print(" Tilt corrected")
                    key = input(" Enter desired coordinate system: [s]pecimen, [g]eographic, [t]ilt corrected ")
                    if key == 's':
                        CS = -1
                    if key == 'g':
                        CS = 0
                    if key == 't':
                        CS = 100
                    if CS not in orlist:
                        if len(orlist) > 0:
                            CS = orlist[0]
                        else:
                            CS = -1
                        if CS == -1:
                            crd = 's'
                        if CS == 0:
                            crd = 'g'
                        if CS == 100:
                            crd = 't'
                        print("desired coordinate system not available, using available: ", crd)
                    k -= 1
                    goon = 0
                if ans == "":
                    if isite == 1:
                        goon = 0
                    else:
                        print("Good bye ")
                        sys.exit()
                if ans == 'd':
                    if initcdf == 0:
                        initcdf = 1
                        ANIS['vxcdf'], ANIS['vycdf'], ANIS['vzcdf'] = 4, 5, 6
                        pmagplotlib.plot_init(ANIS['vxcdf'], 5, 5)
                        pmagplotlib.plot_init(ANIS['vycdf'], 5, 5)
                        pmagplotlib.plot_init(ANIS['vzcdf'], 5, 5)
                    Dir, comp = [], 1
                    print("""
                      Input: Vi D I to  compare  eigenvector Vi with direction D/I
                             where Vi=1: principal
                                   Vi=2: major
                                   Vi=3: minor
                                   D= declination of comparison direction
                                   I= inclination of comparison direction""")
                    con = 1
                    while con == 1:
                        try:
                            vdi = input("Vi D I: ").split()
                            vec = int(vdi[0])-1
                            Dir = [float(vdi[1]), float(vdi[2])]
                            con = 0
                        except IndexError:
                            print(" Incorrect entry, try again ")
                    bpars, hpars = pmagplotlib.plotANIS(ANIS, Ss, iboot, ihext, ivec, ipar, title,
                                                        iplot, comp, vec, Dir, num_bootstraps)
                    Dir, comp = [], 0
                if ans == 'g':
                    con, cnt = 1, 0
                    while con == 1:
                        try:
                            print(" Input:  input pole to great circle ( D I) to  plot a great circle:   ")
                            di = input(" D I: ").split()
                            PDir.append(float(di[0]))
                            PDir.append(float(di[1]))
                            con=0
                        except:
                            cnt += 1
                            if cnt < 10:
                                print(" enter the dec and inc of the pole on one line ")
                            else:
                                print("ummm - you are doing something wrong - i give up")
                                sys.exit()
                    pmagplotlib.plotC(ANIS['data'], PDir, 90., 'g')
                    pmagplotlib.plotC(ANIS['conf'], PDir, 90., 'g')
                    if verbose and plots == 0:
                        pmagplotlib.drawFIGS(ANIS)
                if ans == "p":
                    k -= 2
                    goon = 0
                if ans == "q":
                    k = plt
                    goon = 0
                if ans == "s":
                    keepon = 1
                    site = input(" print site or part of site desired: ")
                    while keepon == 1:
                        try:
                            k = sitelist.index(site)
                            keepon = 0
                        except:
                            tmplist = []
                            for qq in range(len(sitelist)):
                                if site in sitelist[qq]:
                                    tmplist.append(sitelist[qq])
                            print(site, " not found, but this was: ")
                            print(tmplist)
                            site = input('Select one or try again\n ')
                            k = sitelist.index(site)
                    goon, ans = 0, ""
                if ans == "a":
                    locs = pmag.makelist(Locs)
                    site_name = "_"
                    if isite:
                        site_name = site
                    if pmagplotlib.isServer: # use server plot naming convention
                        title = "LO:_" + locs + '_SI:_' + site_name + '_SA:__SP:__CO:_' + crd
                    else: # use more readable plot naming convention
                        title = "{}_{}_{}".format(locs, site_name, crd)
                    save(ANIS, fmt, title)
                    goon = 0
        else:
            if verbose:
                print('skipping plot - not enough data points')
            k += 1
    #   put rmag_results stuff here
    #if len(ResRecs)>0:
    #    ResOut,keylist=pmag.fillkeys(ResRecs)
    #    pmag.magic_write(outfile,ResOut,'rmag_results')
    if verbose:
        print(" Good bye ")

if __name__ == "__main__":
    main()

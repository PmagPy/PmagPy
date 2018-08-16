#!/usr/bin/env python
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
from pmag_env import set_env
if not set_env.isServer:
    import pmagpy.nlt as nlt

# initialize some variables


def save_redo(SpecRecs, inspec):
    SpecRecs, keys = pmag.fillkeys(SpecRecs)
    pmag.magic_write(inspec, SpecRecs, 'pmag_specimens')


def main():
    """
    NAME
        thellier_magic.py

    DESCRIPTION
        plots Thellier-Thellier, allowing interactive setting of bounds
        and customizing of selection criteria.  Saves and reads interpretations
        from a pmag_specimen formatted table, default: thellier_specimens.txt

    SYNTAX
        thellier_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f MEAS, set magic_measurements input file
        -fsp PRIOR, set pmag_specimen prior interpretations file
        -fan ANIS, set rmag_anisotropy file for doing the anisotropy corrections
        -fcr CRIT, set criteria file for grading.
        -fmt [svg,png,jpg], format for images - default is svg
        -sav,  saves plots with out review (default format)
        -spc SPEC, plots single specimen SPEC, saves plot with specified format
            with optional -b bounds adn quits
        -b BEG END: sets  bounds for calculation
           BEG: starting step for slope calculation
           END: ending step for slope calculation
        -z use only z component difference for pTRM calculation

    DEFAULTS
        MEAS: magic_measurements.txt
        REDO: thellier_redo
        CRIT: NONE
        PRIOR: NONE

    OUTPUT
        figures:
            ALL:  numbers refer to temperature steps in command line window
            1) Arai plot:  closed circles are zero-field first/infield
                           open circles are infield first/zero-field
                           triangles are pTRM checks
                           squares are pTRM tail checks
                           VDS is vector difference sum
                           diamonds are bounds for interpretation
            2) Zijderveld plot:  closed (open) symbols are X-Y (X-Z) planes
                                 X rotated to NRM direction
            3) (De/Re)Magnetization diagram:
                           circles are NRM remaining
                           squares are pTRM gained
            4) equal area projections:
               green triangles are pTRM gained direction
                           red (purple) circles are lower(upper) hemisphere of ZI step directions
                           blue (cyan) squares are lower(upper) hemisphere IZ step directions
            5) Optional:  TRM acquisition
            6) Optional: TDS normalization
        command line window:
            list is: temperature step numbers, temperatures (C), Dec, Inc, Int (units of magic_measuements)
                     list of possible commands: type letter followed by return to select option
                     saving of plots creates .svg format files with specimen_name, plot type as name
    """
#
#   initializations
#
    meas_file, critout, inspec = "magic_measurements.txt", "", "thellier_specimens.txt"
    first = 1
    inlt = 0
    version_num = pmag.get_version()
    TDinit, Tinit, field, first_save = 0, 0, -1, 1
    user, comment, AniSpec, locname = "", '', "", ""
    ans, specimen, recnum, start, end = 0, 0, 0, 0, 0
    plots, pmag_out, samp_file, style = 0, "", "", "svg"
    verbose = pmagplotlib.verbose
    fmt = '.'+style
#
# default acceptance criteria
#
    accept = pmag.default_criteria(0)[0]  # set the default criteria
#
# parse command line options
#
    Zdiff, anis = 0, 0
    spc, BEG, END = "", "", ""
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        meas_file = sys.argv[ind+1]
    if '-fsp' in sys.argv:
        ind = sys.argv.index('-fsp')
        inspec = sys.argv[ind+1]
    if '-fan' in sys.argv:
        ind = sys.argv.index('-fan')
        anisfile = sys.argv[ind+1]
        anis = 1
        anis_data, file_type = pmag.magic_read(anisfile)
        if verbose:
            print("Anisotropy data read in from ", anisfile)
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = '.'+sys.argv[ind+1]
    if '-dpi' in sys.argv:
        ind = sys.argv.index('-dpi')
        dpi = '.'+sys.argv[ind+1]
    else:
        dpi = 100
    if '-sav' in sys.argv:
        plots = 1
        verbose = 0
    if '-z' in sys.argv:
        Zdiff = 1
    if '-spc' in sys.argv:
        ind = sys.argv.index('-spc')
        spc = sys.argv[ind+1]
        if '-b' in sys.argv:
            ind = sys.argv.index('-b')
            BEG = int(sys.argv[ind+1])
            END = int(sys.argv[ind+2])
    if '-fcr' in sys.argv:
        ind = sys.argv.index('-fcr')
        critout = sys.argv[ind+1]
        crit_data, file_type = pmag.magic_read(critout)
        if file_type != 'pmag_criteria':
            if verbose:
                print('bad pmag_criteria file, using no acceptance criteria')
            accept = pmag.default_criteria(1)[0]
        else:
            if verbose:
                print("Acceptance criteria read in from ", critout)
            accept = {'pmag_criteria_code': 'ACCEPTANCE',
                      'er_citation_names': 'This study'}
            for critrec in crit_data:
                if 'sample_int_sigma_uT' in critrec.keys():  # accommodate Shaar's new criterion
                    critrec['sample_int_sigma'] = '%10.3e' % (
                        eval(critrec['sample_int_sigma_uT'])*1e-6)
                for key in critrec.keys():
                    if key not in accept.keys() and critrec[key] != '':
                        accept[key] = critrec[key]
    try:
        open(inspec, 'rU')
        PriorRecs, file_type = pmag.magic_read(inspec)
        if file_type != 'pmag_specimens':
            print(file_type)
            print(file_type, inspec, " is not a valid pmag_specimens file ")
            sys.exit()
        for rec in PriorRecs:
            if 'magic_software_packages' not in rec.keys():
                rec['magic_software_packages'] = ""
    except IOError:
        PriorRecs = []
        if verbose:
            print("starting new specimen interpretation file: ", inspec)
    meas_data, file_type = pmag.magic_read(meas_file)
    if file_type != 'magic_measurements':
        print(file_type)
        print(file_type, "This is not a valid magic_measurements file ")
        sys.exit()
    backup = 0
    # define figure numbers for arai, zijderveld and
    #   de-,re-magization diagrams
    AZD = {}
    AZD['deremag'], AZD['zijd'], AZD['arai'], AZD['eqarea'] = 1, 2, 3, 4
    pmagplotlib.plot_init(AZD['arai'], 5, 5)
    pmagplotlib.plot_init(AZD['zijd'], 5, 5)
    pmagplotlib.plot_init(AZD['deremag'], 5, 5)
    pmagplotlib.plot_init(AZD['eqarea'], 5, 5)
    #
    #
    #
    # get list of unique specimen names
    #
    CurrRec = []
    sids = pmag.get_specs(meas_data)
    # get plots for specimen s - default is just to step through arai diagrams
    #
    if spc != "":
        specimen = sids.index(spc)
    while specimen < len(sids):
        methcodes = []

        if verbose:
            print(sids[specimen], specimen+1, 'of ', len(sids))
        MeasRecs = []
        s = sids[specimen]
        datablock, trmblock, tdsrecs = [], [], []
        PmagSpecRec = {}
        if first == 0:
            for key in keys:
                # make sure all new records have same set of keys
                PmagSpecRec[key] = ""
        PmagSpecRec["er_analyst_mail_names"] = user
        PmagSpecRec["specimen_correction"] = 'u'
    #
    # find the data from the meas_data file for this specimen
    #
        for rec in meas_data:
            if rec["er_specimen_name"] == s:
                MeasRecs.append(rec)
                if "magic_method_codes" not in rec.keys():
                    rec["magic_method_codes"] = ""
                methods = rec["magic_method_codes"].split(":")
                meths = []
                for meth in methods:
                    meths.append(meth.strip())  # take off annoying spaces
                methods = ""
                for meth in meths:
                    if meth.strip() not in methcodes and "LP-" in meth:
                        methcodes.append(meth.strip())
                    methods = methods+meth+":"
                methods = methods[:-1]
                rec["magic_method_codes"] = methods
                if "LP-PI-TRM" in meths:
                    datablock.append(rec)
                if "LP-TRM" in meths:
                    trmblock.append(rec)
                if "LP-TRM-TD" in meths:
                    tdsrecs.append(rec)
        if len(trmblock) > 2 and inspec != "":
            if Tinit == 0:
                Tinit = 1
                AZD['TRM'] = 5
                pmagplotlib.plot_init(AZD['TRM'], 5, 5)
        elif Tinit == 1:  # clear the TRM figure if not needed
            pmagplotlib.clearFIG(AZD['TRM'])
        if len(tdsrecs) > 2:
            if TDinit == 0:
                TDinit = 1
                AZD['TDS'] = 6
                pmagplotlib.plot_init(AZD['TDS'], 5, 5)
        elif TDinit == 1:  # clear the TDS figure if not needed
            pmagplotlib.clearFIG(AZD['TDS'])
        if len(datablock) < 4:
            if backup == 0:
                specimen += 1
                if verbose:
                    print('skipping specimen - moving forward ', s)
            else:
                specimen -= 1
                if verbose:
                    print('skipping specimen - moving backward ', s)
    #
    #  collect info for the PmagSpecRec dictionary
    #
        else:
            rec = datablock[0]
            PmagSpecRec["er_citation_names"] = "This study"
            PmagSpecRec["er_specimen_name"] = s
            PmagSpecRec["er_sample_name"] = rec["er_sample_name"]
            PmagSpecRec["er_site_name"] = rec["er_site_name"]
            PmagSpecRec["er_location_name"] = rec["er_location_name"]
            locname = rec['er_location_name'].replace('/', '-')
            if "er_expedition_name" in rec.keys():
                PmagSpecRec["er_expedition_name"] = rec["er_expedition_name"]
            if "magic_instrument_codes" not in rec.keys():
                rec["magic_instrument_codes"] = ""
            PmagSpecRec["magic_instrument_codes"] = rec["magic_instrument_codes"]
            PmagSpecRec["measurement_step_unit"] = "K"
            if "magic_experiment_name" not in rec.keys():
                rec["magic_experiment_name"] = ""
            else:
                PmagSpecRec["magic_experiment_names"] = rec["magic_experiment_name"]

            meths = rec["magic_method_codes"].split()
        # sort data into types
            araiblock, field = pmag.sortarai(datablock, s, Zdiff)
            first_Z = araiblock[0]
            GammaChecks = araiblock[5]
            if len(first_Z) < 3:
                if backup == 0:
                    specimen += 1
                    if verbose:
                        print('skipping specimen - moving forward ', s)
                else:
                    specimen -= 1
                    if verbose:
                        print('skipping specimen - moving backward ', s)
            else:
                backup = 0
                zijdblock, units = pmag.find_dmag_rec(s, meas_data)
                recnum = 0
                if verbose:
                    print("index step Dec   Inc  Int       Gamma")
                    for plotrec in zijdblock:
                        if GammaChecks != "":
                            gamma = ""
                            for g in GammaChecks:
                                if g[0] == plotrec[0]-273:
                                    gamma = g[1]
                                    break
                        if gamma != "":
                            print('%i     %i %7.1f %7.1f %8.3e %7.1f' % (
                                recnum, plotrec[0]-273, plotrec[1], plotrec[2], plotrec[3], gamma))
                        else:
                            print('%i     %i %7.1f %7.1f %8.3e ' % (
                                recnum, plotrec[0]-273, plotrec[1], plotrec[2], plotrec[3]))
                        recnum += 1
                pmagplotlib.plot_arai_zij(AZD, araiblock, zijdblock, s, units[0])
                if verbose:
                    pmagplotlib.draw_figs(AZD)
                if len(tdsrecs) > 2:  # a TDS experiment
                    tdsblock = []  # make a list for the TDS  data
                    Mkeys = ['measurement_magnitude', 'measurement_magn_moment',
                             'measurement_magn_volume', 'measuruement_magn_mass']
                    mkey, k = "", 0
                    # find which type of intensity
                    while mkey == "" and k < len(Mkeys)-1:
                        key = Mkeys[k]
                        if key in tdsrecs[0].keys() and tdsrecs[0][key] != "":
                            mkey = key
                        k += 1
                    if mkey == "":
                        break  # get outta here
                    Tnorm = ""
                    for tdrec in tdsrecs:
                        meths = tdrec['magic_method_codes'].split(":")
                        for meth in meths:
                            # strip off potential nasty spaces
                            meth.replace(" ", "")
                        if 'LT-T-I' in meths and Tnorm == "":  # found first total TRM
                            # normalize by total TRM
                            Tnorm = float(tdrec[mkey])
                            # put in the zero step
                            tdsblock.append([273, zijdblock[0][3]/Tnorm, 1.])
                        # found a LP-TRM-TD demag step, now need complementary LT-T-Z from zijdblock
                        if 'LT-T-Z' in meths and Tnorm != "":
                            step = float(tdrec['treatment_temp'])
                            Tint = ""
                            if mkey != "":
                                Tint = float(tdrec[mkey])
                            if Tint != "":
                                for zrec in zijdblock:
                                    if zrec[0] == step:  # found matching
                                        tdsblock.append(
                                            [step, zrec[3]/Tnorm, Tint/Tnorm])
                                        break
                    if len(tdsblock) > 2:
                        pmagplotlib.plot_tds(
                            AZD['TDS'], tdsblock, s+':LP-PI-TDS:')
                        if verbose:
                            pmagplotlib(draw_figs(AZD))
                    else:
                        print("Something wrong here")
                if anis == 1:   # look up anisotropy data for this specimen
                    AniSpec = ""
                    for aspec in anis_data:
                        if aspec["er_specimen_name"] == PmagSpecRec["er_specimen_name"]:
                            AniSpec = aspec
                            if verbose:
                                print('Found anisotropy record...')
                            break
                if inspec != "":
                    if verbose:
                        print('Looking up saved interpretation....')
                    found = 0
                    for k in range(len(PriorRecs)):
                        try:
                            if PriorRecs[k]["er_specimen_name"] == s:
                                found = 1
                                CurrRec.append(PriorRecs[k])
                                for j in range(len(zijdblock)):
                                    if float(zijdblock[j][0]) == float(PriorRecs[k]["measurement_step_min"]):
                                        start = j
                                    if float(zijdblock[j][0]) == float(PriorRecs[k]["measurement_step_max"]):
                                        end = j
                                pars, errcode = pmag.PintPars(
                                    datablock, araiblock, zijdblock, start, end, accept)
                                pars['measurement_step_unit'] = "K"
                                pars['experiment_type'] = 'LP-PI-TRM'
                                # put in CurrRec, take out of PriorRecs
                                del PriorRecs[k]
                                if errcode != 1:
                                    pars["specimen_lab_field_dc"] = field
                                    pars["specimen_int"] = -1 * \
                                        field*pars["specimen_b"]
                                    pars["er_specimen_name"] = s
                                    if verbose:
                                        print('Saved interpretation: ')
                                    pars, kill = pmag.scoreit(
                                        pars, PmagSpecRec, accept, '', verbose)
                                    pmagplotlib.plot_b(
                                        AZD, araiblock, zijdblock, pars)
                                    if verbose:
                                        pmagplotlib.draw_figs(AZD)
                                    if len(trmblock) > 2:
                                        blab = field
                                        best = pars["specimen_int"]
                                        Bs, TRMs = [], []
                                        for trec in trmblock:
                                            Bs.append(
                                                float(trec['treatment_dc_field']))
                                            TRMs.append(
                                                float(trec['measurement_magn_moment']))
                                        # calculate best fit parameters through TRM acquisition data, and get new banc
                                        NLpars = nlt.NLtrm(
                                            Bs, TRMs, best, blab, 0)
                                        Mp, Bp = [], []
                                        for k in range(int(max(Bs)*1e6)):
                                            Bp.append(float(k)*1e-6)
                                            # predicted NRM for this field
                                            npred = nlt.TRM(
                                                Bp[-1], NLpars['xopt'][0], NLpars['xopt'][1])
                                            Mp.append(npred)
                                        pmagplotlib.plot_trm(
                                            AZD['TRM'], Bs, TRMs, Bp, Mp, NLpars, trec['magic_experiment_name'])
                                        PmagSpecRec['specimen_int'] = NLpars['banc']
                                        if verbose:
                                            print('Banc= ', float(
                                                NLpars['banc'])*1e6)
                                            pmagplotlib.draw_figs(AZD)
                                    mpars = pmag.domean(
                                        araiblock[1], start, end, 'DE-BFL')
                                    if verbose:
                                        print('pTRM direction= ', '%7.1f' % (mpars['specimen_dec']), ' %7.1f' % (
                                            mpars['specimen_inc']), ' MAD:', '%7.1f' % (mpars['specimen_mad']))
                                    if AniSpec != "":
                                        CpTRM = pmag.Dir_anis_corr(
                                            [mpars['specimen_dec'], mpars['specimen_inc']], AniSpec)
                                        AniSpecRec = pmag.doaniscorr(
                                            PmagSpecRec, AniSpec)
                                        if verbose:
                                            print('Anisotropy corrected TRM direction= ', '%7.1f' % (
                                                CpTRM[0]), ' %7.1f' % (CpTRM[1]))
                                            print('Anisotropy corrected intensity= ', float(
                                                AniSpecRec['specimen_int'])*1e6)
                                else:
                                    print('error on specimen ', s)
                        except:
                            pass
                    if verbose and found == 0:
                        print('    None found :(  ')
                if spc != "":
                    if BEG != "":
                        pars, errcode = pmag.PintPars(
                            datablock, araiblock, zijdblock, BEG, END, accept)
                        pars['measurement_step_unit'] = "K"
                        pars["specimen_lab_field_dc"] = field
                        pars["specimen_int"] = -1*field*pars["specimen_b"]
                        pars["er_specimen_name"] = s
                        pars['specimen_grade'] = ''  # ungraded
                        pmagplotlib.plot_b(AZD, araiblock, zijdblock, pars)
                        if verbose:
                            pmagplotlib.draw_figs(AZD)
                        if len(trmblock) > 2:
                            if inlt == 0:
                                inlt = 1
                            blab = field
                            best = pars["specimen_int"]
                            Bs, TRMs = [], []
                            for trec in trmblock:
                                Bs.append(float(trec['treatment_dc_field']))
                                TRMs.append(
                                    float(trec['measurement_magn_moment']))
                            # calculate best fit parameters through TRM acquisition data, and get new banc
                            NLpars = nlt.NLtrm(Bs, TRMs, best, blab, 0)
    #
                            Mp, Bp = [], []
                            for k in range(int(max(Bs)*1e6)):
                                Bp.append(float(k)*1e-6)
                                # predicted NRM for this field
                                npred = nlt.TRM(
                                    Bp[-1], NLpars['xopt'][0], NLpars['xopt'][1])
                    files = {}
                    for key in AZD.keys():
                        files[key] = s+'_'+key+fmt
                    pmagplotlib.save_plots(AZD, files, dpi=dpi)
                    sys.exit()
                if verbose:
                    ans = 'b'
                    while ans != "":
                        print("""
               s[a]ve plot, set [b]ounds for calculation, [d]elete current interpretation, [p]revious, [s]ample, [q]uit:
               """)
                        ans = input('Return for next specimen \n')
                        if ans == "":
                            specimen += 1
                        if ans == "d":
                            save_redo(PriorRecs, inspec)
                            CurrRec = []
                            pmagplotlib.plot_arai_zij(
                                AZD, araiblock, zijdblock, s, units[0])
                            if verbose:
                                pmagplotlib.draw_figs(AZD)
                        if ans == 'a':
                            files = {}
                            for key in AZD.keys():
                                files[key] = "LO:_"+locname+'_SI:_'+PmagSpecRec['er_site_name'] + \
                                    '_SA:_' + \
                                    PmagSpecRec['er_sample_name'] + \
                                    '_SP:_'+s+'_CO:_s_TY:_'+key+fmt
                            pmagplotlib.save_plots(AZD, files)
                            ans = ""
                        if ans == 'q':
                            print("Good bye")
                            sys.exit()
                        if ans == 'p':
                            specimen = specimen - 1
                            backup = 1
                            ans = ""
                        if ans == 's':
                            keepon = 1
                            spec = input(
                                'Enter desired specimen name (or first part there of): ')
                            while keepon == 1:
                                try:
                                    specimen = sids.index(spec)
                                    keepon = 0
                                except:
                                    tmplist = []
                                    for qq in range(len(sids)):
                                        if spec in sids[qq]:
                                            tmplist.append(sids[qq])
                                    print(specimen, " not found, but this was: ")
                                    print(tmplist)
                                    spec = input('Select one or try again\n ')
                            ans = ""
                        if ans == 'b':
                            if end == 0 or end >= len(zijdblock):
                                end = len(zijdblock)-1
                            GoOn = 0
                            while GoOn == 0:
                                answer = input(
                                    'Enter index of first point for calculation: ['+str(start)+']  ')
                                try:
                                    start = int(answer)
                                    answer = input(
                                        'Enter index  of last point for calculation: ['+str(end)+']  ')
                                    end = int(answer)
                                    if start >= 0 and start < len(zijdblock)-2 and end > 0 and end < len(zijdblock) or start >= end:
                                        GoOn = 1
                                    else:
                                        print("Bad endpoints - try again! ")
                                        start, end = 0, len(zijdblock)
                                except ValueError:
                                    print("Bad endpoints - try again! ")
                                    start, end = 0, len(zijdblock)
                            s = sids[specimen]
                            pars, errcode = pmag.PintPars(
                                datablock, araiblock, zijdblock, start, end, accept)
                            pars['measurement_step_unit'] = "K"
                            pars["specimen_lab_field_dc"] = field
                            pars["specimen_int"] = -1*field*pars["specimen_b"]
                            pars["er_specimen_name"] = s
                            pars, kill = pmag.scoreit(
                                pars, PmagSpecRec, accept, '', 0)
                            PmagSpecRec['specimen_scat'] = pars['specimen_scat']
                            PmagSpecRec['specimen_frac'] = '%5.3f' % (
                                pars['specimen_frac'])
                            PmagSpecRec['specimen_gmax'] = '%5.3f' % (
                                pars['specimen_gmax'])
                            PmagSpecRec["measurement_step_min"] = '%8.3e' % (
                                pars["measurement_step_min"])
                            PmagSpecRec["measurement_step_max"] = '%8.3e' % (
                                pars["measurement_step_max"])
                            PmagSpecRec["measurement_step_unit"] = "K"
                            PmagSpecRec["specimen_int_n"] = '%i' % (
                                pars["specimen_int_n"])
                            PmagSpecRec["specimen_lab_field_dc"] = '%8.3e' % (
                                pars["specimen_lab_field_dc"])
                            PmagSpecRec["specimen_int"] = '%9.4e ' % (
                                pars["specimen_int"])
                            PmagSpecRec["specimen_b"] = '%5.3f ' % (
                                pars["specimen_b"])
                            PmagSpecRec["specimen_q"] = '%5.1f ' % (
                                pars["specimen_q"])
                            PmagSpecRec["specimen_f"] = '%5.3f ' % (
                                pars["specimen_f"])
                            PmagSpecRec["specimen_fvds"] = '%5.3f' % (
                                pars["specimen_fvds"])
                            PmagSpecRec["specimen_b_beta"] = '%5.3f' % (
                                pars["specimen_b_beta"])
                            PmagSpecRec["specimen_int_mad"] = '%7.1f' % (
                                pars["specimen_int_mad"])
                            PmagSpecRec["specimen_Z"] = '%7.1f' % (
                                pars["specimen_Z"])
                            PmagSpecRec["specimen_gamma"] = '%7.1f' % (
                                pars["specimen_gamma"])
                            PmagSpecRec["specimen_grade"] = pars["specimen_grade"]
                            if pars["method_codes"] != "":
                                tmpcodes = pars["method_codes"].split(":")
                                for t in tmpcodes:
                                    if t.strip() not in methcodes:
                                        methcodes.append(t.strip())
                            PmagSpecRec["specimen_dec"] = '%7.1f' % (
                                pars["specimen_dec"])
                            PmagSpecRec["specimen_inc"] = '%7.1f' % (
                                pars["specimen_inc"])
                            PmagSpecRec["specimen_tilt_correction"] = '-1'
                            PmagSpecRec["specimen_direction_type"] = 'l'
                            # this is redundant, but helpful - won't be imported
                            PmagSpecRec["direction_type"] = 'l'
                            PmagSpecRec["specimen_int_dang"] = '%7.1f ' % (
                                pars["specimen_int_dang"])
                            PmagSpecRec["specimen_drats"] = '%7.1f ' % (
                                pars["specimen_drats"])
                            PmagSpecRec["specimen_drat"] = '%7.1f ' % (
                                pars["specimen_drat"])
                            PmagSpecRec["specimen_int_ptrm_n"] = '%i ' % (
                                pars["specimen_int_ptrm_n"])
                            PmagSpecRec["specimen_rsc"] = '%6.4f ' % (
                                pars["specimen_rsc"])
                            PmagSpecRec["specimen_md"] = '%i ' % (
                                int(pars["specimen_md"]))
                            if PmagSpecRec["specimen_md"] == '-1':
                                PmagSpecRec["specimen_md"] = ""
                            PmagSpecRec["specimen_b_sigma"] = '%5.3f ' % (
                                pars["specimen_b_sigma"])
                            if "IE-TT" not in methcodes:
                                methcodes.append("IE-TT")
                            methods = ""
                            for meth in methcodes:
                                methods = methods+meth+":"
                            PmagSpecRec["magic_method_codes"] = methods[:-1]
                            PmagSpecRec["specimen_description"] = comment
                            PmagSpecRec["magic_software_packages"] = version_num
                            pmagplotlib.plot_arai_zij(
                                AZD, araiblock, zijdblock, s, units[0])
                            pmagplotlib.plot_b(AZD, araiblock, zijdblock, pars)
                            if verbose:
                                pmagplotlib.draw_figs(AZD)
                            if len(trmblock) > 2:
                                blab = field
                                best = pars["specimen_int"]
                                Bs, TRMs = [], []
                                for trec in trmblock:
                                    Bs.append(
                                        float(trec['treatment_dc_field']))
                                    TRMs.append(
                                        float(trec['measurement_magn_moment']))
                                # calculate best fit parameters through TRM acquisition data, and get new banc
                                NLpars = nlt.NLtrm(Bs, TRMs, best, blab, 0)
                                Mp, Bp = [], []
                                for k in range(int(max(Bs)*1e6)):
                                    Bp.append(float(k)*1e-6)
                                    # predicted NRM for this field
                                    npred = nlt.TRM(
                                        Bp[-1], NLpars['xopt'][0], NLpars['xopt'][1])
                                    Mp.append(npred)
                                pmagplotlib.plot_trm(
                                    AZD['TRM'], Bs, TRMs, Bp, Mp, NLpars, trec['magic_experiment_name'])
                                if verbose:
                                    print(
                                        'Non-linear TRM corrected intensity= ', float(NLpars['banc'])*1e6)
                            if verbose:
                                pmagplotlib.draw_figs(AZD)
                            pars["specimen_lab_field_dc"] = field
                            pars["specimen_int"] = -1*field*pars["specimen_b"]
                            pars, kill = pmag.scoreit(
                                pars, PmagSpecRec, accept, '', verbose)
                            saveit = input(
                                "Save this interpretation? [y]/n \n")
                            if saveit != 'n':
                                # put back an interpretation
                                PriorRecs.append(PmagSpecRec)
                                specimen += 1
                                save_redo(PriorRecs, inspec)
                            ans = ""
                elif plots == 1:
                    specimen += 1
                    if fmt != ".pmag":
                        files = {}
                        for key in AZD.keys():
                            files[key] = "LO:_"+locname+'_SI:_'+PmagSpecRec['er_site_name']+'_SA:_' + \
                                PmagSpecRec['er_sample_name'] + \
                                '_SP:_'+s+'_CO:_s_TY:_'+key+'_'+fmt
                        if pmagplotlib.isServer:
                            black = '#000000'
                            purple = '#800080'
                            titles = {}
                            titles['deremag'] = 'DeReMag Plot'
                            titles['zijd'] = 'Zijderveld Plot'
                            titles['arai'] = 'Arai Plot'
                            AZD = pmagplotlib.add_borders(
                                AZD, titles, black, purple)
                        pmagplotlib.save_plots(AZD, files, dpi=dpi)
    #                   pmagplotlib.combineFigs(s,files,3)
                    else:  # save in pmag format
                        script = "grep "+s+" output.mag | thellier -mfsi"
                        script = script+' %8.4e' % (field)
                        min = '%i' % ((pars["measurement_step_min"]-273))
                        Max = '%i' % ((pars["measurement_step_max"]-273))
                        script = script+" "+min+" "+Max
                        script = script+" |plotxy;cat mypost >>thellier.ps\n"
                        pltf.write(script)
                        pmag.domagicmag(outf, MeasRecs)
        if len(CurrRec) > 0:
            for rec in CurrRec:
                PriorRecs.append(rec)
        CurrRec = []
    if plots != 1 and verbose:
        ans = input(" Save last plot? 1/[0] ")
        if ans == "1":
            if fmt != ".pmag":
                files = {}
                for key in AZD.keys():
                    files[key] = s+'_'+key+fmt
                pmagplotlib.save_plots(AZD, files, dpi=dpi)
        else:
            print("\n Good bye\n")
            sys.exit()
        if len(CurrRec) > 0:
            PriorRecs.append(CurrRec)  # put back an interpretation
        if len(PriorRecs) > 0:
            save_redo(PriorRecs, inspec)
            print('Updated interpretations saved in ', inspec)
    if verbose:
        print("Good bye")


if __name__ == "__main__":
    main()

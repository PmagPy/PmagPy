#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.nlt as nlt


def main():
    """
    NAME
        trmaq_magic.py

    DESCTIPTION
        does non-linear trm acquisisiton correction

    SYNTAX
        trmaq_magic.py [-h][-i][command line options]

    OPTIONS
        -h prints help message and quits
        -i allows interactive setting of file names
        -f MFILE, sets magic_measurements input file
        -ft TSPEC, sets thellier_specimens input file
        -F OUT, sets output for non-linear TRM acquisition corrected data
        -sav save figures and quit
        -fmt [png, svg, pdf]
        -DM [2, 3] MagIC data model, default 3


    DEFAULTS
        MFILE: trmaq_measurements.txt
        TSPEC: thellier_specimens.txt
        OUT: NLT_specimens.txt
    """
    meas_file = 'trmaq_measurements.txt'
    tspec = "thellier_specimens.txt"
    output = 'NLT_specimens.txt'
    data_model_num = int(float(pmag.get_named_arg("-DM", 3)))
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-i' in sys.argv:
        meas_file = input(
            "Input magic_measurements file name? [trmaq_measurements.txt] ")
        if meas_file == "":
            meas_file = "trmaq_measurements.txt"
        tspec = input(
            " thellier_specimens file name? [thellier_specimens.txt] ")
        if tspec == "":
            tspec = "thellier_specimens.txt"
        output = input(
            "File for non-linear TRM adjusted specimen data: [NLTspecimens.txt] ")
        if output == "":
            output = "NLT_specimens.txt"
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        meas_file = sys.argv[ind+1]
    if '-ft' in sys.argv:
        ind = sys.argv.index('-ft')
        tspec = sys.argv[ind+1]
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        output = sys.argv[ind+1]
    if '-sav' in sys.argv:
        save_plots = True
    else:
        save_plots = False
    fmt = pmag.get_named_arg("-fmt", "svg")
    #
    PLT = {'aq': 1}
    if not save_plots:
        pmagplotlib.plot_init(PLT['aq'], 5, 5)
    #
    # get name of file from command line
    #
    comment = ""
    #
    #
    meas_data, file_type = pmag.magic_read(meas_file)
    if 'measurements' not in file_type:
        print(file_type, "This is not a valid measurements file ")
        sys.exit()

    if data_model_num == 2:
        spec_col = "er_specimen_name"
        lab_field_dc_col = "specimen_lab_field_dc"
        int_col = "specimen_int"
        meth_col = "magic_method_codes"
        treat_dc_col = "treatment_dc_field"
        magn_moment_col = "measurement_magn_moment"
        experiment_col = "magic_experiment_name"
        outfile_type = "pmag_specimens"
    else:
        spec_col = "specimen"
        lab_field_dc_col = "int_treat_dc_field"
        int_col = "int_abs"
        meth_col = "method_codes"
        treat_dc_col = "treat_dc_field"
        magn_moment_col = "magn_moment"
        experiment_col = "experiment"
        outfile_type = "specimens"

    sids = pmag.get_specs(meas_data)
    specimen = 0
    #
    # read in thellier_specimen data
    #
    nrm, file_type = pmag.magic_read(tspec)
    PmagSpecRecs= []
    while specimen < len(sids):
        #
        # find corresoponding paleointensity data for this specimen
        #
        s = sids[specimen]
        blab, best = "", ""
        for nrec in nrm:   # pick out the Banc data for this spec
            if nrec[spec_col] == s:
                try:
                    blab = float(nrec[lab_field_dc_col])
                except ValueError:
                    continue
                best = float(nrec[int_col])
                TrmRec = nrec
                break
        if blab == "":
            print("skipping ", s, " : no best ")
            specimen += 1
        else:
            print(sids[specimen], specimen+1, 'of ',
                  len(sids), 'Best = ', best*1e6)
            MeasRecs = []
    #
    # find the data from the meas_data file for this specimen
    #
            for rec in meas_data:
                if rec[spec_col] == s:
                    meths = rec[meth_col].split(":")
                    methcodes = []
                    for meth in meths:
                        methcodes.append(meth.strip())
                    if "LP-TRM" in methcodes:
                        MeasRecs.append(rec)
            if len(MeasRecs) < 2:
                specimen += 1
                print('skipping specimen -  no trm acquisition data ', s)
    #
    #  collect info for the PmagSpecRec dictionary
    #
            else:
                TRMs, Bs = [], []
                for rec in MeasRecs:
                    Bs.append(float(rec[treat_dc_col]))
                    TRMs.append(float(rec[magn_moment_col]))
                # calculate best fit parameters through TRM acquisition data, and get new banc
                NLpars = nlt.NLtrm(Bs, TRMs, best, blab, 0)
    #
                Mp, Bp = [], []
                for k in range(int(max(Bs)*1e6)):
                    Bp.append(float(k)*1e-6)
                    # predicted NRM for this field
                    npred = nlt.TRM(Bp[-1], NLpars['xopt']
                                    [0], NLpars['xopt'][1])
                    Mp.append(npred)
                pmagplotlib.plot_trm(
                    PLT['aq'], Bs, TRMs, Bp, Mp, NLpars, rec[experiment_col])
                if not save_plots:
                    pmagplotlib.draw_figs(PLT)
                print('Banc= ', float(NLpars['banc'])*1e6)
                trmTC = {}
                for key in list(TrmRec.keys()):
                    # copy of info from thellier_specimens record
                    trmTC[key] = TrmRec[key]
                trmTC[int_col] = '%8.3e' % (NLpars['banc'])
                trmTC[meth_col] = TrmRec[meth_col]+":DA-NL"
                PmagSpecRecs.append(trmTC)
                if not save_plots:
                    ans = input("Return for next specimen, s[a]ve plot  ")
                    if ans == 'a':
                        Name = {'aq': rec[spec_col]+'_TRM.{}'.format(fmt)}
                        pmagplotlib.save_plots(PLT, Name)
                else:
                    Name = {'aq': rec[spec_col]+'_TRM.{}'.format(fmt)}
                    pmagplotlib.save_plots(PLT, Name)

                specimen += 1

    pmag.magic_write(output, PmagSpecRecs, outfile_type)


if __name__ == "__main__":
    main()

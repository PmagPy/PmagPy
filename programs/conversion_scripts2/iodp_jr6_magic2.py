#!/usr/bin/env python
from __future__ import print_function
from builtins import str
import sys
import numpy as np
import os
import pmagpy.pmag as pmag

def main(command_line=True, **kwargs):
    """
    NAME
        iodp_jr6_magic.py

    DESCRIPTION
        converts shipboard .jr6 format files to magic_measurements format files

    SYNTAX
        iodp_jr6_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify  input file, or
        -F FILE: specify output file, default is magic_measurements.txt
        -fsa FILE: specify  er_samples.txt file for sample name lookup ,
           default is 'er_samples.txt'
        -loc HOLE : specify hole name (U1456A)
        -A: don't average replicate measurements

    INPUT
        JR6 .jr6 format file
    """


    def fix_separation(filename, new_filename):
        old_file = open(filename, 'r')
        data = old_file.readlines()
        new_data = []
        for line in data:
            new_line = line.replace('-', ' -')
            new_line = new_line.replace('  ', ' ')
            new_data.append(new_line)
        new_file = open(new_filename, 'w')
        for s in new_data:
            new_file.write(s)
        old_file.close()
        new_file.close()
        return new_filename


    def old_fix_separation(filename, new_filename):
        old_file = open(filename, 'r')
        data = old_file.readlines()
        new_data = []
        for line in data:
            new_line = []
            for i in line.split():
                if '-' in i[1:]:
                    lead_char = '-' if i[0] == '-' else ''
                    if lead_char:
                        v = i[1:].split('-')
                    else:
                        v = i.split('-')
                    new_line.append(lead_char + v[0])
                    new_line.append('-' + v[1])
                else:
                    new_line.append(i)
            new_line = (' '.join(new_line)) + '\n'
            new_data.append(new_line)
        new_file = open(new_filename, 'w')
        for s in new_data:
            new_file.write(s)
        new_file.close()
        old_file.close()
        return new_filename



# initialize some stuff
    noave=0
    volume=2.5**3 #default volume is a 2.5cm cube
    inst=""
    samp_con,Z='5',""
    missing=1
    demag="N"
    er_location_name="unknown"
    citation='This study'
    args=sys.argv
    meth_code="LP-NO"
    version_num=pmag.get_version()
    dir_path='.'
    MagRecs=[]
    samp_file = 'er_samples.txt'
    meas_file = 'magic_measurements.txt'
    mag_file = ''
    #
    # get command line arguments
    #
    if command_line:
        if '-WD' in sys.argv:
            ind = sys.argv.index('-WD')
            dir_path=sys.argv[ind+1]
        if '-ID' in sys.argv:
            ind = sys.argv.index('-ID')
            input_dir_path = sys.argv[ind+1]
        else:
            input_dir_path = dir_path
        output_dir_path = dir_path
        if "-h" in args:
            print(main.__doc__)
            return False
        if '-F' in args:
            ind=args.index("-F")
            meas_file = args[ind+1]
        if '-fsa' in args:
            ind = args.index("-fsa")
            samp_file = args[ind+1]
            if samp_file[0]!='/':
                samp_file = os.path.join(input_dir_path, samp_file)
            try:
                open(samp_file,'r')
                ErSamps,file_type=pmag.magic_read(samp_file)
            except:
                print(samp_file,' not found: ')
                print('   download csv file and import to MagIC with iodp_samples_magic.py')
        if '-f' in args:
            ind = args.index("-f")
            mag_file= args[ind+1]
        if "-loc" in args:
            ind=args.index("-loc")
            er_location_name=args[ind+1]
        if "-A" in args:
            noave=1
    if not command_line:
        dir_path = kwargs.get('dir_path', '.')
        input_dir_path = kwargs.get('input_dir_path', dir_path)
        output_dir_path = dir_path
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        mag_file = kwargs.get('mag_file', '')
        samp_file = kwargs.get('samp_file', 'er_samples.txt')
        specnum = kwargs.get('specnum', 1)
        samp_con = kwargs.get('samp_con', '1')
        if len(str(samp_con)) > 1:
            samp_con, Z = samp_con.split('-')
        else:
            Z = ''
        er_location_name = kwargs.get('er_location_name', '')
        noave = kwargs.get('noave', 0) # default (0) means DO average
        meth_code = kwargs.get('meth_code', "LP-NO")

    # format variables
    meth_code=meth_code+":FS-C-DRILL-IODP:SP-SS-C:SO-V"
    meth_code=meth_code.strip(":")
    if mag_file:
        mag_file = os.path.join(input_dir_path, mag_file)
    samp_file = os.path.join(input_dir_path, samp_file)
    meas_file = os.path.join(output_dir_path, meas_file)

    # validate variables
    if not mag_file:
        print("You must provide an IODP_jr6 format file")
        return False, "You must provide an IODP_jr6 format file"
    if not os.path.exists(mag_file):
        print('The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(mag_file))
        return False, 'The input file you provided: {} does not exist.\nMake sure you have specified the correct filename AND correct input directory name.'.format(mag_file)
    if not os.path.exists(samp_file):
        print("Your input directory:\n{}\nmust contain an er_samples.txt file, or you must explicitly provide one".format(input_dir_path))
        return False, "Your input directory:\n{}\nmust contain an er_samples.txt file, or you must explicitly provide one".format(input_dir_path)

    # parse data
    temp = os.path.join(output_dir_path, 'temp.txt')
    fix_separation(mag_file, temp)
    samples, filetype = pmag.magic_read(samp_file)
    with open(temp, 'r') as finput:
        lines = finput.readlines()
    os.remove(temp)
    for line in lines:
        MagRec = {}
        line = line.split()
        spec_text_id = line[0].split('_')[1]
        SampRecs=pmag.get_dictitem(samples,'er_sample_alternatives',spec_text_id,'has')
        if len(SampRecs)>0: # found one
            MagRec['er_specimen_name']=SampRecs[0]['er_sample_name']
            MagRec['er_sample_name']=MagRec['er_specimen_name']
            MagRec['er_site_name']=MagRec['er_specimen_name']
            MagRec["er_citation_names"]="This study"
            MagRec['er_location_name']=er_location_name
            MagRec['magic_software_packages']=version_num
            MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_flag"]='g'
            MagRec["measurement_standard"]='u'
            MagRec["measurement_number"]='1'
            MagRec["treatment_ac_field"]='0'

            volume=float(SampRecs[0]['sample_volume'])
            x = float(line[4])
            y = float(line[3])
            negz = float(line[2])
            cart=np.array([x,y,-negz]).transpose()
            direction = pmag.cart2dir(cart).transpose()
            expon = float(line[5])
            magn_volume = direction[2] * (10.0**expon)
            moment = magn_volume * volume

            MagRec["measurement_magn_moment"]=str(moment)
            MagRec["measurement_magn_volume"]=str(magn_volume)#str(direction[2] * (10.0 ** expon))
            MagRec["measurement_dec"]='%7.1f'%(direction[0])
            MagRec["measurement_inc"]='%7.1f'%(direction[1])

            step = line[1]
            if step == 'NRM':
                meas_type="LT-NO"
            elif step[0:2] == 'AD':
                meas_type="LT-AF-Z"
                treat=float(step[2:])
                MagRec["treatment_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
            elif step[0:2] == 'TD':
                meas_type="LT-T-Z"
                treat=float(step[2:])
                MagRec["treatment_temp"]='%8.3e' % (treat+273.) # temp in kelvin
            elif step[0:3]=='ARM': #
                meas_type="LT-AF-I"
                treat=float(row['step'][3:])
                MagRec["treatment_ac_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
                MagRec["treatment_dc_field"]='%8.3e' %(50e-6) # assume 50uT DC field
                MagRec["measurement_description"]='Assumed DC field - actual unknown'
            elif step[0:3]=='IRM': #
                meas_type="LT-IRM"
                treat=float(step[3:])
                MagRec["treatment_dc_field"]='%8.3e' %(treat*1e-3) # convert from mT to tesla
            else:
                print('unknown treatment type for ',row)
                return False, 'unknown treatment type for ',row

            MagRec['magic_method_codes']=meas_type
            MagRecs.append(MagRec.copy())

        else:
            print('sample name not found: ',row['specname'])
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    file_created, error_message = pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    if file_created:
        return True, meas_file
    else:
        return False, 'Results not written to file'


if __name__ == '__main__':
    main()

#!/usr/bin/env python
import sys,os
from pmagpy import contribution_builder as cb

def main():
    """
    NAME
        bryson_xpeem_measurements.py

    DESCRIPTION
        converts James Bruson XPEEM files into a MagIC format measurement file

    SYNTAX
        bryson_xpeem_measurements.py [command line options]

    OPTIONS
        -h: prints the help message and quits.

        -d DIRECTORY: specify directory where the XPEEM files are located, otherwise current directory is used.

        -s: set the starting measurement sequence number. Default:1

    """

    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-s' in sys.argv:
        ind=sys.argv.index('-s')
        sequence=int(sys.argv[ind+1])
        print("-s =",sys.argv[ind+1])
    else:
        sequence=1
    if '-d' in sys.argv:
        ind=sys.argv.index('-d')
        dir_name=sys.argv[ind+1]
    else:
        dir_name=""
    if dir_name != "":
        os.chdir(dir_name)
        file_list=os.listdir()
        print(file_list)
    else:
        file_list=os.listdir()
    

    x_spacing = 9.488e-9
    y_spacing = 9.709e-9
    md = cb.Contribution()  #md stands for magic file data
    location_data=[{'location':'Portales Valley Meteorite', 'location_type':'Meteorite', 'geologic_classes':'Meteorite', 'lithologies':'H Ordinary Chondrite', 'lat_s':'0', 'lat_n':'0', 'lon_w':'0', 'lon_e':'0', 'age':'4.5', 'age_unit':'Ga'}]
    md.add_magic_table_from_data('locations',location_data)
    md.write_table_to_file('locations')
    siteA_data=[{'site':'Interface A', 'location':'Portales Valley Meteorite', 'result_type':'i', 'result_quality':'g', 'method_codes':'GM-CC', 'citations':'10.1029/2019JE005951', 'geologic_classes':'Meteorite', 'lithologies':'H Ordinary Chondrite', 'geologic_types':'Meteorite', 'lat':'0', 'lon':'0', 'age':'4.5', 'age_unit':'Ga', 'int_abs':'0.000019', 'int_abs_sigma':'0.000006'}]
    siteB_data=[{'site':'Interface B', 'location':'Portales Valley Meteorite', 'result_type':'i', 'result_quality':'g', 'method_codes':'GM-CC', 'citations':'10.1029/2019JE005951', 'geologic_classes':'Meteorite', 'lithologies':'H Ordinary Chondrite', 'geologic_types':'Meteorite', 'lat':'0', 'lon':'0', 'age':'4.5', 'age_unit':'Ga', 'int_abs':'0.000009', 'int_abs_sigma':'0.0000035'}]
    md.add_magic_table_from_data('sites',siteA_data + siteB_data)
    md.write_table_to_file('sites')
    samp_names=[]
    samps=[]
    specs=[]
    for file in file_list:
        file_dir=file[:-9]
        mf=open(file_dir+'measurements.txt','w')
        mf.write("tab\tmeasurements\n")
        mf.write('measurement\texperiment\tspecimen\tsequence\tstandard\tquality\tmethod_codes\tcitations\tderived_value\tmeas_pos_x\tmeas_pos_y\n')
        print("file=",file)
        site=file[2:3]
        print('site=',site)
        spec_name=file_dir
        samp_name=file[:5]
        print ('samp_name=',samp_name)
        if samp_name not in samp_names:
            samp_names.append(samp_name)
            samp={'sample':samp_name, 'site':'Interface '+site, 'result_type':'i', 'result_quality':'g', ' method_codes':'GM-CC', 'citations':'10.1029/2019JE005951', 'geologic_classes':'Meteorite', 'lithologies':'H Ordinary Chondrite', 'geologic_types':'Meteorite'}
            samps.append(samp)
        spec={'specimen':spec_name, 'sample':samp_name, 'result_quality':'g', 'method_codes':'GM-CC', 'citations':'10.1029/2019JE005951', 'geologic_classes':'Meteorite', 'lithologies':'H Ordinary Chondrite', 'geologic_types':'Meteorite'}
        specs.append(spec)
        m=open(dir_name+file,'r')
        line=m.readline() 
        y=0
        while line != "":
#            print(line)
            values=line.split('\t')
            x=0
            for value in values:
#                print('value=',value,' x=',x,' y=',y) 
#                print('sequence=',sequence)
                if value == '':
                    value='0' 
                if value == '\t':
                    value='0' 
                mf.write(spec_name+str(x)+str(y)+'\t'+spec_name+'_xpeem\t'+spec_name+'\t' +str(sequence)+'\tu\tg\tGM-CC\t10.1029/2019JE005951\tXPEEM,'+str(int(value))+',10.1088/1742-6596/430/1/012127\t'+str(x*x_spacing)+'\t'+str(y*y_spacing)+'\n')
#                print('measurement=',measurement) 
                x+=1
                sequence+=1
            y+=1
            line = m.readline() 
        print("file_dir",file_dir)
        mf.close()
    md.add_magic_table_from_data('samples',samps)
    md.write_table_to_file('samples')
    md.add_magic_table_from_data('specimens',specs)
    md.write_table_to_file('specimens')
#    md.add_magic_table_from_data('measurements',measurements)
#    md.write_table_to_file('measurements')
#    sys.command('upload_magic.py')
    print("end")
#        os.mkdir(file_dir)
#        xpeem_file=open(dir_name+file,r)
#        magic_file=open(

def do_help():
    """
    returns help string of script
    """
    return __doc__

if __name__ == "__main__":
    main()


#!/usr/bin/env python
"""
EXAMPLE DOCSTRING for script (delete this line)

NAME
    template_magic.py

DESCRIPTION
    converts TEMPLATE format files to MagIC format files

SYNTAX
    template_magic.py [command line options]

OPTIONS
    -h : prints the help message and quits.
    -usr : colon delimited list of analysts (default : "")
    -f : magnetometer file path
"""
from __future__ import print_function
import os,sys
import pmagpy.pmag as pmag
import pmagpy.contribution_builder as cb
from pandas import DataFrame

def convert(**kwargs):
    """
    EXAMPLE DOCSTRING for function (you would usually put the discription here)

    Parameters
    -----------
    user : colon delimited list of analysts (default : "")
    magfile : input magnetometer file (required)

    Returns
    -----------
    type - Tuple : (True or False indicating if conversion was sucessful, meas_file name written)
    """

    #get parameters from kwargs.get(parameter_name, default_value)
    user = kwargs.get('user', '')
    magfile = kwargs.get('magfile')

    #do any extra formating you need to variables here

    #open magfile to start reading data
    try:
        infile=open(magfile,'r')
    except Exception as ex:
        print(("bad file path: ", magfile))
        return False, "bad file path"

    #Depending on the dataset you may need to read in all data here put it in a list of dictionaries or something here. If you do just replace the "for line in infile.readlines():" bellow with "for d in data:" where data is the structure you put your data into

    #define the lists that hold each line of data for their respective tables
    SpecRecs,SampRecs,SiteRecs,LocRecs,MeasRecs=[],[],[],[],[]

    #itterate over the contence of the file
    for line in infile.readlines():
        MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}

        #extract data from line and put it in variables

        #fill this line of the Specimen table using above variables
        if specimen!="" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
            SpecRec['analysts']=user
            SpecRecs.append(SpecRec)
        #fill this line of the Sample table using above variables
        if sample!="" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
            SampRec['analysts']=user
            SampRecs.append(SampRec)
        #fill this line of the Site table using above variables
        if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
            SiteRec['analysts']=user
            SiteRecs.append(SiteRec)
        #fill this line of the Location table using above variables
        if location!="" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
            LocRec['analysts']=user
            LocRecs.append(LocRec)

        #Fill this line of Meas Table using data in line
        MeasRec['analysts']=user
        MeasRecs.append(MeasRec)

    #close your file object so Python3 doesn't throw an annoying warning
    infile.close()

    #open a Contribution object
    con = cb.Contribution(output_dir_path,read_tables=[])

    #Create Magic Tables and add to a contribution
    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts=pmag.measurements_methods3(MeasRecs,noave) #figures out method codes for measuremet data
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    #write to file
    con.write_table_to_file('specimens', custom_name=spec_file)
    con.write_table_to_file('samples', custom_name=samp_file)
    con.write_table_to_file('sites', custom_name=site_file)
    con.write_table_to_file('locations', custom_name=loc_file)
    meas_file = con.write_table_to_file('measurements', custom_name=meas_file)

    return True, meas_file

def do_help():
    """
    returns help string of script
    """
    return __doc__

def main():
    kwargs = {} #create a key word argument dictionary
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if "-usr" in sys.argv: #check for flag
        ind=sys.argv.index("-usr") #find flag
        kwargs['user']=sys.argv[ind+1] #get data and store in dictionary
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        kwargs['magfile']=sys.argv[ind+1]

    convert(**kwargs)

#this if statement insures it's being called from the commandline
if __name__ == "__main__":
    main()

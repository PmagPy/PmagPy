#!/usr/bin/env python

"""
Module for building or reading in specimen, sample, site, and location data.
"""

import os
import pmag
import validate_upload
import pmag_widgets as pw

class ErMagicBuilder(object):
    """
    more object oriented builder
    """

    def __init__(self, WD):
        self.WD = WD
        self.specimens = []
        self.samples = []
        self.sites = []
        self.locations = []
        self.results = []
        #self.ages = []
        self.ancestry = [None, 'specimen', 'sample', 'site', 'location', None]
        self.data_model = validate_upload.get_data_model()
        self.data_lists = {'specimen': [self.specimens, Specimen], 'sample': [self.samples, Sample],
                           'site': [self.sites, Site], 'location': [self.locations, Location],
                           'age': [self.sites, Site], 'result': [self.results, Result]}
        self.add_methods = {'specimen': self.add_specimen, 'sample': self.add_sample,
                            'site': self.add_site, 'location': self.add_location,
                            'age': None, 'result': self.add_result}
        self.update_methods = {'specimen': self.change_specimen, 'sample': self.change_sample,
                               'site': self.change_site, 'location': self.change_location,
                               'age': None, 'result': self.change_result}
        self.delete_methods = {'specimen': self.delete_specimen, 'sample': self.delete_sample,
                               'site': self.delete_site, 'location': self.delete_location,
                               'age': None, 'result': self.delete_result}
        self.headers = {
            'specimen': {'er': [[], [], []], 'pmag': [[], [], []]},
            
            'sample': {'er': [[], [], []], 'pmag': [[], [], []]},
            
            'site': {'er': [[], [], []], 'pmag': [[], [], []]},
            
            'location': {'er': [[], [], []], 'pmag': [[], [], []]},
            
            'age': {'er': [[], [], []], 'pmag': [[], [], []]},

            'result': {'er': [[], [], []], 'pmag': [[], [], []]}
        }


    def find_by_name(self, item_name, items_list):
        """
        Return item from items_list with name item_name.
        """
        names = [item.name for item in items_list]
        if item_name in names:
            ind = names.index(item_name)
            return items_list[ind]
        return False

    def init_default_headers(self):
        """
        initialize default required headers.
        if there were any pre-existing headers, keep them also.
        """
        if not self.data_model:
            self.data_model = validate_upload.get_data_model()
            if not self.data_model:
                pw.simple_warning("Can't access MagIC-data-model at the moment.\nIf you are working offline, make sure MagIC-data-model.txt is in your PmagPy directory (or download it from https://github.com/ltauxe/PmagPy and put it in your PmagPy directory).\nOtherwise, check your internet connection")
                return False

        # actual is at position 0, reqd is at position 1, optional at position 2
        self.headers['specimen']['er'][1], self.headers['specimen']['er'][2] = self.get_headers('er_specimens')
        self.headers['sample']['er'][1], self.headers['sample']['er'][2] = self.get_headers('er_samples')
        self.headers['site']['er'][1], self.headers['site']['er'][2] = self.get_headers('er_sites')
        self.headers['location']['er'][1], self.headers['location']['er'][2] = self.get_headers('er_locations')
        self.headers['age']['er'][1], self.headers['age']['er'][2] = self.get_headers('er_ages')
        
        self.headers['result']['pmag'][1], self.headers['result']['pmag'][2] = self.get_headers('pmag_results')
        self.headers['specimen']['pmag'][1], self.headers['specimen']['pmag'][2] = self.get_headers('pmag_specimens')
        self.headers['sample']['pmag'][1], self.headers['sample']['pmag'][2] = self.get_headers('pmag_samples')
        self.headers['site']['pmag'][1], self.headers['site']['pmag'][2] = self.get_headers('pmag_sites')

    def get_headers(self, data_type):
        try:
            data_dict = self.data_model[data_type]
        except KeyError:
            return [], []
        reqd_headers = sorted([header for header in data_dict.keys() if data_dict[header]['data_status'] == 'Required'])
        optional_headers = sorted([header for header in data_dict.keys() if data_dict[header]['data_status'] != 'Required'])
        return reqd_headers, optional_headers

    def init_actual_headers(self):
        def headers(data_list, reqd_er_headers, reqd_pmag_headers):
            if data_list:
                er_header = data_list[0].er_data.keys()
                pmag_header = data_list[0].pmag_data.keys()
            else:
                er_header = remove_list_headers(reqd_er_headers)
                pmag_header = remove_list_headers(reqd_pmag_headers)
            return er_header, pmag_header

        self.headers['specimen']['er'][0], self.headers['specimen']['pmag'][0] = headers(self.specimens, self.headers['specimen']['er'][1], self.headers['specimen']['pmag'][1])

        self.headers['sample']['er'][0], self.headers['sample']['pmag'][0] = headers(self.samples, self.headers['sample']['er'][1], self.headers['sample']['pmag'][1])

        self.headers['site']['er'][0], self.headers['site']['pmag'][0] = headers(self.sites, self.headers['site']['er'][1], self.headers['site']['pmag'][1])
        
        if self.locations:
            self.headers['location']['er'][0] = self.locations[0].er_data.keys()
        else:
            self.headers['location']['er'][0] = remove_list_headers(self.headers['location']['er'][1])

        if self.sites:
            self.headers['age']['er'][0] = self.sites[0].age_data.keys()
        else:
            self.headers['age']['er'][0] = remove_list_headers(self.headers['location']['er'][1])

        if self.results:
            self.headers['result']['pmag'][0] = self.results[0].pmag_data.keys()
        else:
            self.headers['result']['pmag'][0] = remove_list_headers(self.headers['result']['pmag'][1])

    def change_specimen(self, old_spec_name, new_spec_name,
                        new_sample_name=None, new_er_data=None, new_pmag_data=None,
                        replace_data=False):
        """
        Find actual data objects for specimen and sample.
        Then call Specimen class change method to update specimen name and data.
        """
        specimen = self.find_by_name(old_spec_name, self.specimens)
        if not specimen:
            print '-W- {} is not a currently existing specimen, so cannot be updated'.format(old_spec_name)
            return False
        if new_sample_name:
            new_sample = self.find_by_name(new_sample_name, self.samples)
            if not new_sample:
                print """-W- {} is not a currently existing sample.
Leaving sample unchanged as: {} for {}""".format(new_sample_name, specimen.sample or '*empty*', specimen)
        else:
            new_sample = None
        specimen.change_specimen(new_spec_name, new_sample, new_er_data, new_pmag_data, replace_data)
        return specimen

    def delete_specimen(self, spec_name):
        """
        Remove specimen with name spec_name from self.specimens.
        If the specimen belonged to a sample, remove it from the sample's specimen list.
        """
        specimen = self.find_by_name(spec_name, self.specimens)
        if not specimen:
            return False
        sample = specimen.sample
        if sample:
            sample.specimens.remove(specimen)
        self.specimens.remove(specimen)
        del specimen

    def add_specimen(self, spec_name, samp_name=None, er_data=None, pmag_data=None):
        """
        Create a Specimen object and add it to self.specimens.
        If a sample name is provided, add the specimen to sample.specimens as well.
        """
        sample = self.find_by_name(samp_name, self.samples)
        specimen = Specimen(spec_name, sample, self.data_model, er_data, pmag_data)

        self.specimens.append(specimen)
        if sample:
            sample.specimens.append(specimen)
        return specimen

    def change_sample(self, old_samp_name, new_samp_name, new_site_name=None,
                      new_er_data=None, new_pmag_data=None, replace_data=False):
        """
        Find actual data objects for sample and site.
        Then call Sample class change method to update sample name and data..
        """
        sample = self.find_by_name(old_samp_name, self.samples)
        if not sample:
            print '-W- {} is not a currently existing sample, so it cannot be updated'.format(old_samp_name)
            return False
        if new_site_name:
            new_site = self.find_by_name(new_site_name, self.sites)
            if not new_site:
                print """-W- {} is not a currently existing site.
Leaving site unchanged as: {} for {}""".format(new_site_name, sample.site or '*empty*', sample)
                new_site = None
        else:
            new_site = None
        sample.change_sample(new_samp_name, new_site, new_er_data, new_pmag_data, replace_data)
        return sample

    def add_sample(self, samp_name, site_name=None, er_data=None, pmag_data=None):
        """
        Create a Sample object and add it to self.samples.
        If a site name is provided, add the sample to site.samples as well.
        """
        site = self.find_by_name(site_name, self.sites)
        sample = Sample(samp_name, site, self.data_model, er_data, pmag_data)
        self.samples.append(sample)
        if site:
            site.samples.append(sample)
        return sample

    def delete_sample(self, sample_name, replacement_samp=None):
        """
        Remove sample with name sample_name from self.samples.
        If the sample belonged to a site, remove it from the site's sample list.
        If the sample had any specimens, change specimen.sample to "".
        """
        sample = self.find_by_name(sample_name, self.samples)
        if not sample:
            return False
        specimens = sample.specimens
        site = sample.site
        if site:
            site.samples.remove(sample)
        self.samples.remove(sample)
        for spec in specimens:
            spec.sample = ""

    def change_site(self, old_site_name, new_site_name, new_location_name=None,
                    new_er_data=None, new_pmag_data=None, replace_data=False):
        """
        Find actual data objects for site and location.
        Then call the Site class change method to update site name and data.
        """
        site = self.find_by_name(old_site_name, self.sites)
        if not site:
            print '-W- {} is not a currently existing site, so it cannot be updated.'.format(old_site_name)
            return False
        if new_location_name:
            old_location = self.find_by_name(site.location.name, self.locations)
            if old_location:
                old_location.sites.remove(site)
            new_location = self.find_by_name(new_location_name, self.locations)
            if new_location:
                new_location.sites.append(site)
            else:
                print """-W- {} is not a currently existing location.
Leaving location unchanged as: {} for {}""".format(new_site_name, site.location or '*empty*', site)
        else:
            new_location = None
        site.change_site(new_site_name, new_location, new_er_data, new_pmag_data, replace_data)
        return site

    def add_site(self, site_name, location_name=None, er_data=None, pmag_data=None):
        """
        Create a Site object and add it to self.sites.
        If a location name is provided, add the site to location.sites as well.
        """
        if location_name:
            location = self.find_by_name(location_name, self.locations)
        else:
            location = None
        new_site = Site(site_name, location, self.data_model, er_data, pmag_data)
        self.sites.append(new_site)
        if location:
            location.sites.append(new_site)
        return new_site

    def delete_site(self, site_name, replacement_site=None):
        """
        Remove site with name site_name from self.sites.
        If the site belonged to a location, remove it from the location's site list.
        If the site had any samples, change sample.site to "".
        """
        site = self.find_by_name(site_name, self.sites)
        if not site:
            return False
        self.sites.remove(site)
        if site.location:
            site.location.sites.remove(site)
        for samp in site.samples:
            samp.site = ''
        del site

    def change_location(self, old_location_name, new_location_name, new_er_data=None,
                        new_pmag_data=None, replace_data=False):
        """
        Find actual data object for location with old_location_name.
        Then call Location class change method to update location name and data.
        """
        location = self.find_by_name(old_location_name, self.locations)
        if not location:
            print '-W- {} is not a currently existing location, so it cannot be updated.'.format(old_location_name)
            return False
        location.change_location(new_location_name, new_er_data, new_pmag_data, replace_data)
        return location

    def add_location(self, location_name, parent_name=None, er_data=None, pmag_data=None):
        """
        Create a Location object and add it to self.locations.
        """
        location = Location(location_name, data_model=self.data_model, er_data=er_data, pmag_data=pmag_data)
        self.locations.append(location)
        return location

    def delete_location(self, location_name):
        """
        Remove location with name location_name from self.locations.
        If the location had any sites, change site.location to "".
        """
        location = self.find_by_name(location_name, self.locations)
        if not location:
            return False
        sites = location.sites
        self.locations.remove(location)
        for site in sites:
            site.location = ''
        del location

    def add_result(self, result_name, specimens=None, samples=None, sites=None, locations=None, pmag_data=None):
        result = Result(result_name, specimens, samples, sites, locations, pmag_data)
        self.results.append(result)
        
    def delete_result(self, result_name):
        result = self.find_by_name(result_name, self.results)
        if result:
            self.results.remove(result)
            del result
            
    def change_result(self, old_result_name, new_result_name, new_er_data=None, new_pmag_data=None, spec_names=None, samp_names=None, site_names=None, loc_names=None):
        """
        Find actual data object for result with old_result_name.
        Then call Result class change method to update result name and data.
        """
        result = self.find_by_name(old_result_name, self.results)
        if not result:
            print '-W- {} is not a currently existing result, so it cannot be updated.'.format(old_result_name)
            return False
        else:
            specimens, samples, sites, locations = None, None, None, None
            if spec_names:
                specimens = [self.find_by_name(spec, self.specimens) for spec in spec_names]
            if samp_names:
                samples = [self.find_by_name(samp, self.samples) for samp in samp_names]
            if site_names:
                sites = [self.find_by_name(site, self.sites) for site in site_names]
            if loc_names:
                locations = [self.find_by_name(loc, self.locations) for loc in loc_names]

            result.change_result(new_result_name, new_pmag_data, specimens, samples, sites, locations)
            return result
    

    ## Methods for reading in data

    def get_data(self):
        """
        attempt to read measurements file in working directory.
        """
        try:
            meas_data, file_type = pmag.magic_read(os.path.join(self.WD, "magic_measurements.txt"))
        except IOError:
            print "-E- ERROR: Can't find magic_measurements.txt file. Check path."
            return {}
        if file_type == 'bad_file':
            print "-E- ERROR: Can't read magic_measurements.txt file. File is corrupted."

        for rec in meas_data:
            #print 'rec', rec
            specimen_name = rec["er_specimen_name"]
            if specimen_name == "" or specimen_name == " ":
                continue
            sample_name = rec["er_sample_name"]
            site_name = rec["er_site_name"]
            location_name = rec["er_location_name"]

            # add items and parents
            location = self.find_by_name(location_name, self.locations)
            if not location:
                location = Location(location_name, data_model=self.data_model)
                self.locations.append(location)
            site = self.find_by_name(site_name, self.sites)
            if not site:
                site = Site(site_name, location, self.data_model)
                self.sites.append(site)
            sample = self.find_by_name(sample_name, self.samples)
            if not sample:
                sample = Sample(sample_name, site, self.data_model)
                self.samples.append(sample)
            specimen = self.find_by_name(specimen_name, self.specimens)
            if not specimen:
                specimen = Specimen(specimen_name, sample, self.data_model)
                self.specimens.append(specimen)

            # add child_items
            if not self.find_by_name(specimen_name, sample.specimens):
                sample.specimens.append(specimen)
            if not self.find_by_name(sample_name, site.samples):
                site.samples.append(sample)
            if not self.find_by_name(site_name, location.sites):
                location.sites.append(site)

    def get_all_magic_info(self):
        self.get_data()
        for child, parent in [('specimen', 'sample'), ('sample', 'site'),
                              ('site', 'location'), ('location', '')]:
            self.get_magic_info(child, parent, 'er')
            self.get_magic_info(child, parent, 'pmag')
        self.get_age_info()
        self.get_results_info()
                
    def get_magic_info(self, child_type, parent_type=None, attr='er'):
        """
        Read er_*.txt or pmag_*.txt file.
        Parse information into dictionaries for each item.
        Then add it to the item object as object.er_data or object.pmag_data.
        """
        parent = ''
        short_filename = attr + '_' + child_type + 's.txt'
        magic_file = os.path.join(self.WD, short_filename)
        magic_name = 'er_' + child_type + '_name'
        if not os.path.isfile(magic_file):
            print '-W- Could not find {} in your working directory {}'.format(short_filename, self.WD)
            return False
        # get the data from the appropriate .txt file
        data_dict = self.read_magic_file(magic_file, magic_name)[0]
        child_list, child_constructor = self.data_lists[child_type]

        if parent_type:
            parent_list, parent_constructor = self.data_lists[parent_type]
        else:
            parent_list, parent_name = None, None
        for child_name in data_dict:
            # if there is a possible parent, try to find parent object in the data model
            if parent_type:
                parent_name = data_dict[child_name]['er_' + parent_type + '_name']
                parent = self.find_by_name(parent_name, parent_list)
                if parent:
                    remove_dict_headers(parent.er_data)
                    remove_dict_headers(parent.pmag_data)
            # if there should be a parent
            # (meaning there is a name for it and the child object should have a parent)
            # but none exists in the data model, go ahead and create that parent object.
            if parent_name and parent_type and not parent:
                parent = parent_constructor(parent_name, None, data_model=self.data_model)
                parent_list.append(parent)
            # otherwise there is no parent and none can be created, so use an empty string
            elif not parent:
                parent = ''
            child = self.find_by_name(child_name, child_list)
            # if the child object does not exist yet in the data model
            if not child:
                child = child_constructor(child_name, parent, data_model=self.data_model)
                child_list.append(child)
            else:
                child.set_parent(parent)
            # add in the appropriate data dictionary
            child.__setattr__(attr + '_data', data_dict[child_name])
            #child.er_data = 

            remove_dict_headers(child.er_data)
            remove_dict_headers(child.pmag_data)
            #
            if parent and (child not in parent.children):
                parent.add_child(child)

    def get_age_info(self, sample_or_site='site'):
        """
        Read er_ages.txt file.
        Parse information into dictionaries for each site/sample.
        Then add it to the site/sample object as site/sample.age_data.
        """
        short_filename = 'er_ages.txt'
        magic_file = os.path.join(self.WD, short_filename)
        magic_name = 'er_' + sample_or_site + '_name'
        if not os.path.isfile(magic_file):
            print '-W- Could not find {} in your working directory {}'.format(short_filename, self.WD)
            return False

        data_dict = self.read_magic_file(magic_file, magic_name)[0]
        items_list, item_constructor = self.data_lists[sample_or_site]
        for pmag_name in data_dict.keys():
            pmag_item = self.find_by_name(pmag_name, items_list)
            if not pmag_item:
                pmag_item = item_constructor(pmag_name, sample_or_site, data_model=self.data_model)
                items_list.append(pmag_item)
            pmag_item.age_data = data_dict[pmag_name]

    def get_results_info(self):
        """
        Read pmag_results.txt file.
        Parse information into dictionaries for each item.
        Then add it to the item object as object.results_data.
        """
        short_filename = "pmag_results.txt"
        magic_file = os.path.join(self.WD, short_filename)
        if not os.path.isfile(magic_file):
            print '-W- Could not find {} in your working directory {}'.format(short_filename, self.WD)
            return False
        # get the data from the pmag_results.txt file
        data_dict = self.read_magic_file(magic_file, 'by_line_number')[0]

        def make_items_list(string, search_items_list):
            names = string.split(':')
            items = []
            for name in names:
                name = name.strip(' ')
                item = self.find_by_name(name, search_items_list)
                if item:
                    items.append(item)
            return items
        
        for num, result in data_dict.items():
            name, specimens, samples, sites, locations = None, None, None, None, None
            for key, value in result.items():
                #print key, ':', value
                if key == 'er_specimen_names':
                    specimens = make_items_list(value, self.specimens)
                if key == 'er_sample_names':
                    samples = make_items_list(value, self.samples)
                if key == 'er_site_names':
                    sites = make_items_list(value, self.sites)
                if key == 'er_location_names':
                    locations = make_items_list(value, self.locations)
                if key == 'pmag_result_name':
                    name = value
            for header_name in ['er_specimen_names', 'er_site_names',
                                'er_sample_names', 'er_location_names']:
                if header_name in result.keys():
                    result.pop(header_name)
            if not name:
                name = num
            result_item = Result(name, specimens, samples, sites, locations, result)
            self.results.append(result_item)
                    
    def read_magic_file(self, path, sort_by_this_name):
        """
        read a magic-formatted tab-delimited file.
        return a dictionary of dictionaries, with this format:
        {'Z35.5a': {'specimen_weight': '1.000e-03', 'er_citation_names': 'This study', 'specimen_volume': '', 'er_location_name': '', 'er_site_name': 'Z35.', 'er_sample_name': 'Z35.5', 'specimen_class': '', 'er_specimen_name': 'Z35.5a', 'specimen_lithology': '', 'specimen_type': ''}, ....}
        """
        DATA = {}
        fin = open(path, 'rU')
        fin.readline()
        line = fin.readline()
        header = line.strip('\n').split('\t')
        #print "path", path#,header
        counter = 0
        for line in fin.readlines():
            #print "line:", line
            tmp_data = {}
            tmp_line = line.strip('\n').split('\t')
            for i in range(len(header)):
                if i < len(tmp_line):
                    tmp_data[header[i]] = tmp_line[i]
                else:
                    tmp_data[header[i]] = ""
            if sort_by_this_name == "by_line_number":
                DATA[counter] = tmp_data
                counter += 1
            else:
                if tmp_data[sort_by_this_name] != "":
                    DATA[tmp_data[sort_by_this_name]] = tmp_data
        fin.close()
        return DATA, header

    



class Pmag_object(object):
    """
    Base class for Specimens, Samples, Sites, etc.
    """

    def __init__(self, name, dtype, data_model=None, er_data=None, pmag_data=None, results_data=None):#, headers={}):
        if not data_model:
            self.data_model = validate_upload.get_data_model()
        else:
            self.data_model = data_model
        self.name = name
        self.dtype = dtype

        er_name = 'er_' + dtype + 's'
        pmag_name = 'pmag_' + dtype + 's'
        self.pmag_reqd_headers, self.pmag_optional_headers = self.get_headers(pmag_name)
        self.er_reqd_headers, self.er_optional_headers = self.get_headers(er_name)
        self.results_reqd_headers, self.results_optional_headers = self.get_headers('pmag_results')
        er_reqd_data = {key: '' for key in self.er_reqd_headers}
        pmag_reqd_data = {key: '' for key in self.pmag_reqd_headers}
        results_reqd_data = {key: '' for key in self.results_reqd_headers}
        if er_data:
            self.er_data = self.combine_dicts(er_data, er_reqd_data)
        else:
            self.er_data = er_reqd_data
        if pmag_data:
            self.pmag_data = self.combine_dicts(pmag_data, pmag_reqd_data)
        else:
            self.pmag_data = pmag_reqd_data
        if results_data:
            self.results_data = self.combine_dicts(results_data, results_reqd_data)
        else:
            self.results_data = None

        if dtype in ('sample', 'site'):
            self.age_reqd_headers, self.age_optional_headers = self.get_headers('er_ages')
            self.age_data = {key: '' for key in self.age_reqd_headers}
            remove_dict_headers(self.age_data)

        remove_dict_headers(self.er_data)
        remove_dict_headers(self.pmag_data)

    def __repr__(self):
        return self.dtype + ": " + self.name

    def get_headers(self, data_type):
        """
        If data model not present, get data model from Earthref site or PmagPy directory.
        Return a list of required headers and optional headers for given data type.
        """
        try:
            data_dict = self.data_model[data_type]
        except KeyError:
            return [], []
        reqd_headers = sorted([header for header in data_dict.keys() if data_dict[header]['data_status'] == 'Required'])
        optional_headers = sorted([header for header in data_dict.keys() if data_dict[header]['data_status'] != 'Required'])
        return reqd_headers, optional_headers

    def update_data(self, er_data=None, pmag_data=None, replace_data=False):
        if er_data:
            if replace_data:
                self.er_data = er_data
            else:
                self.er_data = self.combine_dicts(er_data, self.er_data)
        if pmag_data:
            if replace_data:
                self.pmag_data = pmag_data
            else:
                self.pmag_data = self.combine_dicts(pmag_data, self.pmag_data)

    def combine_dicts(self, new_dict, old_dict):
        """
        returns a dictionary with all key, value pairs from new_dict.
        also returns key, value pairs from old_dict, if that key does not exist in new_dict.
        if a key is present in both new_dict and old_dict, the new_dict value will take precedence.
        """
        old_data_keys = old_dict.keys()
        new_data_keys = new_dict.keys()
        all_keys = set(old_data_keys).union(new_data_keys)
        combined_data_dict = {}
        for k in all_keys:
            try:
                combined_data_dict[k] = new_dict[k]
            except KeyError:
                combined_data_dict[k] = old_dict[k]
        return combined_data_dict

    def add_child(self, child):
        if 'children' in dir(self):
            self.children.append(child)


class Specimen(Pmag_object):

    """
    Specimen level object
    """
    def __init__(self, name, sample, data_model=None, er_data=None, pmag_data=None):
        dtype = 'specimen'
        super(Specimen, self).__init__(name, dtype, data_model, er_data, pmag_data)
        self.sample = sample or ""

    def get_parent(self):
        return self.sample

    def set_parent(self, new_samp):
        """
        Set self.sample as either an empty string, or with a new Sample.
        """
        self.sample = new_samp
        if new_samp:
            if not isinstance(new_samp, Sample):
                raise Exception
        return new_samp

    def change_specimen(self, new_name, new_sample=None, er_data=None, pmag_data=None, replace_data=False):
        self.name = new_name
        if new_sample:
            self.sample.specimens.remove(self)
            self.sample = new_sample
            self.sample.specimens.append(self)
        self.update_data(er_data, pmag_data, replace_data)


class Sample(Pmag_object):

    """
    Sample level object
    """

    def __init__(self, name, site, data_model=None, er_data=None, pmag_data=None):
        dtype = 'sample'
        super(Sample, self).__init__(name, dtype, data_model, er_data, pmag_data)
        self.specimens = []
        self.children = self.specimens
        self.site = site or ""

    def get_parent(self):
        return self.site

    def set_parent(self, new_site):
        """
        Set self.site as either an empty string, or with a new Site.
        """
        if new_site:
            if not isinstance(new_site, Site):
                raise Exception
        self.site = new_site
        return new_site
        
    def change_sample(self, new_name, new_site=None, er_data=None, pmag_data=None, replace_data=False):
        self.name = new_name
        if new_site:
            if self.site:
                self.site.samples.remove(self)
            self.site = new_site
            self.site.samples.append(self)
        self.update_data(er_data, pmag_data, replace_data)


class Site(Pmag_object):

    """
    Site level object
    """

    def __init__(self, name, location, data_model=None, er_data=None, pmag_data=None):
        dtype = 'site'
        super(Site, self).__init__(name, dtype, data_model, er_data, pmag_data)
        self.samples = []
        self.children = self.samples
        self.location = location or ""

    def get_parent(self):
        return self.location

    def set_parent(self, new_loc):
        if new_loc:
            if not isinstance(new_loc, Location):
                raise Exception
        self.location = new_loc
        return new_loc
        
    def change_site(self, new_name, new_location=None, new_er_data=None,
                    new_pmag_data=None, replace_data=False):
        """
        Update a site's name, location, er_data, and pmag_data.
        By default, new data will be added in to pre-existing data, overwriting existing values.
        If replace_data is True, the new data dictionary will simply take the place of the existing dict.
        """
        self.name = new_name
        if new_location:
            self.location = new_location
        self.update_data(new_er_data, new_pmag_data, replace_data)


class Location(Pmag_object):

    """
    Location level object
    """

    def __init__(self, name, parent=None, data_model=None, er_data=None, pmag_data=None):
        dtype = 'location'
        super(Location, self).__init__(name, dtype, data_model, er_data, pmag_data)
        #def __init__(self, name, dtype, data_model=None, er_data=None, pmag_data=None, results_data=None):#, headers={}):
        self.sites = []
        self.children = self.sites

    def get_parent(self):
        return False

    def set_parent(self, parent=None):
        return False
        
    def change_location(self, new_name, new_er_data=None, new_pmag_data=None, replace_data=False):
        self.name = new_name
        #if new_er_data:
        #    self.er_data = self.combine_dicts(new_er_data, self.er_data)
        self.update_data(new_er_data, new_pmag_data, replace_data)

class Result(object):

    def __init__(self, name, specimens=None, samples=None,
                 sites=None, locations=None, pmag_data=None):
        self.name = name
        self.specimens = specimens
        self.samples = samples
        self.sites = sites
        self.locations = locations
        self.pmag_data = pmag_data
        self.er_data = {}

    def __repr__(self):
        descr = self.pmag_data.get('result_description')
        return 'Result: {}, {}'.format(self.name, descr)

    def combine_dicts(self, new_dict, old_dict):
        """
        returns a dictionary with all key, value pairs from new_dict.
        also returns key, value pairs from old_dict, if that key does not exist in new_dict.
        if a key is present in both new_dict and old_dict, the new_dict value will take precedence.
        """
        old_data_keys = old_dict.keys()
        new_data_keys = new_dict.keys()
        all_keys = set(old_data_keys).union(new_data_keys)
        combined_data_dict = {}
        for k in all_keys:
            try:
                combined_data_dict[k] = new_dict[k]
            except KeyError:
                combined_data_dict[k] = old_dict[k]
        return combined_data_dict

    
    def change_result(self, new_name, new_pmag_data=None, specs=None, samps=None, sites=None, locs=None):
        self.name = new_name
        if new_pmag_data:
            self.pmag_data = self.combine_dicts(new_pmag_data, self.pmag_data)
        self.specimens = specs
        self.samples = samps
        self.sites = sites
        self.locations = locs


if __name__ == '__main__':
    wd = pmag.get_named_arg_from_sys('-WD', default_val=os.getcwd())
    builder = ErMagicBuilder(wd)
    builder.get_data()

# Random helper methods that MIGHT belong in pmag.py

def put_list_value_first(lst, first_value):
    if first_value in lst:
        lst.remove(first_value)
        lst[:0] = [first_value]

def remove_dict_headers(data_dict):
    for header in ['er_specimen_name', 'er_sample_name', 'er_site_name', 'er_location_name']:
        if header in data_dict.keys():
            data_dict.pop(header)
    return data_dict

def remove_list_headers(data_list):
    for header in ['er_specimen_name', 'er_sample_name', 'er_site_name', 'er_location_name']:
        if header in data_list:
            data_list.remove(header)
    return data_list

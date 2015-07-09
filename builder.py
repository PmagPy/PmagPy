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
        #self.ages = []
        self.data_model = validate_upload.get_data_model()
        self.data_lists = {'specimen': [self.specimens, Specimen], 'sample': [self.samples, Sample],
                           'site': [self.sites, Site], 'location': [self.locations, Location]}
        #'age': [self.ages, None]}


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
        self.headers = {}
        if not self.data_model:
            self.data_model = validate_upload.get_data_model()
            if not self.data_model:
                pw.simple_warning("Can't access MagIC-data-model at the moment.\nIf you are working offline, make sure MagIC-data-model.txt is in your PmagPy directory (or download it from https://github.com/ltauxe/PmagPy and put it in your PmagPy directory).\nOtherwise, check your internet connection")
                return False

        # header should contain all required headers, plus any already in the file

        self.er_specimens_reqd_header, self.er_specimens_optional_header = self.get_headers('er_specimens')
        self.er_samples_reqd_header, self.er_samples_optional_header = self.get_headers('er_samples')
        self.er_sites_reqd_header, self.er_sites_optional_header = self.get_headers('er_sites')
        self.er_locations_reqd_header, self.er_locations_optional_header = self.get_headers('er_locations')
        self.er_ages_reqd_header, self.er_ages_optional_header = self.get_headers('er_ages')

        self.pmag_results_reqd_header, self.pmag_results_optional_header = self.get_headers('pmag_results')
        self.pmag_specimens_reqd_header, self.pmag_specimens_optional_header = self.get_headers('pmag_specimens')
        self.pmag_samples_reqd_header, self.pmag_samples_optional_header = self.get_headers('pmag_samples')
        self.pmag_sites_reqd_header, self.pmag_sites_optional_header = self.get_headers('pmag_sites')

        self.er_specimens_header, self.er_samples_header, self.er_sites_header, self.er_locations_header, self.er_ages_header = [], [], [], [], []
        self.pmag_specimens_header, self.pmag_samples_header, self.pmag_sites_header, self.pmag_results_header = [], [], [], []


    def get_headers(self, data_type):
        try:
            data_dict = self.data_model[data_type]
        except KeyError:
            return [], []
        reqd_headers = sorted([header for header in data_dict.keys() if data_dict[header]['data_status'] == 'Required'])
        optional_headers = sorted([header for header in data_dict.keys() if data_dict[header]['data_status'] != 'Required'])
        return reqd_headers, optional_headers


    #def get_headers(self, data_type, current_header):
    #    reqd_header, optional_header = self.get_reqd_and_optional_headers(data_type)
    #    # combine already existing header with required header
    #    full_header = list(set(current_header).union(reqd_header))
    #    put_list_value_first(reqd_header, data_type[:-1] + '_name')
    #    return reqd_header, optional_header
    def init_actual_headers(self):
        if self.specimens:
            self.er_specimens_header = self.specimens[0].er_data.keys()
        else:
            self.er_specimens_header = self.er_specimens_reqd_header
        if self.samples:
            self.er_samples_header = self.samples[0].er_data.keys()
        else:
            self.er_samples_header = self.er_samples_reqd_header
        if self.sites:
            self.er_sites_header = self.sites[0].er_data.keys()
        else:
            self.er_sites_header = self.er_sites_reqd_header
        if self.locations:
            self.er_locations_header = self.locations[0].er_data.keys()
        else:
            self.er_locations_header = self.er_locations_reqd_header
        if self.sites:
            self.er_ages_header = self.sites[0].age_data.keys()
        else:
            self.er_ages_header = self.er_ages_reqd_header



    def change_specimen(self, old_spec_name, new_spec_name,
                        new_sample_name=None, new_er_data=None, new_pmag_data=None):
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
        specimen.change_specimen(new_spec_name, new_sample, new_er_data, new_pmag_data)

    def delete_specimen(self, spec_name):
        """
        Remove specimen with name spec_name from self.specimens.
        If the specimen belonged to a sample, remove it from the sample's specimen list.
        """
        specimen = self.find_by_name(spec_name, self.specimens)
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

    def change_sample(self, old_samp_name, new_samp_name, new_site_name=None, new_er_data=None, new_pmag_data=None):
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
        sample.change_sample(new_samp_name, new_site, new_er_data, new_pmag_data)

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
        specimens = sample.specimens
        site = sample.site
        if site:
            site.samples.remove(sample)
        self.samples.remove(sample)
        for spec in specimens:
            spec.sample = ""

    def change_site(self, old_site_name, new_site_name, new_location_name=None, new_er_data=None, new_pmag_data=None):
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
        site.change_site(new_site_name, new_location, new_er_data, new_pmag_data)

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
        self.sites.remove(site)
        if site.location:
            site.location.sites.remove(site)
        for samp in site.samples:
            samp.site = ''
        del site

    def change_location(self, old_location_name, new_location_name, new_er_data=None, new_pmag_data=None):
        """
        Find actual data object for location with old_location_name.
        Then call Location class change method to update location name and data.
        """
        location = self.find_by_name(old_location_name, self.locations)
        if not location:
            print '-W- {} is not a currently existing location, so it cannot be updated.'.format(old_location_name)
            return False
        location.change_location(new_location_name, new_er_data, new_pmag_data)
        return location

    def add_location(self, location_name, er_data=None, pmag_data=None):
        """
        Create a Location object and add it to self.locations.
        """
        location = Location(location_name, self.data_model, er_data=er_data, pmag_data=pmag_data)
        self.locations.append(location)
        return location

    def delete_location(self, location_name):
        """
        Remove location with name location_name from self.locations.
        If the location had any sites, change site.location to "".
        """
        location = self.find_by_name(location_name, self.locations)
        sites = location.sites
        self.locations.remove(location)
        for site in sites:
            site.location = ''
        del location


    #def find_all_children(self, parent_item):
    #    """
    #
    #    ancestry = ['specimen', 'sample', 'site', 'location']
    #    child_types = {'sample': self.specimens, 'site': self.samples, 'location': self.sites}
    #    dtype = parent_item.dtype
    #    ind = ancestry.index(dtype)
    #    children = child_types[dtype]
    #
    #    if dtype in (1, 2, 3):
    #        pass


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
                location = Location(location_name, self.data_model)
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


    def get_er_magic_info(self, child_type, pmag_or_er='er', parent_type=None):
        """
        Read er_*.txt file.
        Parse information into dictionaries for each item.
        Then add it to the item object as object.er_data.
        """
        short_filename = "er_" + child_type + 's.txt'
        magic_file = os.path.join(self.WD, short_filename)
        magic_name = 'er_' + child_type + '_name'
        if not os.path.isfile(magic_file):
            print '-W- Could not find {} in your working directory {}'.format(short_filename, self.WD)
            return False
        # get the data from the appropriate er_*.txt file
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
                parent.remove_headers(parent.er_data)
            # if there should be a parent
            # (meaning there is a name for it and the child object should have a parent)
            # but none exists in the data model, go ahead and create that parent object.
            elif parent_name and parent_type and not parent:
                parent = parent_constructor(parent_name, data_model=self.data_model)
            # otherwise there is no parent and none can be created, so use an empty string
            else:
                parent = ''
            child = self.find_by_name(child_name, child_list)
            # if the child object does not exist yet in the data model
            if not child:
                child = child_constructor(child_name, parent_name, data=data_dict, data_model=self.data_model)
            # add in the appropriate data dictionary
            child.er_data = data_dict[child_name]
            child.remove_headers(child.er_data)

    def get_pmag_magic_info(self, child_type, parent_type=None):
        """
        Read pmag_*.txt file.
        Parse information into dictionaries for each item.
        Then add it to the item object as object.pmag_data.
        """
        short_filename = "pmag_" + child_type + 's.txt'
        magic_file = os.path.join(self.WD, short_filename)
        magic_name = 'er_' + child_type + '_name'
        if not os.path.isfile(magic_file):
            print '-W- Could not find {} in your working directory {}'.format(short_filename, self.WD)
            return False
        # get the data from the appropriate er_*.txt file
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
                parent.remove_headers(parent.pmag_data)
            # if there should be a parent
            # (meaning there is a name for it and the child object should have a parent)
            # but none exists in the data model, go ahead and create that parent object.
            elif parent_name and parent_type and not parent:
                parent = parent_constructor(parent_name, data_model=self.data_model)
            # otherwise there is no parent and none can be created, so use an empty string
            else:
                parent = ''
            child = self.find_by_name(child_name, child_list)
            # if the child object does not exist yet in the data model
            if not child:
                child = child_constructor(child_name, parent_name, data=data_dict, data_model=self.data_model)
            # add in the appropriate data dictionary
            child.pmag_data = data_dict[child_name]
            child.remove_headers(child.pmag_data)



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

    def __init__(self, name, dtype, data_model=None, er_data=None, pmag_data=None):#, headers={}):
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
        er_reqd_data = {key: '' for key in self.er_reqd_headers}
        pmag_reqd_data = {key: '' for key in self.pmag_reqd_headers}
        if er_data:
            self.er_data = self.combine_dicts(er_data, er_reqd_data)
        else:
            self.er_data = er_reqd_data
        if pmag_data:
            self.pmag_data = self.combine_dicts(pmag_data, pmag_reqd_data)
        else:
            self.pmag_data = pmag_reqd_data

        if dtype in ('sample', 'site'):
            self.age_reqd_headers, self.age_optional_headers = self.get_headers('er_ages')
            self.age_data = {key: '' for key in self.age_reqd_headers}
            self.remove_headers(self.age_data)

        self.remove_headers(self.er_data)
        self.remove_headers(self.pmag_data)

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

    def remove_headers(self, data_dict):
        for header in ['er_specimen_name', 'er_sample_name', 'er_site_name', 'er_location_name']:
            if header in data_dict.keys():
                data_dict.pop(header)

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

    


class Specimen(Pmag_object):

    """
    Specimen level object
    """
    def __init__(self, name, sample, data_model=None, er_data=None, pmag_data=None):
        dtype = 'specimen'
        super(Specimen, self).__init__(name, dtype, data_model, er_data, pmag_data)
        self.sample = sample or ""

    def change_specimen(self, new_name, new_sample=None, er_data=None, pmag_data=None):
        self.name = new_name
        if new_sample:
            self.sample.specimens.remove(self)
            self.sample = new_sample
            self.sample.specimens.append(self)
        if er_data:
            self.er_data = self.combine_dicts(er_data, self.er_data)
        if pmag_data:
            self.pmag_data = self.combine_dicts(pmag_data, self.pmag_data)    


class Sample(Pmag_object):

    """
    Sample level object
    """

    def __init__(self, name, site, data_model=None, er_data=None, pmag_data=None):
        dtype = 'sample'
        super(Sample, self).__init__(name, dtype, data_model, er_data, pmag_data)
        self.specimens = []
        self.site = site or ""

    def change_sample(self, new_name, new_site=None, er_data=None, pmag_data=None):
        self.name = new_name
        if new_site:
            if self.site:
                self.site.samples.remove(self)
            self.site = new_site
            self.site.samples.append(self)
        if er_data:
            self.er_data = self.combine_dicts(er_data, self.er_data)
        if pmag_data:
            self.pmag_data = self.combine_dicts(pmag_data, self.pmag_data)    


class Site(Pmag_object):

    """
    Site level object
    """

    def __init__(self, name, location, data_model=None, er_data=None, pmag_data=None):
        dtype = 'site'
        super(Site, self).__init__(name, dtype, data_model, er_data, pmag_data)
        self.samples = []
        self.location = location or ""

    def change_site(self, new_name, new_location=None, new_er_data=None, new_pmag_data=None):
        self.name = new_name
        if new_location:
            self.location = new_location
        if new_er_data:
            self.er_data = self.combine_dicts(new_er_data, self.er_data)
        if new_pmag_data:
            self.pmag_data = self.combine_dicts(new_pmag_data, self.pmag_data)    


class Location(Pmag_object):

    """
    Location level object
    """

    def __init__(self, name, data_model=None, er_data=None, pmag_data=None):
        dtype = 'location'
        super(Location, self).__init__(name, dtype, data_model, er_data, pmag_data)
        self.sites = []

    def change_location(self, new_name, new_er_data=None, new_pmag_data=None):
        self.name = new_name
        if new_er_data:
            self.er_data = self.combine_dicts(new_er_data, self.er_data)




if __name__ == '__main__':
    wd = pmag.get_named_arg_from_sys('-WD', default_val=os.getcwd())
    builder = ErMagicBuilder(wd)
    builder.get_data()


    #specimen = Specimen('spec1', 'specimen')
    #for spec in builder.specimens:
        #print str(spec) + ' belongs to ' + str(spec.sample) + ' belongs to ' + str(spec.sample.site) + ' belongs to ' + str(spec.sample.site.location)
    #for site in builder.sites:
    #    print site, site.samples
    #    print '--'


# Random helper methods that MIGHT belong in pmag.py

def put_list_value_first(lst, first_value):
    if first_value in lst:
        lst.remove(first_value)
        lst[:0] = [first_value]

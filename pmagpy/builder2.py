#!/usr/bin/env python

"""
Module for building or reading in specimen, sample, site, and location data.
"""
from __future__ import print_function

from builtins import str
from builtins import range
from builtins import object
import os
# import time
import pmagpy.pmag as pmag
import pmagpy.validate_upload2 as validate_upload


class ErMagicBuilder(object):
    """
    more object oriented builder
    """

    def __init__(self, WD, data_model=None):
        self.WD = WD
        self.measurements = []
        self.specimens = []
        self.samples = []
        self.sites = []
        self.locations = []
        self.results = []
        self.write_ages = False
        self.ancestry = [None, 'specimen', 'sample', 'site', 'location', None]
        #
        self.double = ['magic_method_codes', 'specimen_description',
                       'sample_description', 'site_description']
        #
        self.incl_pmag_data = set(['result'])
        if not data_model:
            self.data_model = validate_upload.get_data_model()
        else:
            self.data_model = data_model
        self.data_lists = {'specimen': [self.specimens, Specimen, self.add_specimen],
                           'sample': [self.samples, Sample, self.add_sample],
                           'site': [self.sites, Site, self.add_site],
                           'location': [self.locations, Location, self.add_location],
                           'age': [self.sites, Site, self.add_site],
                           'result': [self.results, Result, self.add_result],
                           'measurement': [self.measurements, Measurement, self.add_measurement]}
        self.add_methods = {'specimen': self.add_specimen, 'sample': self.add_sample,
                            'site': self.add_site, 'location': self.add_location,
                            'age': None, 'result': self.add_result}
        self.update_methods = {'specimen': self.change_specimen, 'sample': self.change_sample,
                               'site': self.change_site, 'location': self.change_location,
                               'age': self.change_age, 'result': self.change_result}
        self.delete_methods = {'specimen': self.delete_specimen, 'sample': self.delete_sample,
                               'site': self.delete_site, 'location': self.delete_location,
                               'age': None, 'result': self.delete_result}
        # actual is at position 0, reqd is at position 1, optional at position 2
        self.headers = {
            'measurement': {'er': [[], [], []], 'pmag': [[], [], []]},

            'specimen': {'er': [[], [], []], 'pmag': [[], [], []]},

            'sample': {'er': [[], [], []], 'pmag': [[], [], []]},

            'site': {'er': [[], [], []], 'pmag': [[], [], []]},

            'location': {'er': [[], [], []], 'pmag': [[], [], []]},

            'age': {'er': [[], [], []], 'pmag': [[], [], []]},

            'result': {'er': [[], [], []], 'pmag': [[], [], []]}
        }
        self.first_age_headers = ['er_citation_names', 'magic_method_codes', 'age_unit']
        self.age_type = 'site'

    def make_name_list(self, obj_list):
        name_list = []
        for obj in obj_list:
            try:
                name_list.append(obj.name)
            except AttributeError:
                if obj:
                    name_list.append(obj)
                else:
                    name_list.append('')
        return name_list

    def get_name(self, pmag_object, *args):
        for arg in args:
            try:
                pmag_object = pmag_object.__getattribute__(arg)
            except AttributeError:
                return ''
        return pmag_object


    def find_by_name(self, item_name, items_list, name_list=None):
        """
        Return item from items_list with name item_name.
        """
        if not name_list:
            names = [item.name for item in items_list if item]
        else:
            names = name_list
        if item_name in names:
            ind = names.index(item_name)
            return items_list[ind]
        return False

    def find_or_create_by_name(self, item_name, items_list, item_type):
        """
        See if item with item_name exists in item_list.
        If not, create that item.
        Either way, return an item of type item_type.
        """
        item = self.find_by_name(item_name, items_list)
        if not item:
            item = self.data_lists[item_type][2](item_name, None)
        return item

    def init_default_headers(self):
        """
        initialize default required headers.
        if there were any pre-existing headers, keep them also.
        """
        if not self.data_model:
            self.data_model = validate_upload.get_data_model()
            if not self.data_model:
                print("Can't access MagIC-data-model at the moment.\nIf you are working offline, make sure MagIC-data-model.txt is in your PmagPy directory (or download it from https://github.com/ltauxe/PmagPy and put it in your PmagPy directory).\nOtherwise, check your internet connection")
                return False

        # actual is at position 0, reqd is at position 1, optional at position 2
        self.headers['measurement']['er'][1], self.headers['measurement']['er'][2] = self.get_headers('magic_measurements')
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
        reqd_headers = sorted([header for header in list(data_dict.keys()) if data_dict[header]['data_status'] == 'Required'])
        optional_headers = sorted([header for header in list(data_dict.keys()) if data_dict[header]['data_status'] != 'Required'])
        return reqd_headers, optional_headers

    def init_actual_headers(self):
        def headers(data_list, reqd_er_headers, reqd_pmag_headers):
            if data_list:
                er_header, pmag_header = set([]), set([])
                for item in data_list:
                    for key in list(item.er_data.keys()):
                        er_header.add(key)
                    for key in list(item.pmag_data.keys()):
                        pmag_header.add(key)
                ## old non-thorough way
                #er_header = data_list[0].er_data.keys()
                #pmag_header = data_list[0].pmag_data.keys()
                er_header = remove_list_headers(er_header)
                pmag_header = remove_list_headers(pmag_header)
            else:
                er_header = remove_list_headers(reqd_er_headers)
                pmag_header = remove_list_headers(reqd_pmag_headers)
            return list(er_header), list(pmag_header)

        self.headers['measurement']['er'][0], self.headers['measurement']['pmag'][0] = headers(self.measurements, self.headers['measurement']['er'][1], self.headers['measurement']['pmag'][1])

        self.headers['specimen']['er'][0], self.headers['specimen']['pmag'][0] = headers(self.specimens, self.headers['specimen']['er'][1], self.headers['specimen']['pmag'][1])

        self.headers['sample']['er'][0], self.headers['sample']['pmag'][0] = headers(self.samples, self.headers['sample']['er'][1], self.headers['sample']['pmag'][1])

        self.headers['site']['er'][0], self.headers['site']['pmag'][0] = headers(self.sites, self.headers['site']['er'][1], self.headers['site']['pmag'][1])

        self.headers['location']['er'][0], self.headers['location']['pmag'][0] = headers(self.locations, self.headers['location']['er'][1], self.headers['location']['pmag'][1])

        age_list = self.data_lists[self.age_type][0]
        if age_list:
            age_headers = []
            for item in age_list:
                for header in list(item.age_data.keys()):
                    if header not in age_headers:
                        age_headers.append(header)
            self.headers['age']['er'][0] = age_headers
        else:
            self.headers['age']['er'][0] = remove_list_headers(self.headers['age']['er'][1])
        # make sure that some recommended but not required age headers are added in
        for head in self.first_age_headers:
            if head not in self.headers['age']['er'][0]:
                self.headers['age']['er'][0].append(head)

        self.headers['result']['er'][0], self.headers['result']['pmag'][0] = headers(self.results, self.headers['result']['er'][1], self.headers['result']['pmag'][1])

    def add_measurement(self, exp_name, meas_num, spec_name=None, er_data=None, pmag_data=None):
        """
        Find actual data object for specimen.
        Then create a measurement belonging to that specimen and add it to the data object
        """
        specimen = self.find_by_name(spec_name, self.specimens)
        measurement = Measurement(exp_name, meas_num, specimen, er_data)
        self.measurements.append(measurement)
        return measurement

    def change_specimen(self, old_spec_name, new_spec_name,
                        new_sample_name=None, new_er_data=None, new_pmag_data=None,
                        replace_data=False):
        """
        Find actual data objects for specimen and sample.
        Then call Specimen class change method to update specimen name and data.
        """
        specimen = self.find_by_name(old_spec_name, self.specimens)
        if not specimen:
            print('-W- {} is not a currently existing specimen, so cannot be updated'.format(old_spec_name))
            return False
        if new_sample_name:
            new_sample = self.find_by_name(new_sample_name, self.samples)
            if not new_sample:
                print("""-W- {} is not a currently existing sample.
Creating a new sample named: {} """.format(new_sample_name, new_sample_name))
                new_sample = self.add_sample(new_sample_name)
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
        return []

    def add_specimen(self, spec_name, samp_name=None, er_data=None, pmag_data=None):
        """
        Create a Specimen object and add it to self.specimens.
        If a sample name is provided, add the specimen to sample.specimens as well.
        """
        if samp_name:
            sample = self.find_by_name(samp_name, self.samples)
            if not sample:
                print("""-W- {} is not a currently existing sample.
Creating a new sample named: {} """.format(samp_name, samp_name))
                sample = self.add_sample(samp_name)
        else:
            sample = None

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
            print('-W- {} is not a currently existing sample, so it cannot be updated'.format(old_samp_name))
            return False
        if new_site_name:
            new_site = self.find_by_name(new_site_name, self.sites)
            if not new_site:
                print("""-W- {} is not a currently existing site.
Adding site named: {}""".format(new_site_name, new_site_name))#sample.site or '*empty*', sample)
                new_site = self.add_site(new_site_name)
        else:
            new_site = None
        sample.change_sample(new_samp_name, new_site, new_er_data, new_pmag_data, replace_data)
        return sample

    def add_sample(self, samp_name, site_name=None, er_data=None, pmag_data=None):
        """
        Create a Sample object and add it to self.samples.
        If a site name is provided, add the sample to site.samples as well.
        """
        if site_name:
            site = self.find_by_name(site_name, self.sites)
            if not site:
                print("""-W- {} is not a currently existing site.
Creating a new site named: {} """.format(site_name, site_name))
                site = self.add_site(site_name)
        else:
            site = None
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
        return specimens


    def change_age(self, old_name, new_age_data=None, item_type='site', replace_data=False):
        item = self.find_by_name(old_name, self.data_lists[item_type][0])
        if replace_data:
            default_age_data = {key: '' for key in self.headers['age']['er'][1]}
            item.age_data = combine_dicts(new_age_data, default_age_data)
        else:
            item.age_data = combine_dicts(new_age_data, item.age_data)
        return item

    def change_site(self, old_site_name, new_site_name, new_location_name=None,
                    new_er_data=None, new_pmag_data=None, replace_data=False):
        """
        Find actual data objects for site and location.
        Then call the Site class change method to update site name and data.
        """
        site = self.find_by_name(old_site_name, self.sites)
        if not site:
            print('-W- {} is not a currently existing site, so it cannot be updated.'.format(old_site_name))
            return False
        if new_location_name:
            if site.location:
                old_location = self.find_by_name(site.location.name, self.locations)
                if old_location:
                    old_location.sites.remove(site)
            new_location = self.find_by_name(new_location_name, self.locations)
            if not new_location:
                print("""-W- {} is not a currently existing location.
Adding location with name: {}""".format(new_location_name, new_location_name))
                new_location = self.add_location(new_location_name)
            new_location.sites.append(site)
        else:
            new_location = None
        ## check all declinations/azimuths/longitudes in range 0=>360.
        #for key, value in new_er_data.items():
        #    new_er_data[key] = pmag.adjust_to_360(value, key)
        site.change_site(new_site_name, new_location, new_er_data, new_pmag_data, replace_data)
        return site

    def add_site(self, site_name, location_name=None, er_data=None, pmag_data=None):
        """
        Create a Site object and add it to self.sites.
        If a location name is provided, add the site to location.sites as well.
        """
        if location_name:
            location = self.find_by_name(location_name, self.locations)
            if not location:
                location = self.add_location(location_name)
        else:
            location = None

        ## check all declinations/azimuths/longitudes in range 0=>360.
        #for key, value in er_data.items():
        #    er_data[key] = pmag.adjust_to_360(value, key)

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
        samples = site.samples
        for samp in samples:
            samp.site = ''
        del site
        return samples

    def change_location(self, old_location_name, new_location_name, new_parent_name=None,
                        new_er_data=None, new_pmag_data=None, replace_data=False):
        """
        Find actual data object for location with old_location_name.
        Then call Location class change method to update location name and data.
        """
        location = self.find_by_name(old_location_name, self.locations)
        if not location:
            print('-W- {} is not a currently existing location, so it cannot be updated.'.format(old_location_name))
            return False
        location.change_location(new_location_name, new_er_data, new_pmag_data, replace_data)
        return location

    def add_location(self, location_name, parent_name=None, er_data=None, pmag_data=None):
        """
        Create a Location object and add it to self.locations.
        """
        if not location_name:
            return False
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
            if site:
                site.location = ''
        del location
        return sites

    def add_age(self, item_name, age_data):
        items_list = self.data_lists[self.age_type][0]
        item = self.find_by_name(item_name, items_list)
        if not item:
            msg = '-W- You have tried to add age data for {}, but there is no {} by that name'.format(item_name, self.age_type)
            print(msg)
            return False
        else:
            required = {key: '' for key in self.headers['age']['er'][1]}
            item.age_data = combine_dicts(age_data, required)
            self.write_ages = True

    def delete_age(self, item_name):
        pass

    def add_result(self, result_name, spec_names=None, samp_names=None, site_names=None, loc_names=None, pmag_data=None):
        specimens, samples, sites, locations = None, None, None, None
        if spec_names:
            specimens = [self.find_by_name(name, self.specimens) for name in spec_names]
        if samp_names:
            samples = [self.find_by_name(name, self.samples) for name in samp_names]
        if site_names:
            sites = [self.find_by_name(name, self.sites) for name in site_names]
        if loc_names:
            locations = [self.find_by_name(name, self.locations) for name in loc_names]
        result = Result(result_name, specimens, samples, sites, locations, pmag_data, self.data_model)
        self.results.append(result)
        return result

    def delete_result(self, result_name):
        result = self.find_by_name(result_name, self.results)
        if result:
            self.results.remove(result)
            del result

    def change_result(self, old_result_name, new_result_name, new_er_data=None,
                      new_pmag_data=None, spec_names=None, samp_names=None,
                      site_names=None, loc_names=None, replace_data=False):
        """
        Find actual data object for result with old_result_name.
        Then call Result class change method to update result name and data.
        """
        result = self.find_by_name(old_result_name, self.results)
        if not result:
            msg = '-W- {} is not a currently existing result, so it cannot be updated.'.format(old_result_name)
            print(msg)
            return False
        else:
            specimens, samples, sites, locations = None, None, None, None
            if spec_names:
                specimens = [self.find_or_create_by_name(spec, self.specimens, 'specimen') for spec in spec_names]
            if samp_names:
                samples = [self.find_or_create_by_name(samp, self.samples, 'sample') for samp in samp_names]
            if site_names:
                sites = [self.find_or_create_by_name(site, self.sites, 'site') for site in site_names]
            if loc_names:
                locations = [self.find_or_create_by_name(loc, self.locations, 'location') for loc in loc_names]

            result.change_result(new_result_name, new_pmag_data, specimens, samples,
                                 sites, locations, replace_data)
            return result

    ## Methods for reading in data

    def get_data(self):
        """
        attempt to read measurements file in working directory.
        """
        meas_file = os.path.join(self.WD, 'magic_measurements.txt')
        if not os.path.isfile(meas_file):
            print("-I- No magic_measurements.txt file")
            return {}
        try:
            meas_data, file_type = pmag.magic_read(meas_file)
        except IOError:
            print("-I- No magic_measurements.txt file")
            return {}
        if file_type == 'bad_file':
            print("-E- ERROR: Can't read magic_measurements.txt file. File is corrupted.")

        old_specimen_name = ''
        #start_time = time.time()
        meas_name_list = [measurement.name for measurement in self.measurements]

        for rec in meas_data:
            # get citation information
            citation = rec.get('er_citation_names', 'This study')
            if 'This study' not in citation:
                citation = citation.strip() + ':This study'
            er_data = {'er_citation_names': citation}
            pmag_data = {'er_citation_names': 'This study'}
            specimen_name = rec["er_specimen_name"]
            # ignore measurement if there is no specimen
            if specimen_name == "" or specimen_name == " ":
                continue
            # if we've moved onto a new specimen, make sure a sample/site/location
            # exists for that specimen
            if specimen_name != old_specimen_name:
                sample_name = rec["er_sample_name"]
                site_name = rec["er_site_name"]
                location_name = rec["er_location_name"]

                # add items and parents
                location = self.find_by_name(location_name, self.locations)
                if location_name and not location:
                    location = self.add_location(location_name, er_data=er_data,
                                                 pmag_data=pmag_data)
                site = self.find_by_name(site_name, self.sites)
                if site_name and not site:
                    site = self.add_site(site_name, location_name,
                                         er_data, pmag_data)
                sample = self.find_by_name(sample_name, self.samples)
                if sample_name and not sample:
                    sample = self.add_sample(sample_name, site_name,
                                             er_data, pmag_data)
                specimen = self.find_by_name(specimen_name, self.specimens)
                if specimen_name and not specimen:
                    specimen = self.add_specimen(specimen_name, sample_name,
                                                 er_data, pmag_data)

                # add child_items
                if sample and not self.find_by_name(specimen_name, sample.specimens):
                    sample.specimens.append(specimen)
                if site and not self.find_by_name(sample_name, site.samples):
                    site.samples.append(sample)
                if location and not self.find_by_name(site_name, location.sites):
                    location.sites.append(site)

            exp_name = rec['magic_experiment_name']
            meas_num = rec['measurement_number']

            meas_name = exp_name + '_' + str(meas_num)
            measurement = self.find_by_name(meas_name, self.measurements, meas_name_list)
            if not measurement:
                self.add_measurement(exp_name, meas_num, specimen.name, rec)
                meas_name_list.append(meas_name)

            old_specimen_name = specimen_name
        #end_time = time.time() - start_time

    def get_all_magic_info(self):
        self.get_data()
        for child, parent in [('specimen', 'sample'), ('sample', 'site'),
                              ('site', 'location'), ('location', '')]:
            print('-I- Getting {} info'.format(child))
            self.get_magic_info(child, parent, 'er')
            if self.get_magic_info(child, parent, 'pmag'):
                self.incl_pmag_data.add(child)
        self.get_age_info()
        self.get_results_info()

    def get_magic_info(self, child_type, parent_type=None, attr='er',
                       filename=None, sort_by_file_type=False):
        """
        Read er_*.txt or pmag_*.txt file.
        If no filename is provided, use er_* or pmag_* file in WD.
        If sort_by_file_type, use file header to determine child, parent types,
        instead of passing those in as arguments.
        Once file is open, parse information into dictionaries for each item.
        If the item does not yet exist, add it to the builder data object.
        Then add info to the item object as object.er_data or object.pmag_data.
        """
        parent = ''
        grandparent_type = None
        magic_name = 'er_' + child_type + '_name'
        expected_item_type = child_type
        if not filename:
            short_filename = attr + '_' + child_type + 's.txt'
            magic_file = os.path.join(self.WD, short_filename)
        else:
            short_filename = os.path.split(filename)[1]
            magic_file = filename
            attr = short_filename.split('_')[0]
        print('-I- Attempting to read {}'.format(magic_file))
        if not os.path.isfile(magic_file):
            print('-W- Could not find {}'.format(magic_file))
            return False
        # get the data from the appropriate .txt file

        data_dict, header, file_type = self.read_magic_file(magic_file, magic_name,
                                                            sort_by_file_type=sort_by_file_type)
        if not data_dict:
            print('-W- Could not read in file: {}.\n    Make sure it is a MagIC-format file'.format(magic_file))
            return False

        item_type = file_type.split('_')[1][:-1]
        # if a file was named wrong, use the type of data that is actually in that file
        if item_type != expected_item_type:
            print('-W- Expected data of type: {} but instead got: {}'.format(expected_item_type,
                                                                             item_type))
            print('-W- Using type: {}'.format(item_type))
            if item_type == 'age':
                self.get_age_info(filename)
                return 'age'
            child_type = item_type
            magic_name = 'er_' + child_type + '_name'
            ind = self.ancestry.index(child_type)
            parent_type = self.ancestry[ind+1]
            if item_type != 'location':
                grandparent_type = self.ancestry[ind+2]
            else:
                grandparent_type = ''
        if not grandparent_type:
            ind = self.ancestry.index(child_type)
            try:
                grandparent_type = self.ancestry[ind+2]
            except IndexError:
                grandparent_type = None
        child_list, child_class, child_constructor = self.data_lists[child_type]

        if parent_type:
            parent_list, parent_class, parent_constructor = self.data_lists[parent_type]
        else:
            parent_list, parent_name = None, None
        for child_name in data_dict:
            # if there is a possible parent, try to find parent object in the data model
            if parent_type:
                parent_name = data_dict[child_name].get('er_' + parent_type + '_name', '')
                parent = self.find_by_name(parent_name, parent_list)
                if parent:
                    remove_dict_headers(parent.er_data)
                    remove_dict_headers(parent.pmag_data)
            # if there should be a parent
            # (meaning there is a name for it and the child object should have a parent)
            # but none exists in the data model, go ahead and create that parent object.
            if parent_name and parent_type and not parent:
                # try to get grandparent
                grandparent = None
                grandparent_name = None
                if grandparent_type:
                    grandparent_list, grandparent_class, grandparent_constructor = self.data_lists[grandparent_type]
                    grandparent_name = data_dict[child_name]['er_' + grandparent_type + '_name']
                    grandparent = self.find_by_name(grandparent_name, grandparent_list)
                    if grandparent_name and not grandparent:
                        grandparent = grandparent_constructor(grandparent_name, None)
                parent = parent_constructor(parent_name, grandparent_name)
            # otherwise there is no parent and none can be created, so use an empty string
            elif not parent:
                parent_name = None
                parent = ''
            child = self.find_by_name(child_name, child_list)
            # if the child object does not exist yet in the data model
            if not child:
                child = child_constructor(child_name, parent_name)
            else:
                # bind parent to child and child to parent
                if parent:
                    child.set_parent(parent)
                if parent and (child not in parent.children):
                    parent.add_child(child)

            # add in the appropriate data dictionary to the child object
            if attr == 'er':
                self.update_methods[child_type](child_name, child_name, parent_name,
                                                new_er_data=data_dict[child_name])
            else:
                self.update_methods[child_type](child_name, child_name, parent_name,
                                                new_pmag_data=data_dict[child_name])
            # old way
            #child.__setattr__(attr + '_data', data_dict[child_name])
            remove_dict_headers(child.er_data)
            remove_dict_headers(child.pmag_data)
            #
        return child_type

    def get_age_info(self, filename=None):
        """
        Read er_ages.txt file.
        Parse information into dictionaries for each site/sample.
        Then add it to the site/sample object as site/sample.age_data.
        """
        # use filename if provided, otherwise find er_ages.txt in WD
        if not filename:
            short_filename = 'er_ages.txt'
            magic_file = os.path.join(self.WD, short_filename)
        else:
            magic_file = filename
        if not os.path.isfile(magic_file):
            print('-W- Could not find {}'.format(magic_file))
            return False

        data_dict, header, file_type = self.read_magic_file(magic_file, 'by_line_number')
        # if provided file is not an age_file,
        # try to read it in as whatever type of file it actually is
        if file_type != 'er_ages':
            item_type = file_type.split('_')[1][:-1]
            self.get_magic_info(item_type, filename=filename, sort_by_file_type=True)
            return file_type

        # if it is an age file,
        # determine level for each age and assign it to the appropriate pmag object
        for item_dict in list(data_dict.values()):
            item_type = None
            for dtype in ['specimen', 'sample', 'site', 'location']:
                header_name = 'er_' + dtype + '_name'
                if header_name in list(item_dict.keys()):
                    if item_dict[header_name]:
                        item_type = dtype
                        item_name = item_dict[header_name].strip()
                        break
            if not item_type:
                print('-W- You must provide a name for your age')
                print('    These data:\n{}\n    will not be imported'.format(item_dict))
                continue
            items_list = self.data_lists[item_type][0]
            item = self.find_by_name(item_name, items_list)
            if not item:
                ## the following code creates any item in er_ages that does not exist already
                ## however, we may not WANT that behavior
                print("""-I- A {} named {} in your age file was not found in the data object:
    Now initializing {} {}""".format(item_type, item_name, item_type, item_name))
                ind = self.ancestry.index(item_type)
                parent_type = self.ancestry[ind+1]
                parent_header, parent_constructor = None, None
                if parent_type:
                    parent_list, parent_class, parent_constructor = self.data_lists[parent_type]
                    parent_header = 'er_' + parent_type + '_name'
                parent_name = item_dict.get(parent_header, '')
                parent = self.find_by_name(parent_name, parent_list)
                # if the parent item doesn't exist, and should, create it
                if parent_name and not parent:
                    print("""-I- A {} named {} in your age file was not found in the data object:
    Now initializing {} {}""".format(parent_type, parent_name, parent_type, parent_name))
                    parent = parent_constructor(parent_name, None)
                item_constructor = self.data_lists[item_type][2]
                if not parent:
                    parent_name = None
                item = item_constructor(item_name, parent_name)
            # add the age data to the object
            item.age_data = remove_dict_headers(item_dict)
        # note that data is available to write
        self.write_ages = True
        return file_type

    def get_results_info(self, filename=None):
        """
        Read pmag_results.txt file.
        Parse information into dictionaries for each item.
        Then add it to the item object as object.results_data.
        """
        if not filename:
            short_filename = "pmag_results.txt"
            magic_file = os.path.join(self.WD, short_filename)
        else:
            magic_file = filename
        if not os.path.isfile(magic_file):
            print('-W- Could not find {} in your working directory {}'.format(short_filename, self.WD))
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

        for num, result in list(data_dict.items()):
            name, specimens, samples, sites, locations = None, None, None, None, None
            for key, value in list(result.items()):
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
                if header_name in list(result.keys()):
                    result.pop(header_name)
            if not name:
                name = num
            result_item = self.find_by_name(name, self.results)
            if not result_item:
                result_item = Result(name, specimens, samples, sites, locations, result, self.data_model)
            else:
                print('-W- Two or more results with name: {} found in your result file.\n    Taking only the first.'.format(name))
            if result_item and result_item not in self.results:
                self.results.append(result_item)

    def read_magic_file(self, path, sort_by_this_name, sort_by_file_type=False):
        """
        read a magic-formatted tab-delimited file.
        return a dictionary of dictionaries, with this format:
        {'Z35.5a': {'specimen_weight': '1.000e-03', 'er_citation_names': 'This study', 'specimen_volume': '', 'er_location_name': '', 'er_site_name': 'Z35.', 'er_sample_name': 'Z35.5', 'specimen_class': '', 'er_specimen_name': 'Z35.5a', 'specimen_lithology': '', 'specimen_type': ''}, ....}
        """
        DATA = {}
        with open(path, 'r') as fin:
            lines = list(fin.readlines())
        first_line = lines[0]
        if not first_line:
            return False, None, 'empty_file'
        if first_line[0] == "s" or first_line[1] == "s":
            delim = ' '
        elif first_line[0] == "t" or first_line[1] == "t":
            delim = '\t'
        else:
            print('-W- error reading ', path)
            return False, None, 'bad_file'

        file_type = first_line.strip('\n').split(delim)[1]
        if sort_by_file_type:
            item_type = file_type.split('_')[1][:-1]
            if item_type == 'age':
                sort_by_this_name = "by_line_number"
            else:
                sort_by_this_name = 'er_' + item_type + '_name'
        line = lines[1]
        header = line.strip('\n').split(delim)
        counter = 0
        for line in lines[2:]:
            tmp_data = {}
            tmp_line = line.strip('\n').split(delim)
            for i in range(len(header)):
                if i < len(tmp_line):
                    tmp_data[header[i]] = tmp_line[i].strip()
                else:
                    tmp_data[header[i]] = ""
            if sort_by_this_name == "by_line_number":
                DATA[counter] = tmp_data
                counter += 1
            else:
                if tmp_data[sort_by_this_name] != "":
                    DATA[tmp_data[sort_by_this_name]] = tmp_data
        return DATA, header, file_type


    def write_measurements_file(self):
        filename = os.path.join(self.WD, 'magic_measurements.txt')
        magic_outfile = open(filename, 'w')
        measurement_headers = self.headers['measurement']['er'][0]
        measurement_headers[:0] = ['er_specimen_name', 'er_sample_name', 'er_site_name',
                                   'er_location_name', 'magic_experiment_name', 'measurement_number']
        specimen_names = self.make_name_list(self.specimens)
        meas_strings = []
        for meas in self.measurements:
            meas_string = []
            # if a specimen has been deleted,
            # do not record any measurements for that specimen
            if not meas.specimen.name in specimen_names or not meas.specimen.name:
                continue

            for header in measurement_headers:
                if header == 'er_specimen_name':
                    val = self.get_name(meas, 'specimen', 'name')
                elif header == 'er_sample_name':
                    val = self.get_name(meas, 'specimen', 'sample', 'name')
                elif header == 'er_site_name':
                    val = self.get_name(meas, 'specimen', 'sample', 'site', 'name')
                elif header == 'er_location_name':
                    val = self.get_name(meas, 'specimen', 'sample', 'site', 'location', 'name')
                elif header == 'magic_experiment_name':
                    val = meas.experiment_name
                elif header == 'measurement_number':
                    val = meas.meas_number
                else:
                    val = meas.er_data.get(header, '')
                meas_string.append(val)
            meas_string = '\t'.join(meas_string)
            meas_strings.append(meas_string)
        # write data to file
        magic_outfile.write('tab\tmagic_measurements\n')
        header_string = '\t'.join(measurement_headers)
        magic_outfile.write(header_string + '\n')
        for string in meas_strings:
            magic_outfile.write(string + '\n')
        magic_outfile.close()
        return True


    ### Methods for writing data ###
    def write_files(self):
        """
        write all data out into er_* and pmag_* files as appropriate
        """
        warnings = self.validate_data()

        print('-I- Writing all saved data to files')
        if self.measurements:
            self.write_measurements_file()
        for dtype in ['specimen', 'sample', 'site']:
            if self.data_lists[dtype][0]:
                do_pmag = dtype in self.incl_pmag_data
                self.write_magic_file(dtype, do_er=True, do_pmag=do_pmag)
                if not do_pmag:
                    pmag_file = os.path.join(self.WD, 'pmag_' + dtype + 's.txt')
                    if os.path.isfile(pmag_file):
                        os.remove(pmag_file)

        if self.locations:
            self.write_magic_file('location', do_er=True, do_pmag=False)

        self.write_age_file()

        if self.results:
            self.write_result_file()

        if warnings:
            print('-W- ' + str(warnings))
            return False, warnings

        return True, None


    def write_magic_file(self, dtype, do_er=True, do_pmag=True):
        if dtype == 'location':
            do_pmag = False
        # make header
        add_headers = []
        self.ancestry_ind = self.ancestry.index(dtype)
        for i in range(self.ancestry_ind, len(self.ancestry) - 1):
            add_headers.append('er_' + self.ancestry[i] + "_name")
        er_actual_headers = sorted(self.headers[dtype]['er'][0])
        pmag_actual_headers = sorted(self.headers[dtype]['pmag'][0])
        # clean up pmag header: write pmag method code header without '++'
        for pmag_head in pmag_actual_headers[:]:
            if '++' in pmag_head:
                pmag_actual_headers.remove(pmag_head)
                pmag_actual_headers.append(pmag_head[:-2])
        er_full_headers = add_headers[:]
        er_full_headers.extend(er_actual_headers)
        pmag_full_headers = add_headers[:]
        pmag_full_headers.extend(pmag_actual_headers)

        er_start = 'er_' + dtype + 's'
        pmag_start = 'pmag_' + dtype + 's'
        er_strings = []
        pmag_strings = []
        # get sorted list of all relevant items
        items_list = sorted(self.data_lists[dtype][0], key=lambda item: item.name)
        # fill in location begin/end lat/lon if those values are not present
        if dtype == 'location':
            d = self.get_min_max_lat_lon(items_list)
            for item in items_list[:]:
                for header in ['location_begin_lat', 'location_begin_lon',
                               'location_end_lat', 'location_end_lon']:
                    if not item.er_data[header]:
                        item.er_data[header] = d[item.name][header]
        # go through items and collect necessary data
        for item in items_list[:]:
            # get an item's ancestors
            ancestors = self.get_ancestors(item)
            er_string = []
            pmag_string = []
            # if item has no pmag_data at all, do not write it to pmag_file
            do_this_pmag = True
            temp_pmag_data = list(item.pmag_data.values())
            if 'This study' in temp_pmag_data:
                temp_pmag_data.remove('This study')
            if not any(temp_pmag_data):
                do_this_pmag = False
            # compile er data
            if do_er:
                er_string.append(item.name)
                for ancestor in ancestors:
                    er_string.append(ancestor)
                for key in er_actual_headers:
                    try:
                        add_string = str(item.er_data[key])
                    except KeyError:
                        add_string = ''
                        item.er_data[key] = ''
                    if key == 'er_citation_names' and not add_string.strip('\t'):
                        add_string = 'This study'
                    er_string.append(add_string)
                er_string = '\t'.join(er_string)
                er_strings.append(er_string)
            # if we are writing a pmag file AND this particular item has pmag data,
            # compile this item's pmag data
            if do_pmag and do_this_pmag:
                pmag_string.append(item.name)
                for ancestor in ancestors:
                    pmag_string.append(ancestor)
                # get an item's descendents (only req'd for pmag files)
                descendents = self.get_descendents(item)
                more_headers = []
                more_strings = []
                # add in appropriate descendents
                possible_types = ['specimen', 'sample', 'site']
                for num, descendent_list in enumerate(descendents):
                    item_string = get_item_string(descendent_list)
                    more_strings.append(item_string)
                    more_headers.append('er_' + possible_types[num] + '_names')
                ind = len(pmag_string)
                pmag_string.extend(more_strings)
                if more_headers == pmag_full_headers[ind:ind+len(more_strings)]:
                    pass
                else:
                    pmag_full_headers[ind:ind] = more_headers
                # write out all needed values
                for key in pmag_actual_headers:
                    try:
                        add_string = item.pmag_data[key]
                    except KeyError:
                        add_string = ''
                        item.pmag_data[key] = ''
                    # add default values
                    if key == 'er_citation_names' and not add_string.strip('\t'):
                        add_string = 'This study'
                    pmag_string.append(str(add_string))
                pmag_string = '\t'.join(pmag_string)
                pmag_strings.append(pmag_string)
        # write acutal pmag file with all collected data
        pmag_header_string = '\t'.join(pmag_full_headers)
        pmag_outfile = ''
        if do_pmag:
            pmag_outfile = open(os.path.join(self.WD, pmag_start + '.txt'), 'w')
            pmag_outfile.write('tab\t' + pmag_start + '\n')
            pmag_outfile.write(pmag_header_string + '\n')
            for string in pmag_strings:
                pmag_outfile.write(string + '\n')
            pmag_outfile.close()
        # write acutal er file with all collected data
        er_header_string = '\t'.join(er_full_headers)
        er_outfile = ''
        if do_er:
            er_outfile = open(os.path.join(self.WD, er_start + '.txt'), 'w')
            er_outfile.write('tab\t' + er_start + '\n')
            er_outfile.write(er_header_string + '\n')
            for string in er_strings:
                er_outfile.write(string + '\n')
            er_outfile.close()
        return er_outfile, pmag_outfile

    def write_result_file(self):
        actual_headers = sorted(self.headers['result']['pmag'][0])
        add_headers = ['pmag_result_name', 'er_specimen_names', 'er_sample_names',
                       'er_site_names', 'er_location_names']
        full_headers = add_headers[:]
        full_headers.extend(actual_headers)
        header_string = '\t'.join(full_headers)
        results = self.data_lists['result'][0]
        result_strings = []

        for result in results:
            result_string = []
            result_string.append(result.name)
            spec_str = get_item_string(result.specimens)
            samp_str = get_item_string(result.samples)
            site_str = get_item_string(result.sites)
            loc_str = get_item_string(result.locations)
            strings = [spec_str, samp_str, site_str, loc_str]
            for string in strings:
                result_string.append(string)
            for key in actual_headers:
                add_string = result.pmag_data[key]
                if key == 'er_citation_names' and not add_string.strip('\t'):
                    add_string = 'This study'
                result_string.append(str(add_string))
            result_string = '\t'.join(result_string)
            result_strings.append(result_string)

        outfile = open(os.path.join(self.WD, 'pmag_results.txt'), 'w')
        outfile.write('tab\tpmag_results\n')
        outfile.write(header_string + '\n')
        for string in result_strings:
            outfile.write(string + '\n')
        outfile.close()
        return outfile

    def write_age_file(self):
        """
        Write er_ages.txt based on updated ErMagicBuilder data object
        """
        if not self.write_ages:
            print('-I- No age data available to write')
            return
        first_headers = self.first_age_headers
        actual_headers = sorted(self.headers['age']['er'][0])
        for header in first_headers:
            if header in actual_headers:
                actual_headers.remove(header)
        add_headers = ['er_specimen_name', 'er_sample_name', 'er_site_name', 'er_location_name']
        actual_headers[:0] = first_headers
        full_headers = add_headers[:]
        full_headers.extend(actual_headers)

        header_string = '\t'.join(full_headers)
        ages = []
        for dtype in ['specimen', 'sample', 'site', 'location']:
            ages_list = sorted(self.data_lists[dtype][0], key=lambda item: item.name)
            ages.extend(ages_list)

        age_strings = []
        for age in ages:
            ind = self.ancestry.index(age.dtype)
            ancestors = ['' for num in range(len(self.ancestry) - (ind+2))]
            data_found = False
            string = ''
            if age.dtype == 'specimen':
                string += age.name + '\t'
            elif age.dtype == 'sample':
                string += '\t' + age.name + '\t'
            elif age.dtype == 'site':
                string += '\t\t' + age.name + '\t'
            elif age.dtype == 'location':
                string += '\t\t\t' + age.name + '\t'
            parent = age.get_parent()
            grandparent = None
            if parent:
                ancestors[0] = parent.name
                grandparent = parent.get_parent()
                if grandparent:
                    ancestors[1] = grandparent.name
                    greatgrandparent = grandparent.get_parent()
                    if greatgrandparent:
                        ancestors[2] = greatgrandparent.name
            for ancestor in ancestors:
                string += ancestor + '\t'
            for key in actual_headers:
                try:
                    add_string = age.age_data[key]
                except KeyError:
                    add_string = ''
                    age.age_data[key] = ''
                if add_string and not key == 'er_citation_names':
                    data_found = True
                if key == 'er_citation_names' and not add_string.strip('\t'):
                    add_string = 'This study'
                string += add_string + '\t'
            # prevent extra '' at the end of age string
            if string.endswith('\t'):
                string = string[:-1]
            # only write ages to file if there is data provided
            if data_found:
                age_strings.append(string)
        outfile = open(os.path.join(self.WD, 'er_ages.txt'), 'w')
        outfile.write('tab\ter_ages\n')
        outfile.write(header_string + '\n')
        if not age_strings:
            outfile.close()
            os.remove(os.path.join(self.WD, 'er_ages.txt'))
            return False
        for string in age_strings:
            outfile.write(string + '\n')
        outfile.close()
        return outfile

    ## Validations  ##

    def validate_data(self):
        """
        Validate specimen, sample, site, and location data.
        """
        warnings = {}
        spec_warnings, samp_warnings, site_warnings, loc_warnings = {}, {}, {}, {}
        if self.specimens:
            spec_warnings = self.validate_items(self.specimens, 'specimen')
        if self.samples:
            samp_warnings = self.validate_items(self.samples, 'sample')
        if self.sites:
            site_warnings = self.validate_items(self.sites, 'site')
        if self.locations:
            loc_warnings = self.validate_items(self.locations, 'location')
        return spec_warnings, samp_warnings, site_warnings, loc_warnings


    def validate_items(self, item_list, item_type):
        """
        Go through a list Pmag_objects and check for:
        parent errors,
        children errors,
        type errors.
        Return a dictionary of exceptions in this format:
        {sample1: {'parent': [warning1, warning2, warning3], 'child': [warning1, warning2]},
         sample2: {'child': [warning1], 'type': [warning1, warning2]},
          ...}

        """
        def append_or_create_dict_item(warning_type, dictionary, key, value):
            """
            Add to dictionary with this format:
            {key1: {warning_type1: [value1, value2], warning_type2: [value1]},
            ...}
            """
            if not value:
                return
            try:
                name = key.name
            except AttributeError:
                name = key
            if not name in dictionary:
                dictionary[name] = {}
            if not warning_type in dictionary[name]:
                dictionary[name][warning_type] = []
            for v in value:
                dictionary[name][warning_type].append(v)

        def check_item_type(item, item_type):#, warnings=None):
            """
            Make sure that item has appropriate type, and is in the data object.
            """
            warnings = []
            item_list, item_class, item_constructor = self.data_lists[item_type]
            if not isinstance(item, item_class):
                warnings.append(PmagException('wrong type'))
            if item not in item_list:
                warnings.append(PmagException('not in data object'))
            return warnings

        def check_item_for_parent(item, item_type, parent_type):
            """
            Make sure that item has a parent of the correct type
            """
            if not parent_type:
                return []
            if not isinstance(item, Pmag_object):
                return []
            warnings = []
            parent = item.get_parent()
            parent_list, parent_class, parent_constructor = self.data_lists[parent_type]
            if not parent or not parent.name:
                warnings.append(PmagException('missing parent'))
                return warnings
            if not isinstance(parent, parent_class):
                warnings.append(PmagException('invalid parent type', parent))
            if not parent in parent_list:
                warnings.append(PmagException('parent not in data object', parent))
            return warnings

        def check_item_for_children(item, child_type):
            """
            Make sure that any children are of the correct type,
            and are in the data object
            """
            if not child_type:
                return []
            warnings = []
            children = item.children
            child_list, child_class, child_constructor = self.data_lists[child_type]
            for child in children:
                if not isinstance(child, child_class):
                    warnings.append(PmagException('child has wrong type', child))
                if not child in child_list:
                    warnings.append(PmagException('child not in data object', child))
            return warnings

        warnings = {}
        type_ind = self.ancestry.index(item_type)
        parent_type = self.ancestry[type_ind+1]
        child_type = self.ancestry[type_ind-1]
        for item in item_list:
            #warnings[item] = []
            type_warnings = check_item_type(item, item_type)
            append_or_create_dict_item('type', warnings, item, type_warnings)
            parent_warnings = check_item_for_parent(item, item_type, parent_type)
            append_or_create_dict_item('parent', warnings, item, parent_warnings)
            child_warnings = check_item_for_children(item, child_type)
            append_or_create_dict_item('children', warnings, item, child_warnings)
        return warnings


    def validate_results(self, result_list):
        """
        """
        def in_data_obj(lst, dtype):
            missing = []
            for item in lst:
                if item not in self.data_lists[dtype][0]:
                    try:
                        item_name = item.name
                    except AttributeError:
                        item_name = str(item)
                    missing.append(item_name)
            return missing

        def add_result_dict_item(dictionary, key, value):
            if not value:
                return
            elif key not in dictionary:
                dictionary[key] = value

        warnings = {}
        for result in result_list:
            res_warnings = {}
            if result.specimens:
                add_result_dict_item(res_warnings, 'specimen', in_data_obj(result.specimens, 'specimen'))
            if result.samples:
                add_result_dict_item(res_warnings, 'sample', in_data_obj(result.samples, 'sample'))
            if result.sites:
                add_result_dict_item(res_warnings, 'site', in_data_obj(result.sites, 'site'))
            if result.locations:
                add_result_dict_item(res_warnings, 'location', in_data_obj(result.locations, 'location'))
            if res_warnings:
                warnings[result.name] = res_warnings
        return warnings

    def validate_measurements(self, meas_list):
        meas_warnings = {}
        for meas in meas_list:
            warnings = []
            if not meas.specimen:
                warnings.append(PmagException('missing parent'))
            elif not meas.specimen in self.specimens:
                warnings.append(PmagException('parent not in data object', meas.specimen))
            if warnings:
                meas_warnings[meas] = {}
                meas_warnings[meas]['parent'] = warnings

        return meas_warnings

    # helper methods
    def get_ancestors(self, pmag_object):
        ancestors = []
        ancestors = ['' for num in range(len(self.ancestry) - (self.ancestry_ind+2))]
        parent = self.ancestry[self.ancestry_ind+1]
        parent = pmag_object.get_parent()
        grandparent, greatgrandparent = None, None
        if parent:
            ancestors[0] = parent.name
            grandparent = parent.get_parent()
            if grandparent:
                ancestors[1] = grandparent.name
                greatgrandparent = grandparent.get_parent()
                if greatgrandparent:
                    ancestors[2] = greatgrandparent.name
        return ancestors

    def get_descendents(self, pmag_object):
        descendents = self.ancestry[1:self.ancestry_ind]
        descendents = ['' for num in range(len(descendents))]
        children = pmag_object.children
        if children:
            descendents[-1] = children
        grandchildren = []
        for child in pmag_object.children:
            if pmag_object.children:
                grandchildren.extend(child.children)
        if grandchildren:
            descendents[-2] = grandchildren
        greatgrandchildren = []
        for gchild in grandchildren:
            if gchild.children:
                greatgrandchildren.extend(gchild.children)
        if greatgrandchildren:
            descendents[-3] = greatgrandchildren
        return descendents

    def get_min_max_lat_lon(self, locations):
        """
        Take a list of locations and return a dictionary with:
        location1:
        'location_begin_lat', 'location_begin_lon',
        'location_end_lat', 'location_end_lon'.
        and so on.
        """
        d = {}
        for location in locations:
            sites = location.sites
            max_lat, min_lat = '', ''
            max_lon, min_lon = '', ''
            if not any(sites):
                d[location.name] = {'location_begin_lat': min_lat, 'location_begin_lon': min_lon,
                                    'location_end_lat': max_lat, 'location_end_lon': max_lon}
                #return d
                continue
            lats, lons = [], []
            # try to fill in min/max latitudes/longitudes from sites
            for site in sites:
                if site.er_data['site_lon']:
                    lons.append(site.er_data['site_lon'])
                if site.er_data['site_lat']:
                    lats.append(site.er_data['site_lat'])
            if lats:
                lats = [float(lat) for lat in lats]
                max_lat = max(lats)
                min_lat = min(lats)
            if lons:
                lons = [float(lon) for lon in lons]
                max_lon = max(lons)
                min_lon = min(lons)
            d[location.name] = {'location_begin_lat': min_lat, 'location_begin_lon': min_lon,
                                'location_end_lat': max_lat, 'location_end_lon': max_lon}
        return d



class PmagException(Exception):

    def __init__(self, message, obj=None):
        super(PmagException, self).__init__(message)
        self.obj = obj


# measurements can be uniquely identified by experiment name + measurement #
# location, site, sample, and specimen names are ALL required headers for each measurement

class Measurement(object):

    def __init__(self, experiment_name, meas_number, specimen=None, data=None):
        self.experiment_name = experiment_name
        self.meas_number = meas_number
        self.name = experiment_name.strip() + '_' + str(meas_number)
        self.specimen = specimen
        self.er_data = remove_dict_headers(data)
        self.pmag_data = {}

    def __repr__(self):
        return 'Measurement: ' + self.name


class Pmag_object(object):
    """
    Base class for Specimens, Samples, Sites, etc.
    """

    def __init__(self, name, dtype, data_model=None, er_data=None, pmag_data=None, results_data=None):#, headers={}):
        if not data_model:
            self.data_model = validate_upload.get_data_model()
        else:
            self.data_model = data_model
        self.name = name.strip() # names shouldn't start or end with a space!
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
            self.er_data = combine_dicts(er_data, er_reqd_data)
        else:
            self.er_data = er_reqd_data
        if pmag_data:
            self.pmag_data = combine_dicts(pmag_data, pmag_reqd_data)
        else:
            self.pmag_data = pmag_reqd_data
        if results_data:
            self.results_data = combine_dicts(results_data, results_reqd_data)
        else:
            self.results_data = None

        if dtype in ('specimen', 'sample', 'site', 'location'):
            self.age_reqd_headers, self.age_optional_headers = self.get_headers('er_ages')
            self.age_data = {key: '' for key in self.age_reqd_headers}
            remove_dict_headers(self.age_data)

        # take out unneeded headers
        remove_dict_headers(self.er_data)
        remove_dict_headers(self.pmag_data)
        # make sure all longitudes/declinations/azimuths are in 0-360
        self.er_data = pmag.adjust_all_to_360(self.er_data)

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
        reqd_headers = sorted([header for header in list(data_dict.keys()) if data_dict[header]['data_status'] == 'Required'])
        optional_headers = sorted([header for header in list(data_dict.keys()) if data_dict[header]['data_status'] != 'Required'])
        return reqd_headers, optional_headers

    def update_data(self, er_data=None, pmag_data=None, replace_data=False):
        if er_data:
            if replace_data:
                self.er_data = er_data
            else:
                self.er_data = combine_dicts(er_data, self.er_data)
        if er_data:
            pmag.adjust_all_to_360(self.er_data)
        if pmag_data:
            if replace_data:
                self.pmag_data = pmag_data
            else:
                self.pmag_data = combine_dicts(pmag_data, self.pmag_data)
        if pmag_data:
            pmag.adjust_all_to_360(self.pmag_data)

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
        self.children = []
        self.propagate_data()

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
        self.propagate_data()
        return new_samp

    def change_specimen(self, new_name, new_sample=None, er_data=None, pmag_data=None, replace_data=False):
        self.name = new_name
        if new_sample:
            if self.sample:
                self.sample.specimens.remove(self)
            self.sample = new_sample
            self.sample.specimens.append(self)
        self.update_data(er_data, pmag_data, replace_data)
        self.propagate_data()

    def propagate_data(self):
        if not self.sample:
            return
        for dtype in ['class', 'lithology', 'type']:
            if 'specimen_' + dtype in list(self.er_data.keys()):
                if (not self.er_data['specimen_' + dtype]) or (self.er_data['specimen_' + dtype].lower() == "not specified"):
                    if self.sample.er_data['sample_' + dtype]:
                        value = self.sample.er_data['sample_' + dtype]
                        self.er_data['specimen_' + dtype] = value


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
        self.propagate_data()

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
        self.propagate_data()
        return new_site

    def change_sample(self, new_name, new_site=None, er_data=None, pmag_data=None, replace_data=False):
        self.name = new_name
        if new_site:
            if self.site:
                self.site.samples.remove(self)
            self.site = new_site
            self.site.samples.append(self)
        self.update_data(er_data, pmag_data, replace_data)
        self.propagate_data()

    def propagate_data(self):
        if not self.site:
            return
        for dtype in ['class', 'lithology', 'type']:
            samp_key = 'sample_' + dtype
            site_key = 'site_' + dtype
            if samp_key in list(self.er_data.keys()):
                if (not self.er_data[samp_key]) or (self.er_data[samp_key].lower() == "not specified"):
                    if site_key not in self.site.er_data:
                        self.site.er_data[site_key] = ''
                    elif self.site.er_data[site_key]:
                        value = self.site.er_data[site_key]
                        self.er_data[samp_key] = value
        for dtype in ['lat', 'lon']:
            samp_key = 'sample_' + dtype
            site_key = 'site_' + dtype
            if samp_key in list(self.er_data.keys()):
                if not self.er_data[samp_key]:
                    if site_key in list(self.site.er_data.keys()):
                        self.er_data[samp_key] = self.site.er_data[site_key]


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
        #    self.er_data = combine_dicts(new_er_data, self.er_data)
        self.update_data(new_er_data, new_pmag_data, replace_data)

class Result(object):

    def __init__(self, name, specimens='', samples='', sites='',
                 locations='', pmag_data=None, data_model=None):
        if not data_model:
            self.data_model = validate_upload.get_data_model()
        else:
            self.data_model = data_model
        self.name = name.strip() # names shouldn't start or end with a space!
        self.specimens = specimens
        self.samples = samples
        self.sites = sites
        self.locations = locations
        self.er_data = {}

        pmag_name = 'pmag_results'
        self.pmag_reqd_headers, self.pmag_optional_headers = self.get_headers(pmag_name)
        #self.results_reqd_headers, self.results_optional_headers = self.get_headers('pmag_results')

        pmag_reqd_data = {key: '' for key in self.pmag_reqd_headers}
        #results_reqd_data = {key: '' for key in self.results_reqd_headers}

        if pmag_data:
            self.pmag_data = combine_dicts(pmag_data, pmag_reqd_data)
        else:
            self.pmag_data = pmag_reqd_data
        # make sure all longitudes/declinations/azimuths are in 0-360
        self.pmag_data = pmag.adjust_all_to_360(self.pmag_data)

    def __repr__(self):
        if self.pmag_data:
            descr = self.pmag_data.get('result_description')
        else:
            descr = ''
        return 'Result: {}, {}'.format(self.name, descr)

    def get_headers(self, data_type):
        """
        If data model not present, get data model from Earthref site or PmagPy directory.
        Return a list of required headers and optional headers for given data type.
        """
        try:
            data_dict = self.data_model[data_type]
        except KeyError:
            return [], []
        reqd_headers = sorted([header for header in list(data_dict.keys()) if data_dict[header]['data_status'] == 'Required'])
        optional_headers = sorted([header for header in list(data_dict.keys()) if data_dict[header]['data_status'] != 'Required'])
        return reqd_headers, optional_headers

    def change_result(self, new_name, new_pmag_data=None, specs=None, samps=None,
                      sites=None, locs=None, replace_data=False):
        self.name = new_name
        if new_pmag_data:
            self.pmag_data = combine_dicts(new_pmag_data, self.pmag_data)
        self.specimens = specs
        self.samples = samps
        self.sites = sites
        self.locations = locs
        # make sure all longitudes/declinations/azimuths are in 0-360
        self.pmag_data = pmag.adjust_all_to_360(self.pmag_data)



if __name__ == '__main__':
    wd = pmag.get_named_arg('-WD', default_val=os.getcwd())
    builder = ErMagicBuilder(wd)
    builder.get_data()

# Random helper methods that MIGHT belong in pmag.py


def get_item_string(items_list):
    """
    take in a list of pmag_objects
    return a colon-delimited list of the findable names
    """
    if not items_list:
        return ''
    string_list = []
    for item in items_list:
        try:
            name = item.name
            string_list.append(name)
        except AttributeError:
            pass
    return ":".join(string_list)


def put_list_value_first(lst, first_value):
    if first_value in lst:
        lst.remove(first_value)
        lst[:0] = [first_value]

def remove_dict_headers(data_dict):
    for header in ['er_specimen_name', 'er_sample_name', 'er_site_name',
                   'er_location_name', 'pmag_result_name',
                   'er_specimen_names', 'er_sample_names', 'er_site_names',
                   'magic_experiment_name', 'measurement_number']:
        if header in list(data_dict.keys()):
            data_dict.pop(header)
    return data_dict

def remove_list_headers(data_list):
    for header in ['er_specimen_name', 'er_sample_name', 'er_site_name',
                   'er_location_name', 'pmag_result_name',
                   'er_specimen_names', 'er_sample_names', 'er_site_names',
                   'magic_experiment_name', 'measurement_number']:
        if header in data_list:
            data_list.remove(header)
    return data_list

def combine_dicts(new_dict, old_dict):
    """
    returns a dictionary with all key, value pairs from new_dict.
    also returns key, value pairs from old_dict, if that key does not exist in new_dict.
    if a key is present in both new_dict and old_dict, the new_dict value will take precedence.
    """
    old_data_keys = list(old_dict.keys())
    new_data_keys = list(new_dict.keys())
    all_keys = set(old_data_keys).union(new_data_keys)
    combined_data_dict = {}
    for k in all_keys:
        try:
            combined_data_dict[k] = new_dict[k]
        except KeyError:
            combined_data_dict[k] = old_dict[k]
    return combined_data_dict

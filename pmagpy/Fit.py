from __future__ import print_function

from builtins import map
from builtins import str
from builtins import object
class Fit(object):

    meas_data = None

    def __init__(self, name, tmax, tmin, color=(0,0,0), GUI=None, PCA_type=None):
        """
        The Data Structure that represents an interpretation
        @param: name -> the name of the fit as it will be displayed to the user
        @param: tmax -> the upper bound of the fit
        @param: tmin -> the lower bound of the fit
        @param: color -> the color of the fit when it is plotted
        @param: GUI -> the Zeq_GUI on which this fit is drawn
        """
        if not isinstance(name,str): name = str(name)
        elif name == "" or name.replace(" ","") == "": print("No name supplied for Fit, this is generally a problem, naming Toto."); name = "Toto"
        self.name = name
        if type(tmax) != str:
            if tmax == None: self.tmax = ""
            else:
                try: self.tmax = str(tmax)
                except ValueError: self.tmax = ""
        else:
            self.tmax = tmax
        if type(tmin) != str:
            if tmin == None: self.tmin = ""
            else:
                try: self.tmin = str(tmin)
                except ValueError: self.tmin = ""
        else:
            self.tmin = tmin
        self.color = color
        calculation_type=None
        if PCA_type == None:
            if GUI!=None: calculation_type=GUI.PCA_type_box.GetValue()
            else: calculation_type = None
        if calculation_type=="line": PCA_type="DE-BFL"
        elif calculation_type=="line-anchored": PCA_type="DE-BFL-A"
        elif calculation_type=="line-with-origin": PCA_type="DE-BFL-O"
        elif calculation_type=="Fisher": PCA_type="DE-FM"
        elif calculation_type=="plane": PCA_type="DE-BFP"
        self.PCA_type = PCA_type
        if GUI!=None:
            self.lines = [None,None]
            self.points = [None,None]
            self.eqarea_data = [None,None]
            self.mm0_data = [None,None]
        self.GUI = GUI
        self.pars = {}
        self.geopars = {}
        self.tiltpars = {}

    def select(self):
        """
        Makes this fit the selected fit on the GUI that is it's parent
        (Note: may be moved into GUI soon)
        """
        if self.GUI==None: return
        self.GUI.current_fit = self
        if self.tmax != None and self.tmin != None:
            self.GUI.update_bounds_boxes()
        if self.PCA_type != None:
            self.GUI.update_PCA_box()
        try: self.GUI.zijplot
        except AttributeError: self.GUI.draw_figure(self.GUI.s)
        self.GUI.fit_box.SetStringSelection(self.name)
        self.GUI.get_new_PCA_parameters(-1)

    def get(self,coordinate_system):
        """
        Return the pmagpy paramters dictionary associated with this fit and the given
        coordinate system
        @param: coordinate_system -> the coordinate system who's parameters to return
        """
        if coordinate_system == 'DA-DIR' or coordinate_system == 'specimen':
            return self.pars
        elif coordinate_system == 'DA-DIR-GEO' or coordinate_system == 'geographic':
            return self.geopars
        elif coordinate_system == 'DA-DIR-TILT' or coordinate_system == 'tilt-corrected':
            return self.tiltpars
        else:
            print("-E- no such parameters to fetch for " + coordinate_system + " in fit: " + self.name)
            return None

    def put(self,specimen,coordinate_system,new_pars):
        """
        Given a coordinate system and a new parameters dictionary that follows pmagpy
        convention given by the pmag.py/domean function it alters this fit's bounds and
        parameters such that it matches the new data.
        @param: specimen -> None if fit is for a site or a sample or a valid specimen from self.GUI
        @param: coordinate_system -> the coordinate system to alter
        @param: new_pars -> the new paramters to change your fit to
        @alters: tmin, tmax, pars, geopars, tiltpars, PCA_type
        """

        if specimen != None:
            if type(new_pars)==dict:
                if 'er_specimen_name' not in list(new_pars.keys()): new_pars['er_specimen_name'] = specimen
                if 'specimen_comp_name' not in list(new_pars.keys()): new_pars['specimen_comp_name'] = self.name
            if type(new_pars) != dict or 'measurement_step_min' not in list(new_pars.keys()) or 'measurement_step_max' not in list(new_pars.keys()) or 'calculation_type' not in list(new_pars.keys()):
                print("-E- invalid parameters cannot assign to fit %s for specimen %s - was given:\n%s"%(self.name,specimen,str(new_pars)))
                return self.get(coordinate_system)

            self.tmin = new_pars['measurement_step_min']
            self.tmax = new_pars['measurement_step_max']
            self.PCA_type = new_pars['calculation_type']

            if self.GUI!=None:
                steps = self.GUI.Data[specimen]['zijdblock_steps']
                tl = [self.tmin,self.tmax]
                for i,t in enumerate(tl):
                    if str(t) in steps: tl[i] = str(t)
                    elif str(int(t)) in steps: tl[i] = str(int(t))
                    elif "%.1fmT"%t in steps: tl[i] = "%.1fmT"%t
                    elif "%.0fC"%t in steps: tl[i] = "%.0fC"%t
                    else:
                        print("-E- Step " + str(tl[i]) + " does not exsist (func: Fit.put)")
                        tl[i] = str(t)
                self.tmin,self.tmax = tl
            elif meas_data != None:
                steps = meas_data[specimen]['zijdblock_steps']
                tl = [self.tmin,self.tmax]
                for i,t in enumerate(tl):
                    if str(t) in steps: tl[i] = str(t)
                    elif str(int(t)) in steps: tl[i] = str(int(t))
                    elif "%.1fmT"%t in steps: tl[i] = "%.1fmT"%t
                    elif "%.0fC"%t in steps: tl[i] = "%.0fC"%t
                    else:
                        print("-E- Step " + str(tl[i]) + " does not exsist (func: Fit.put)")
                        tl[i] = str(t)
                self.tmin,self.tmax = tl
            else: self.tmin,self.tmax = list(map(str, tl))

        if coordinate_system == 'DA-DIR' or coordinate_system == 'specimen':
            self.pars = new_pars
        elif coordinate_system == 'DA-DIR-GEO' or coordinate_system == 'geographic':
            self.geopars = new_pars
        elif coordinate_system == 'DA-DIR-TILT' or coordinate_system == 'tilt-corrected':
            self.tiltpars = new_pars
        else:
            print('-E- no such coordinate system could not assign those parameters to fit')

    def equal(self,other):
        if not isinstance(other,Fit): return False
        elif self.name != other.name: return False
        elif self.tmin != other.tmin: return False
        elif self.tmax != other.tmax: return False
        elif self.PCA_type != other.PCA_type: return False
#        elif 'specimen_dec' in self.pars.keys() and 'specimen_dec' in other.pars.keys() and self.pars!=other.pars: return False
#        elif 'specimen_dec' in self.geopars.keys() and 'specimen_dec' in other.geopars.keys() and self.geopars!=other.geopars: return False
#        elif 'specimen_dec' in self.tiltpars.keys() and 'specimen_dec' in other.tiltpars.keys() and self.tiltpars!=other.tiltpars: return False
        elif self.color != other.color: print("color difference between fits"); return True
        else: return True

    def has_values(self, name, tmin, tmax):
        """
        A basic fit equality checker compares name and bounds of 2 fits
        @param: name -> name of the other fit
        @param: tmin -> lower bound of the other fit
        @param: tmax -> upper bound of the other fit
        @return: boolean comaparing 2 fits
        """
        return str(self.name) == str(name) and str(self.tmin) == str(tmin) and str(self.tmax) == str(tmax)

    def __str__(self):
        """
        Readable printing method for fit to turn it into a string
        @return: string representing fit
        """
        try: return self.name + ": \n" + "Tmax = " + self.tmax + ", Tmin = " + self.tmin + "\n" + "Color = " + str(self.color)
        except ValueError: return self.name + ": \n" + " Color = " + self.color

#! /usr/bin/env python

import sys
import re

# using this to get a nice, clean list from the table of contents in Cookbook to see what we've got
def remove_numbers(the_file):
    data = open(the_file, 'rU').readlines()
    print "data", data
    new_data = []
    for i in data:
        i = str(i)
        listy = i.split()
        print listy
        try:
            new_data.append(listy[1])
        except:
            pass
    new_file = open('full_list_of_programs.txt', 'w')
    new_file.write(str(new_data))

# using this to clean up file with the programs from sort_script.py
def thingee(a_file):
    data = open(a_file, 'rU').readlines()
    listy = []
    for i in data:
        new = i[9:-9]
        new = new + '.py'
        print new
        listy.append(new)
    print listy
    open('final_list_of_programs_with_tests.txt', 'w').write(str(listy))
    return listy


from_table_of_contents = ['aarm_magic.py', 'angle.py', 'ani_depthplot.py', 'aniso_magic.py', 'apwp.py', 'atrm_magic.py', 'azdip_magic.py', 'b_vdm.py', 'basemap_magic.py', 'biplot_magic.py', 'bootams.py', 'cart_dir.py', 'chartmaker.py', 'chi_magic.py', 'combine_magic.py', 'common_mean.py', 'cont_rot.py', 'convert2unix.py', 'convert_samples.py', 'core_depthplot.py', 'curie.py', 'customize_criteria.py', 'dayplot_magic.py', 'di_eq.py', 'di_geo.py', 'di_rot.py', 'di_tilt.py', 'di_vgp.py', 'dipole_pinc.py', 'dipole_plat.py', 'dir_cart.py', 'dmag_magic.py', 'download_magic.py', 'eigs_s.py', 'eq_di.py', 'eqarea.py', 'eqarea_ell.py', 'eqarea_magic.py', 'find_EI.py', 'fisher.py', 'fishqq.py', 'fishrot.py', 'foldtest.py', 'foldtest_magic.py', 'gaussian.py', 'gobing.py', 'gofish.py', 'gokent.py', 'goprinc.py', 'grab_magic_key.py', 'histplot.py', 'hysteresis_magic.py', 'igrf.py', 'incfish.py', 'irmaq_magic.py', 'k15_magic.py', 'k15_s.py', 'KLY4S_magic.py', 'lnp_magic.py', 'lowrie.py', 'lowrie_magic.py', 'MagIC.py', 'magic_select.py', 'make_magic_plots.py', 'Measurement', 'measurements_normalize.py', 'mk_redo.py', 'nrm_specimens_magic.py', 'orientation_magic.py', 'parse_measurements.py', 'pca.py', 'plotXY.py', 'plot_cdf.py', 'plot_magic_keys.py', 'plot_mapPTS.py', 'plotdi_a.py', 'pmag_results_extract.py', 'pt_rot.py', 'qqlot.py', 'quick_hyst.py', 'revtest.py', 'revtest_magic.py', 's_eigs.py', 's_geo.py', 's_hext.py', 's_tilt.py', 's_magic.py', 'scalc.py', 'scalc_magic.py', 'site_edit_magic.py', 'specimens_results_magic.py', 'stats.py', 'strip_magic.py', 'sundec.py', 'thellier_GUI.py', 'thellier_magic.py', 'thellier_magic_redo.py', 'tk03.py', 'uniform.py', 'update_measurements.py', 'upload_magic.py', 'vdm_b.py', 'vector_mean.py', 'vgp_di.py', 'vgpmap_magic.py', 'watsonsF.py', 'watsonsV.py', 'zeq.py', 'zeq_magic.py', 'zeq_magic_redo.py']

#from_table_of_contents.sort()
print "from table of contents", from_table_of_contents
print len(from_table_of_contents)

programs_I_made_tests_for = ['CIT_magic.py', 'aarm_magic.py', 'agm_magic.py', 'angle.py', 'ani_depthplot.py', 'aniso_magic.py', 'apwp.py', 'atrm_magic.py', 'azdip_magic.py', 'b_vdm.py', 'basemap_magic.py', 'biplot_magic.py', 'bootams.py', 'cart_dir.py', 'chartmaker.py', 'chi_magic.py', 'combine_magic.py', 'common_mean.py', 'cont_rot.py', 'convert2unix.py', 'convert_samples.py', 'core_depthplot.py', 'curie.py', 'customize_criteria.py', 'dayplot_magic.py', 'di_eq.py', 'di_geo.py', 'di_rot.py', 'di_tilt.py', 'di_vgp.py', 'dipole_pinc.py', 'dipole_plat.py', 'dir_cart.py', 'dmag_magic.py', 'download_magic.py', 'eigs_s.py', 'eq_di.py', 'eqarea_ell.py', 'eqarea_magic.py', 'eqarea.py', 'find_EI.py', 'fisher.py', 'fishqq.py', 'fishrot.py', 'foldtest_magic.py', 'foldtest.py', 'gaussian.py', 'gobing.py', 'gofish.py', 'gokent.py', 'goprinc.py', 'grab_magic_key.py', 'histplot.py', 'hysteresis_magic.py', 'igrf.py', 'incfish.py', 'irmaq_magic.py', 'k15_magic.py', 'k15_s.py', 'kly4s_magic.py', 'lnp_magic.py', 'lowrie_magic.py', 'lowrie.py', 'magic_select.py', 'make_magic_plots.py', 'make_magic_plots_test,"conver.py', 'mk_redo.py', 'nrm_specimens_magic.py', 'orientation_magic.py', 'parse_measurements.py', 'pca.py', 'plot_cdf.py', 'plot_magic_keys.py', 'plotdi_a.py', 'plotxy.py', 'pmag_results_extract.py', 'pt_rot.py', 'qqplot.py', 'quick_hyst.py', 'revtest_magic.py', 'revtest.py', 's_eigs.py', 's_geo.py', 's_hext.py', 's_tilt.py', 'scalc_magic.py', 'scalc.py', 'site_edit_magic.py', 'stats.py', 'strip_magic.py', 'sundec.py', 'thellier_magic_redo.py', 'thellier_magic.py', 'tk03.py', 'uniform.py', 'upload_magic.py', 'vdm_b.py', 'vector_mean.py', 'vgp_di.py', 'vgpmap_magic.py', 'watsonsF.py', 'watsonsV.py', 'working.py', 'zeq_magic_redo.py', 'zeq_magic.py', 'zeq.py', '.py']
#programs_I_made_tests_for = ['aarm_magic.py', 'agm_magic.py', 'angle.py', 'ani_depthplot.py', 'aniso_magic.py', 'apwp.py', 'atrm_magic.py', 'azdip_magic.py', 'b_vdm.py', 'basemap_magic.py', 'biplot_magic.py', 'bootams.py', 'cart_dir.py', 'chartmaker.py', 'chi_magic.py', 'combine_magic.py', 'common_mean.py', 'cont_rot.py', 'convert2unix.py', 'convert_samples.py', 'core_depthplot.py', 'curie.py', 'customize_criteria.py', 'dayplot_magic.py', 'di_eq.py', 'di_geo.py', 'di_rot.py', 'di_tilt.py', 'di_vgp.py', 'dipole_pinc.py', 'dipole_plat.py', 'dir_cart.py', 'dmag_magic.py', 'download_magic.py', 'eigs_s.py', 'eq_di.py', 'eqarea_ell.py', 'eqarea_magic.py', 'eqarea.py', 'find_EI.py', 'fisher.py', 'fishqq.py', 'fishrot.py', 'foldtest_magic.py', 'foldtest.py', 'gaussian.py', 'gobing.py', 'gofish.py', 'gokent.py', 'goprinc.py', 'grab_magic_key.py', 'histplot.py', 'hysteresis_magic.py', 'igrf.py', 'incfish.py', 'irmaq_magic.py', 'k15_magic.py', 'k15_s.py', 'kly4s_magic.py', 'lnp_magic.py', 'lowrie_magic.py', 'lowrie.py', 'magic_select.py', 'make_magic_plots.py', 'make_magic_plots_test,"conver.py', 'mk_redo.py', 'nrm_specimens_magic.py', 'orientation_magic.py', 'pca.py', 'plot_cdf.py', 'plot_magic_keys.py', 'plotdi_a.py', 'plotxy.py', 'pmag_results_extract.py', 'pt_rot.py', 'quick_hyst.py', 'revtest_magic.py', 'revtest.py', 's_eigs.py', 's_geo.py', 's_hext.py', 's_tilt.py', 'scalc_magic.py', 'scalc.py', 'site_edit_magic.py', 'stats.py', 'strip_magic.py', 'sundec.py', 'thellier_magic_redo.py', 'thellier_magic.py', 'tk03.py', 'uniform.py', 'upload_magic.py', 'vdm_b.py', 'vector_mean.py', 'vgp_di.py', 'vgpmap_magic.py', 'watsonsF.py', 'watsonsV.py', 'working.py', 'zeq_magic_redo.py', 'zeq_magic.py']

#programs_I_made_tests_for.sort()
print "programs I made tests for", programs_I_made_tests_for
print len(programs_I_made_tests_for)


for i in from_table_of_contents:
    if i.lower() in programs_I_made_tests_for:
        pass
    else:
        print i


if __name__ == "__main__":
    pass
#    remove_numbers('list_of_programs.txt')
#    thingee('list_of_programs_with_tests.txt')

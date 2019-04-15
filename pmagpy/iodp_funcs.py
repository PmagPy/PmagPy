import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import pmagpy.pmag as pmag
def make_plot(fignum,arch_df,edited_df,sect_depths,hole,\
              gad_inc,depth_min,depth_max,labels):
    arch_df=arch_df[arch_df['core_depth']>depth_min]
    arch_df=arch_df[arch_df['core_depth']<=depth_max]
    edited_df=edited_df[edited_df['core_depth']>depth_min]
    edited_df=edited_df[edited_df['core_depth']<=depth_max]

    max_depth=arch_df.core_depth.max()
    min_depth=arch_df.core_depth.min()
    ax=plt.figure(fignum,(12,20))
    ax.add_subplot(131)
    plt.plot(np.log10(edited_df['magn_volume']*1e3),edited_df['core_depth'],'go')
    plt.plot(np.log10(arch_df['magn_volume']*1e3),arch_df['core_depth'],'k.',markersize=1)
#    plt.plot(np.log10(noends['magn_volume']*1e3),noends['core_depth'],'b.',)

    for d in sect_depths:
        plt.axhline(-d,color='black',linestyle='dashed')

    plt.xlabel('Log Intensity (mA/m)')
    for d in sect_depths:
        if d<max_depth and d>min_depth:
            plt.axhline(d,color='black',linestyle='dashed')
    plt.ylim(depth_max,depth_min)

    ax.add_subplot(132)

    plt.plot(edited_df['dir_dec'],edited_df['core_depth'],'go')
    plt.plot(arch_df['dir_dec'],arch_df['core_depth'],'k.',markersize=1)
#    plt.plot(noends['dir_dec'],noends['core_depth'],'b.')
    plt.axvline(180,color='red')

    plt.xlabel('Declination')
    plt.ylim(depth_max,depth_min)
    for d in sect_depths:
        if d<max_depth and d>min_depth:
            plt.axhline(d,color='black',linestyle='dashed')
    plt.ylim(depth_max,depth_min)

    plt.title(hole)
    ax.add_subplot(133)
    plt.plot(edited_df['dir_inc'],edited_df['core_depth'],'go')
    plt.plot(arch_df['dir_inc'],arch_df['core_depth'],'k.',markersize=1)
#    plt.plot(noends['dir_inc'],noends['core_depth'],'b.')

    plt.xlabel('Inclination')
    plt.axvline(gad_inc,color='blue',linestyle='dotted')
    plt.axvline(-gad_inc,color='blue',linestyle='dotted')

    plt.axvline(0,color='red')
    plt.xlim(-90,90)
    for d in sect_depths:
        if d<max_depth and d>=min_depth:
            plt.axhline(d,color='black',linestyle='dashed')


    for k in range(len(labels.values)):
        if sect_depths[k]<max_depth and sect_depths[k]>=min_depth:
            plt.text(100,sect_depths[k],labels.values[k],verticalalignment='top')
    plt.ylim(depth_max,depth_min);
    plt.savefig('Figures/'+hole+'_'+str(fignum)+'.pdf')
    print ('Plot saved in', 'Figures/'+hole+'_'+str(fignum)+'.pdf')

def inc_hist(df,hole):
    plt.figure(figsize=(12,5))
    plt.subplot(121)
    plt.ylabel('Number of inclinations')
    plt.xlabel('Inclination')
    sns.distplot(df['dir_inc'],kde=False,bins=24)
    plt.xlim(-90,90)
    plt.subplot(122)
    plt.ylabel('Fraction of inclinations')
    sns.distplot(df['dir_inc'],bins=24)
    plt.xlabel('Inclination')
    plt.xlim(-90,90)
    plt.savefig('Figures/'+hole+'_inclination_histogram.pdf');
    print ('Plot saved in ','Figures/'+hole+'_inclination_histogram.pdf')
    
def demag_step(magic_dir,hole,demag_step):
    arch_data=pd.read_csv(magic_dir+'/srm_arch_measurements.txt',sep='\t',header=1) 
    depth_data=pd.read_csv(magic_dir+'/srm_arch_sites.txt',sep='\t',header=1)
    depth_data['specimen']=depth_data['site']
    depth_data=depth_data[['specimen','core_depth']]
    depth_data.sort_values(by='specimen')
    arch_data=pd.merge(arch_data,depth_data,on='specimen')

    arch_demag_step=arch_data[arch_data['treat_ac_field']==demag_step]
    arch_demag_step=arch_data[arch_data['treat_ac_field']==demag_step]
    pieces=arch_demag_step.specimen.str.split('-',expand=True)
    pieces.columns=['exp','hole','core','sect','A/W','offset']
    arch_demag_step['core_sects']=pieces['core'].astype('str')+'-'+pieces['sect'].astype('str')

    arch_demag_step['offset']=pieces['offset'].astype('float')
    arch_demag_step['core']=pieces['core']
    arch_demag_step.to_csv(hole+'/'+hole+'_arch_demag_step.csv',index=False)
    print ("Here's your demagnetization step DataFrame")
    return arch_demag_step

def remove_ends(arch_demag_step,hole):
    noends=pd.DataFrame(columns=arch_demag_step.columns)
    core_sects=arch_demag_step.core_sects.unique()
    for core_sect in core_sects:
        cs_df=arch_demag_step[arch_demag_step['core_sects'].str.contains(core_sect)]
        if '-1' in core_sect: 
            cs_df=cs_df[cs_df.offset>cs_df['offset'].min()+80] # top 80cm
        else:
            cs_df=cs_df[cs_df.offset>cs_df['offset'].min()+10] # top 10 cm
        cs_df=cs_df[cs_df.offset<cs_df['offset'].max()-10]
        noends=pd.concat([noends,cs_df])
    noends.drop_duplicates(inplace=True)
    noends.to_csv(hole+'/'+hole+'_noends.csv',index=False)  
    print ("Here's your no end DataFrame")
    return noends

def remove_disturbance(noends,hole):
    disturbance_file=hole+'/'+hole+'_disturbances.xlsx'
    disturbance_df=pd.read_excel(disturbance_file)
    disturbance_df.dropna(subset=['Drilling disturbance intensity'],inplace=True)
    disturbance_df=disturbance_df[disturbance_df['Drilling disturbance intensity'].str.contains('high')]
    disturbance_df=disturbance_df[['Top Depth [m]','Bottom Depth [m]']]
    disturbance_df.reset_index(inplace=True)
    nodist=noends.copy(deep=True)
    for k in disturbance_df.index.tolist():
        top=disturbance_df.loc[k]['Top Depth [m]']
        bottom=disturbance_df.loc[k]['Bottom Depth [m]']
        nodist=nodist[(nodist['core_depth']<top) | (nodist['core_depth']>bottom)]
    nodist.sort_values(by='core_depth',inplace=True)
    nodist.drop_duplicates(inplace=True)
# save for later
    nodist.to_csv(hole+'/'+hole+'_nodisturbance.csv',index=False)    
    print ("Here's your no DescLogic disturbance DataFrame")
    return nodist

def no_xray_disturbance(nodist,hole):
    xray_file=hole+'/'+hole+'_xray_disturbance.xlsx'
    xray_df=pd.read_excel(xray_file,header=3)
    no_xray_df=pd.DataFrame(columns=nodist.columns)
    xray_df=xray_df[['Core','Section','interval (offset cm)']]

    xray_df.dropna(subset=['interval (offset cm)'],inplace=True)

    xray_df.reset_index(inplace=True)

    xray_df['core_sect']=xray_df['Core']+'-'+xray_df['Section'].astype('str')
    xr_core_sects=xray_df['core_sect'].tolist()

    nd_core_sects=nodist['core_sects'].tolist()
    used=[]
    # put in undisturbed cores
    for coresect in nd_core_sects: 
        if coresect not in used and coresect not in xr_core_sects:
            core_df=nodist[nodist['core_sects'].str.contains(coresect)]
            no_xray_df=pd.concat([no_xray_df,core_df])
            used.append(coresect)
        #print ('included all of ',coresect)
# take out disturbed bits
    for coresect in xr_core_sects: 
        if 'all' not in coresect:
        # pick out core_sect affected by disturbance
            core_df=nodist[(nodist['core_sects'].str.contains(coresect))]
            interval=xray_df.loc[xray_df['core_sect']==coresect]\
                 ['interval (offset cm)'].str.split('-').tolist()[0]
            top=int(interval[0])
            bottom=int(interval[1])
        # remove disturbed bit
            core_df=core_df[(core_df['offset']<top) | (core_df['offset']>bottom)]
        # add undisturbed bit to no_xray_df
            no_xray_df=pd.concat([no_xray_df,core_df])
        #print ('excluded bit from ',coresect,' between ',top,bottom)
# take out entire cores that are disturbed
    for coresect in xr_core_sects:  
        if 'all' in coresect:
            core=coresect.split('-')[0]
            no_xray_df=no_xray_df[no_xray_df['core'].str.match(core)==False]
            #print ('excluded all of ',core)
    no_xray_df.sort_values(by='core_depth',inplace=True)
#no_xray_df.drop_duplicates(inplace=True)
# save for later
    no_xray_df.to_csv(hole+'/'+hole+'_noXraydisturbance.csv',index=False)    
#meas_dicts = no_xray_df.to_dict('records')
#pmag.magic_write(magic_dir+'/no_xray_measurements.txt', meas_dicts, 'measurements')

    print ('Here is your DataFrame with no Xray identified disturbances')
    return no_xray_df
 
def adj_dec(df,hole):
    cores=df.core.unique()
    adj_dec_df=pd.DataFrame(columns=df.columns)
    for core in cores:
        core_df=df[df['core']==core]
        di_block=core_df[['dir_dec','dir_inc']].values
        ppars=pmag.doprinc(di_block)
        if ppars['inc']>0: # take the antipode
            ppars['dec']=ppars['dec']-180
        core_df['adj_dec']=(core_df['dir_dec']-ppars['dec'])%360
        core_df['dir_dec']=(core_df['adj_dec']+90)%360 # set mean normal to 90 for plottingh
        adj_dec_df=pd.concat([adj_dec_df,core_df])
    adj_dec_df.to_csv(hole+'/'+hole+'_dec_adjusted.csv') 
    print ('Adjusted Declination DataFrame returned')
    return adj_dec_df

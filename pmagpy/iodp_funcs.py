import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag
import pmagpy.pmagplotlib as pmagplotlib
def make_plot(fignum,arch_df,edited_df,sect_depths,hole,\
              gad_inc,depth_min,depth_max,labels,spec_df=[],agemin=0,agemax=0):
    arch_df=arch_df[arch_df['core_depth']>depth_min]
    arch_df=arch_df[arch_df['core_depth']<=depth_max]
    edited_df=edited_df[edited_df['core_depth']>depth_min]
    edited_df=edited_df[edited_df['core_depth']<=depth_max]
    if len(spec_df)>0:
        spec_df=spec_df[spec_df['core_depth']>depth_min]
        spec_df=spec_df[spec_df['core_depth']<=depth_max]
        plot_spec=True
    else: plot_spec=False
    max_depth=arch_df.core_depth.max()
    min_depth=arch_df.core_depth.min()
    plot=1
    if agemax:
        col=5
        fig=plt.figure(fignum,(14,16))
    else:
        col=3
        fig=plt.figure(fignum,(8,20))
    ax=plt.subplot(1,col,plot)
    plot+=1
    plt.plot(np.log10(edited_df['magn_volume']*1e3),edited_df['core_depth'],\
            'co',markeredgecolor='grey')
    plt.plot(np.log10(arch_df['magn_volume']*1e3),arch_df['core_depth'],'k.',markersize=1)

    for d in sect_depths:
        plt.axhline(-d,color='black',linestyle='dashed')
    plt.ylabel('Depth (mbsf)')
    plt.xlabel('Log Intensity (mA/m)')
    for d in sect_depths:
        if d<max_depth and d>min_depth:
            plt.axhline(d,color='black',linestyle='dashed')
    plt.ylim(depth_max,depth_min)

    ax=plt.subplot(1,col,plot)
    plot+=1
    plt.plot(edited_df['dir_dec'],edited_df['core_depth'],'co',markeredgecolor='grey')
    plt.plot(arch_df['dir_dec'],arch_df['core_depth'],'k.',markersize=1)
    if plot_spec:
        plt.plot(spec_df['dir_dec'],spec_df['core_depth'],'r*',markersize=10)
    
    plt.axvline(180,color='red')

    plt.xlabel('Declination')
    plt.ylim(depth_max,depth_min)
    for d in sect_depths:
        if d<max_depth and d>min_depth:
            plt.axhline(d,color='black',linestyle='dashed')
    plt.ylim(depth_max,depth_min)

    plt.title(hole)
    ax=plt.subplot(1,col,plot)
    plot+=1
    plt.plot(edited_df['dir_inc'],edited_df['core_depth'],'co',markeredgecolor='grey')
    plt.plot(arch_df['dir_inc'],arch_df['core_depth'],'k.',markersize=1)
    if plot_spec:
        plt.plot(spec_df['dir_inc'],spec_df['core_depth'],'r*',markersize=10)

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
    if agemax:
        ax=plt.subplot(1,col,plot)
        ax.axis('off') 
        ax=plt.subplot(1,col,plot+1)
        pmagplotlib.plot_ts(ax,agemin,agemax)
    plt.savefig('Figures/'+hole+'_'+str(fignum)+'.pdf')
    print ('Plot saved in', 'Figures/'+hole+'_'+str(fignum)+'.pdf')

def inc_hist(df,hole):
    plt.figure(figsize=(12,5))
    plt.subplot(121)
    plt.ylabel('Number of inclinations')
    sns.distplot(df['dir_inc'],kde=False,bins=24)
    plt.xlabel('Inclination')
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
    pieces=arch_demag_step.specimen.str.split('-',expand=True)
    pieces.columns=['exp','hole','core','sect','A/W','offset']
    arch_demag_step['core_sects']=pieces['core'].astype('str')+'-'+pieces['sect'].astype('str')
    arch_demag_step['offset']=pieces['offset'].astype('float')
    arch_demag_step['core']=pieces['core']
    arch_demag_step['section']=pieces['sect']
    arch_demag_step.drop_duplicates(inplace=True)
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
    noends.fillna("",inplace=True)
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
    nodist.fillna("",inplace=True)
# save for later
    nodist.to_csv(hole+'/'+hole+'_nodisturbance.csv',index=False)    
    print ("Here's your no DescLogic disturbance DataFrame")
    return nodist

def no_xray_disturbance(nodist,hole):
    xray_file=hole+'/'+hole+'_xray_disturbance.xlsx'
    xray_df=pd.read_excel(xray_file,header=2)
    no_xray_df=pd.DataFrame(columns=nodist.columns)
    xray_df=xray_df[['Core','Section','interval (offset cm)']]
    xray_df.dropna(inplace=True)
    if type(xray_df.Section)!='str':
        xray_df.Section=xray_df.Section.astype('int64')
    xray_df.reset_index(inplace=True)
    xray_df['core_sect']=xray_df['Core']+'-'+xray_df['Section'].astype('str')
    xr_core_sects=xray_df['core_sect'].tolist()
    nd_core_sects=nodist['core_sects'].tolist()
    used=[]
    # put in undisturbed cores
    for coresect in nd_core_sects: 
        if coresect not in used and coresect not in xr_core_sects:
            core_df=nodist[nodist['core_sects'].str.match(coresect)]
            no_xray_df=pd.concat([no_xray_df,core_df])
            used.append(coresect)
# take out disturbed bits
    for coresect in xr_core_sects: 
        if 'all' not in coresect:
        # pick out core_sect affected by disturbance
            core_df=nodist[(nodist['core_sects'].str.match(coresect))]
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
        #    print ('excluded all of ',core)
    no_xray_df.sort_values(by='core_depth',inplace=True)
# save for later
    no_xray_df.drop_duplicates(inplace=True)
    no_xray_df.fillna("",inplace=True)
    no_xray_df.to_csv(hole+'/'+hole+'_noXraydisturbance.csv',index=False)    
#meas_dicts = no_xray_df.to_dict('records')
#pmag.magic_write(magic_dir+'/no_xray_measurements.txt', meas_dicts, 'measurements')

    print ('Here is your DataFrame with no Xray identified disturbances')
    return no_xray_df
 
def adj_dec(df,hole):
    cores=df.core.unique()
    adj_dec_df=pd.DataFrame(columns=df.columns)
    core_dec_corr={}
    for core in cores:
        core_df=df[df['core']==core]
        di_block=core_df[['dir_dec','dir_inc']].values
        ppars=pmag.doprinc(di_block)
        if ppars['inc']>0: # take the antipode
            ppars['dec']=ppars['dec']-180
        core_dec_corr[core]=ppars['dec']
        core_df['adj_dec']=(core_df['dir_dec']-ppars['dec'])%360
        core_df['dir_dec']=(core_df['adj_dec']+90)%360 # set mean normal to 90 for plottingh
        adj_dec_df=pd.concat([adj_dec_df,core_df])
    adj_dec_df.fillna("",inplace=True)
    adj_dec_df.drop_duplicates(inplace=True)
    adj_dec_df.to_csv(hole+'/'+hole+'_dec_adjusted.csv',index=False) 
    print ('Adjusted Declination DataFrame returned')
    return adj_dec_df,core_dec_corr

def plot_aniso(df,fignum=1,save_figs=False):
    v1_decs=df['v1_dec'].values
    v1_incs=df['v1_inc'].values
    v3_decs=df['v3_dec'].values
    v3_incs=df['v3_inc'].values
    ipmag.plot_net(fignum)
    ipmag.plot_di(dec=v1_decs,inc=v1_incs,marker='s',markersize=50,color='red')
    ipmag.plot_di(dec=v3_decs,inc=v3_incs,marker='o',markersize=50,color='black')
    plt.title('Core coordinates')
    if save_figs: plt.savefig('aniso_core.svg')

    fig2=ipmag.plot_net(fignum+1)
    v1_decs=df['v1_dec_adj'].values
    v3_decs=df['v3_dec_adj'].values

    ipmag.plot_di(dec=v1_decs,inc=v1_incs,marker='s',markersize=50,color='red')
    ipmag.plot_di(dec=v3_decs,inc=v3_incs,marker='o',markersize=50,color='black')
    plt.title('Declination Adjusted')
    if save_figs: plt.savefig('aniso_corr.svg')
    return 

def convert_hole_depths(affine_file,hole_df,site,hole):
    affine=pd.read_csv(affine_file)
    affine['core']=affine['Core'].astype('str')+affine['Core type']
    affine['hole']=site+affine['Hole']
    hole_affine_df=affine[affine['hole'].str.match(hole)] # get the list for this hole
    hole_df['composite_depth']=hole_df['core_depth']
    cores=hole_affine_df.core.tolist()
    for core in cores:
        mbsf=hole_df[hole_df.core==core]['core_depth']
        if hole in affine['hole'].tolist() and  core in hole_affine_df.core.tolist():
            offset=hole_affine_df[hole_affine_df['core']==core]\
                    ['Cumulative offset (m)'].astype('float').values[0]
            hole_df.loc[hole_df.core==core,'composite_depth']=mbsf+offset
    hole_df['affine table']=affine_file
    return hole_df

def age_depth_plot(datums,paleo,size=100,depth_key='midpoint CSF-A (m)',title='UAge_Model_',dmin=0,dmax=600):

    plt.figure(1,(6,6))
    diatoms=paleo[paleo.Type.str.contains('DIAT')]
    rads=paleo[paleo.Type.str.contains('RAD')]
    diatom_lo=diatoms[diatoms.Event.str.contains('LO')]
    diatom_lo.reset_index(inplace=True)
    diatom_fo=diatoms[diatoms.Event.str.contains('FO')]
    diatom_fo.reset_index(inplace=True)
    rad_lo=rads[rads.Event.str.contains('LO')]
    rad_lo.reset_index(inplace=True)
    rad_fo=rads[rads.Event.str.contains('FO')]
    rad_fo.reset_index(inplace=True)
    age_key='Published Age\n(Ma)'
    mid_key='Mid depth \n(mbsf)'
    top_key='Top depth \n(mbsf)'
    bot_key='Bottom depth \n(mbsf)'
    datums['top']=datums[depth_key]-datums['range (+/-) (m)']
    datums['bot']=datums[depth_key]+datums['range (+/-) (m)']

    Hole_A=datums[datums['Hole'].str.contains('A')]
    Hole_B=datums[datums['Hole'].str.contains('B')]
    Hole_B.reset_index(inplace=True)
    Hole_C=datums[datums['Hole'].str.contains('C')]
    Hole_C.reset_index(inplace=True)
    Hole_E=datums[datums['Hole'].str.contains('E')]
    Hole_E.reset_index(inplace=True)




# put on curve
    zero=pd.DataFrame(columns=datums.columns,index=[0])
    zero['Age (Ma)']=0
    zero[depth_key]=0
    datums=pd.concat([zero,datums])
    datums.dropna(subset=['Age (Ma)',depth_key],   inplace=True)
    datums.sort_values(by=['Age (Ma)'],inplace=True)
    coeffs=np.polyfit(datums['Age (Ma)'].values,datums[depth_key].values,3)
    fit=np.polyval(coeffs,datums['Age (Ma)'].values)
    plt.plot(datums['Age (Ma)'].values,fit,'c-',lw=3,label='polynomial fit')


# plot the paleo
    for k in rad_lo.index:
        plt.plot([rad_lo.iloc[k][age_key],rad_lo.iloc[k][age_key]],\
             [rad_lo.iloc[k][top_key],rad_lo.iloc[k][bot_key]],'g-')
    plt.scatter(rad_lo[age_key].values,rad_lo[mid_key].values,\
            marker='v',color='w',label='Rad LO',alpha=0.5,edgecolor='g')
    for k in rad_fo.index:
        plt.plot([rad_fo.iloc[k][age_key],rad_fo.iloc[k][age_key]],\
             [rad_fo.iloc[k][top_key],rad_fo.iloc[k][bot_key]],'g-')
    plt.scatter(rad_fo[age_key].values,rad_fo[mid_key].values,\
            marker='^',color='w',label='Rad FO',alpha=0.5,edgecolor='g')

    for k in diatom_fo.index:
        plt.plot([diatom_fo.iloc[k][age_key],diatom_fo.iloc[k][age_key]],\
             [diatom_fo.iloc[k][top_key],diatom_fo.iloc[k][bot_key]],'b-')
    plt.scatter(diatom_fo[age_key].values,diatom_fo[mid_key].values,\
            marker='^',color='w',label='Diatom FO',alpha=0.5,edgecolor='b')


    for k in diatom_lo.index:
        plt.plot([diatom_lo.iloc[k][age_key],diatom_lo.iloc[k][age_key]],\
             [diatom_lo.iloc[k][top_key],diatom_lo.iloc[k][bot_key]],'b-')
    plt.scatter(diatom_lo[age_key].values,diatom_lo[mid_key].values,\
            marker='v',color='w',label='Diatom LO',alpha=0.5,edgecolor='b')


#plot the pmag tie points


    plt.scatter(Hole_A['Age (Ma)'].values,Hole_A[depth_key].values,\
            marker='*',s=size,color='r',label='U1536A')
    for k in Hole_A.index:
        plt.plot([Hole_A.iloc[k]['Age (Ma)'],Hole_A.iloc[k]['Age (Ma)']],\
             [Hole_A.iloc[k]['top'],Hole_A.iloc[k]['bot']],'k-')
    plt.scatter(Hole_B['Age (Ma)'].values,Hole_B[depth_key].values,\
            marker='*',s=size,color='b',label='U1536B',alpha=1)
    for k in Hole_B.index:
        plt.plot([Hole_B.iloc[k]['Age (Ma)'],Hole_B.iloc[k]['Age (Ma)']],\
             [Hole_B.iloc[k]['top'],Hole_B.iloc[k]['bot']],'k-')
    plt.scatter(Hole_C['Age (Ma)'].values,Hole_C[depth_key].values,\
            marker='*',s=size,color='k',label='U1536C',alpha=1)
    for k in Hole_C.index:
        plt.plot([Hole_C.iloc[k]['Age (Ma)'],Hole_C.iloc[k]['Age (Ma)']],\
             [Hole_C.iloc[k]['top'],Hole_C.iloc[k]['bot']],'k-')
    plt.scatter(Hole_E['Age (Ma)'].values,Hole_E[depth_key].values,\
            marker='*',s=size,color='g',label='U1536E',alpha=1)

    for k in Hole_E.index:
        plt.plot([Hole_E.iloc[k]['Age (Ma)'],Hole_E.iloc[k]['Age (Ma)']],\
             [Hole_E.iloc[k]['top'],Hole_E.iloc[k]['bot']],'k-')


    
    plt.ylim(dmax,dmin)
    plt.xlim(amax,amin)
    plt.xlabel('Age (Ma), GTS12')
    plt.ylabel('Depth (mbsf)')
    plt.title(title)
    plt.legend()
    plt.savefig('Figures/'+title+'.pdf')
    return coeffs

def do_affine(affine_file,datums):
    cmb_top_key='Top Depth CCSF-A (m)'
    cmb_bot_key='Bottom Depth CCSF-A (m)'
    mbsf_top_key='Top Depth CSF-A (m)'
    mbsf_bot_key='Bottom Depth CSF-A (m)'
    datums.dropna(subset=['Core-Sect-Depth (top)'],inplace=True)
    holes=datums['Hole'].unique()
    affine=pd.read_csv(affine_file)
    datums['top_core_list']=datums['Core-Sect-Depth (top)'].str.split('-')
    datums['bot_core_list']=datums['Core-Sect-Depth (bottom)'].str.split('-')
    datums['top_core']=datums['top_core_list'].str.get(0)
    datums['bot_core']=datums['bot_core_list'].str.get(0)
    affine['core']=affine['Core'].astype('str')+affine['Core type']
    affine['hole']='Hole '+affine['Hole']
    aff_holes=affine['hole'].values.tolist()
    datums_out=pd.DataFrame(columns=datums.columns)
    for hole in holes:        
        hole_df=datums[datums['Hole']==hole]
        hole_affine_df=affine[affine['hole']==hole]
        top_cores=hole_df['top_core'].values
        bot_cores=hole_df['bot_core'].values
        for core in top_cores:
            if hole in aff_holes and  core in hole_affine_df.core.tolist():
                offset=hole_affine_df[hole_affine_df['core']==core]\
                      ['Cumulative offset (m)'].astype('float').values[0]
                mbsf=hole_df[hole_df.top_core==core][mbsf_top_key]
                hole_df.loc[hole_df.top_core==core,cmb_top_key]=mbsf+offset
            else:
                mbsf=hole_df[hole_df.top_core==core][mbsf_top_key]
                hole_df.loc[hole_df.top_core==core,cmb_top_key]=mbsf # no offset possible

        for core in bot_cores:
            if hole in aff_holes and  core in hole_affine_df.core.tolist():
                offset=hole_affine_df[hole_affine_df['core']==core]\
                      ['Cumulative offset (m)'].astype('float').values[0]
                mbsf=hole_df[hole_df.bot_core==core][mbsf_bot_key]
                hole_df.loc[hole_df.bot_core==core,cmb_bot_key]=mbsf+offset
            else:
                mbsf=hole_df[hole_df.bot_core==core][mbsf_bot_key]
                hole_df.loc[hole_df.bot_core==core,cmb_bot_key]=mbsf # no offset possible


        datums_out=pd.concat([datums_out,hole_df])   
    datums_out['affine table']=affine_file
    datums_out['midpoint CCSF-A (m)']=datums_out[cmb_bot_key]+.5*(datums_out[cmb_top_key]-datums_out[cmb_bot_key])
    return datums_out

def fix_aniso_data(aniso_df,core_dec_adj,site_df):


    aniso_df['aniso_v1_list']=aniso_df['aniso_v1'].str.split(":")
    aniso_df['tau1']=aniso_df['aniso_v1_list'].str.get(0).astype('float')
    aniso_df['v1_dec']=aniso_df['aniso_v1_list'].str.get(1).astype('float')
    aniso_df['v1_inc']=aniso_df['aniso_v1_list'].str.get(2).astype('float')
    aniso_df['aniso_v2_list']=aniso_df['aniso_v2'].str.split(":")
    aniso_df['tau2']=aniso_df['aniso_v2_list'].str.get(0).astype('float')
    aniso_df['v2_inc']=aniso_df['aniso_v2_list'].str.get(2).astype('float')
    aniso_df['v2_dec']=aniso_df['aniso_v2_list'].str.get(1).astype('float')
    aniso_df['aniso_v3_list']=aniso_df['aniso_v3'].str.split(":")
    aniso_df['tau3']=aniso_df['aniso_v3_list'].str.get(0).astype('float')
    aniso_df['v3_dec']=aniso_df['aniso_v3_list'].str.get(1).astype('float')
    aniso_df['v3_inc']=aniso_df['aniso_v3_list'].str.get(2).astype('float')

    pieces=aniso_df.specimen.str.split('-',expand=True)
    pieces.columns=['exp','hole','core','sect','A/W','offset']
    aniso_df['core']=pieces['core'].astype('str')
    cores=aniso_df.core.unique()
    aniso_dec_adj_df=pd.DataFrame(columns=aniso_df.columns)
    for core in cores:
        core_df=aniso_df[aniso_df.core.str.match(core)]
        core_df['v1_dec_adj']=(core_df['v1_dec']-core_dec_adj[core])%360
        core_df['v2_dec_adj']=(core_df['v2_dec']-core_dec_adj[core])%360
        core_df['v3_dec_adj']=(core_df['v3_dec']-core_dec_adj[core])%360
        aniso_dec_adj_df=pd.concat([aniso_dec_adj_df,core_df])



    site_df['specimen']=site_df['site']
    site_df=site_df[['specimen','core_depth']]
    aniso_dec_adj_df=aniso_dec_adj_df.merge(site_df,on='specimen')

    aniso_dec_adj_df.drop(columns=['aniso_v1_list','aniso_v2_list','aniso_v3_list'],inplace=True)
    return aniso_dec_adj_df

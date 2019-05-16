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
    for d in sect_depths:
        if d<max_depth and d>min_depth:
            plt.axhline(d,color='black',linestyle='dashed',linewidth=.75)
    plot+=1
    plt.plot(np.log10(edited_df['magn_volume']*1e3),edited_df['core_depth'],\
            'co',markeredgecolor='grey')
    plt.plot(np.log10(arch_df['magn_volume']*1e3),arch_df['core_depth'],'k.',markersize=1)

    plt.ylabel('Depth (mbsf)')
    plt.xlabel('Log Intensity (mA/m)')
    plt.ylim(depth_max,depth_min)

    ax=plt.subplot(1,col,plot)
    for d in sect_depths:
        if d<max_depth and d>min_depth:
            plt.axhline(d,color='black',linestyle='dashed',linewidth=.75)
    plot+=1
    plt.plot(edited_df['dir_dec'],edited_df['core_depth'],'co',markeredgecolor='grey')
    plt.plot(arch_df['dir_dec'],arch_df['core_depth'],'k.',markersize=1)
    if plot_spec:
        plt.plot(spec_df['dir_dec'],spec_df['core_depth'],'r*',markersize=10)
    
    plt.axvline(180,color='red')

    plt.xlabel('Declination')
    plt.ylim(depth_max,depth_min)
    plt.ylim(depth_max,depth_min)

    plt.title(hole)
    ax=plt.subplot(1,col,plot)
    for d in sect_depths:
        if d<max_depth and d>min_depth:
            plt.axhline(d,color='black',linestyle='dashed',linewidth=.75)
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
        core_df=nodist[(nodist['core_sects'].str.match(coresect))]
        x_core_df=xray_df[xray_df['core_sect']==coresect]
        core_sect_intervals=x_core_df['interval (offset cm)'].tolist()
        for core_sect_interval in core_sect_intervals:
            interval=core_sect_interval.split('-') 
            top=int(interval[0])
            bottom=int(interval[1])
        # remove disturbed bit
            core_df=core_df[(core_df['offset']<top) | (core_df['offset']>bottom)]
        # add undisturbed bit to no_xray_df
        no_xray_df=pd.concat([no_xray_df,core_df])
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

def age_depth_plot(datums,paleo,size=100,depth_key='midpoint CSF-A (m)',title='Age_Model_',dmin=0,dmax=600,amin=0,amax=8,poly=3):

    plt.figure(1,(5,5))
# put on curve
    zero=pd.DataFrame(columns=datums.columns,index=[0])
    zero['Age (Ma)']=0
    zero[depth_key]=0
    datums=pd.concat([zero,datums])
    datums.dropna(subset=['Age (Ma)',depth_key],   inplace=True)
    datums.sort_values(by=['Age (Ma)'],inplace=True)
    coeffs=np.polyfit(datums['Age (Ma)'].values,datums[depth_key].values,poly)
    fit=np.polyval(coeffs,datums['Age (Ma)'].values)
    plt.plot(datums['Age (Ma)'].values,fit,'c-',lw=3,label='polynomial fit')

#plot the tie points
    datums.dropna(subset=['Hole'],inplace=True)
    datums['top']=datums[depth_key]-datums['range (+/-) (m)']
    datums['bot']=datums[depth_key]+datums['range (+/-) (m)']
    datums=datums[datums['bot']<dmax]
    holes=datums['Hole'].unique()
    colors=['r','b','k','g']
    pcolors=['c','m','y','r','k']
    age_key='Published Age\n(Ma)'
    mid_key='Mid depth \n(mbsf)'
    top_key='Top depth \n(mbsf)'
    bot_key='Bottom depth \n(mbsf)'
    for i in range(len(holes)):
# plot the paleo
        paleo_hole=paleo[paleo.Hole.str.match(holes[i])]
        diatoms=paleo_hole[paleo_hole.Type.str.contains('DIAT')]
        rads=paleo_hole[paleo_hole.Type.str.contains('RAD')]
        diatom_lo=diatoms[diatoms.Event.str.contains('LO')]
        diatom_lo.reset_index(inplace=True)
        diatom_fo=diatoms[diatoms.Event.str.contains('FO')]
        diatom_fo.reset_index(inplace=True)
        rad_lo=rads[rads.Event.str.contains('LO')]
        rad_lo.reset_index(inplace=True)
        rad_fo=rads[rads.Event.str.contains('FO')]
        rad_fo.reset_index(inplace=True)
        for k in rad_lo.index:
            plt.plot([rad_lo.iloc[k][age_key],rad_lo.iloc[k][age_key]],\
                 [rad_lo.iloc[k][top_key],rad_lo.iloc[k][bot_key]],'g-')
        plt.scatter(rad_lo[age_key].values,rad_lo[mid_key].values,\
                marker='v',color='w',edgecolor=pcolors[i],label=holes[i]+':Rad LO')
        for k in rad_fo.index:
            plt.plot([rad_fo.iloc[k][age_key],rad_fo.iloc[k][age_key]],\
                 [rad_fo.iloc[k][top_key],rad_fo.iloc[k][bot_key]],'g-')
        plt.scatter(rad_fo[age_key].values,rad_fo[mid_key].values,\
                marker='^',color='w',edgecolor=pcolors[i],label=holes[i]+':Rad FO')

        for k in diatom_fo.index:
            plt.plot([diatom_fo.iloc[k][age_key],diatom_fo.iloc[k][age_key]],\
                 [diatom_fo.iloc[k][top_key],diatom_fo.iloc[k][bot_key]],'b-')
        plt.scatter(diatom_fo[age_key].values,diatom_fo[mid_key].values,\
                marker='>',color='w',edgecolor=pcolors[i+1],label=holes[i]+':Diatom FO')


        for k in diatom_lo.index:
            plt.plot([diatom_lo.iloc[k][age_key],diatom_lo.iloc[k][age_key]],\
                 [diatom_lo.iloc[k][top_key],diatom_lo.iloc[k][bot_key]],'b-')
        plt.scatter(diatom_lo[age_key].values,diatom_lo[mid_key].values,\
                marker='<',color='w',edgecolor=pcolors[i+1],label=holes[i]+':Diatom LO')

# put on the pmag
        hole=datums[datums['Hole'].str.match(holes[i])]
        hole.reset_index(inplace=True)

        plt.scatter(hole['Age (Ma)'].values,hole[depth_key].values,\
            marker='*',s=size,color=colors[i],label=holes[i]+':PMAG')
        for k in hole.index:
             plt.plot([hole.iloc[k]['Age (Ma)'],hole.iloc[k]['Age (Ma)']],\
                 [hole.iloc[k]['top'],hole.iloc[k]['bot']],'k-')

        size=size-20 
    plt.ylim(dmax,dmin)
    plt.xlim(amin,amax)
    plt.xlabel('Age (Ma), GTS12')
    plt.ylabel('Depth (mbsf)')
    plt.title(title)
    #plt.legend(bbox_to_anchor=(1.5,1))
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

def kdes_for_incs(site_df,max_depth,interval=5,figsize=(2,12),depth_key='composite_depth',cmap='Blues'):
    start=0
    nplots=int(max_depth/interval)
    fig,ax=plt.subplots(nplots,1,figsize=figsize)
    fig.subplots_adjust(hspace=0,wspace=0)
    plt.xlabel('Inclination')
    ax[0].axhline(0,color='black')
    for i  in range(nplots):
        ax[i].xaxis.set_major_locator(plt.NullLocator())
        ax[i].yaxis.set_major_locator(plt.NullLocator())
        df=site_df[(site_df[depth_key]>=start)&(site_df[depth_key]<start+interval)]
        sns.kdeplot(df['dir_inc'],data2=df[depth_key],cmap=cmap,shade=True,ax=ax[i])
        ax[i].set_xlim(-90,90)
        ax[i].set_ylim(start+interval,start)
        ax[i].set_xlabel('')
        ax[i].axis('off')
        ax[i].axvline(-90,color='black')
        ax[i].axvline(90,color='black')
        start+=interval  
    ax[i].axhline(interval,color='black')
    return fig,ax 

def make_composite(affine_file,site,holes):
    first=True
    for hole in holes: #holes:
        adj_dec_df=pd.read_csv(hole+'/'+hole+'_dec_adjusted.csv')
        adj_dec_df['hole']=hole
        if first:
            site_df=pd.DataFrame(columns=adj_dec_df.columns)
            first=False
        adj_depth=convert_hole_depths(affine_file,adj_dec_df,site,hole)
        adj_depth.to_csv(hole+'/'+hole+'_depth_adjusted.csv',index=False)
        site_df=pd.concat([site_df,adj_depth])
    return site_df
    

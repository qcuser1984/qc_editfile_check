#!/home/geo2/anaconda3/bin/python

import os
from datetime import datetime

import pandas as pd
pd.set_option('display.max_columns', 50)
pd.set_option("display.max_rows", 50)


def sps_to_frame_skip(path_to_sps,char):
    '''get a number of rows to skip to account for header'''
    try:
        with open(path_to_sps, 'r',encoding='utf-8') as file:
            lines = file.readlines()
            first_data_line=[i for i in lines if i.startswith(char)][0]
            to_skip=int(lines.index(first_data_line))
            return(to_skip)
    except Exception as exc:
        print(f'Something went wrong: {exc}')
        

def th_sps_to_df(path_to_sps):
    '''read theretical S or R sps and return a frame'''
    if os.path.exists(path_to_sps):
        extension=os.path.splitext(os.path.split(path_to_sps)[1])[1]
        #print(extension)
        if extension not in ['.s01','.S01','.r01','.R01']:
            print(f'Unknown file extension {extension}')
        else:
            if extension in ['.r01','.R01']:
                df_out = pd.read_csv(path_to_sps,
                                    skiprows = sps_to_frame_skip(path_to_sps,'R'), sep = '\s+',
                                    names = ['code','line','point','idx','easting','northing','extras'])
                df_out.drop(columns = ['code','extras'], inplace = True)
                return df_out
            elif extension in ['.s01','.S01']:
                df_out= pd.read_csv(path_to_sps,
                                    skiprows = sps_to_frame_skip(path_to_sps,'S'), sep = '\s+',
                                    names = ['code','line','point','idx','easting','northing','extras'])               
                df_out.drop(columns = ['code','extras'], inplace = True)
                return df_out            
    else:
        print(f'No such file {path_to_sps}') 



def deployed_sps_to_df(path_to_sps):
    '''returns deployed rps as dataframe'''
    if os.path.exists(path_to_sps) and os.stat(path_to_sps).st_size>0: #check if file exists and not empty
        rows_to_skip= sps_to_frame_skip(path_to_sps,'R')   
        df_out = pd.read_fwf(path_to_sps,
            skiprows = rows_to_skip,
            colspecs = [(0,1),(2,8),(12,18),(23,24),(40,46),(47,55),(57,65),
                        (71,74),(74,80),(80,86),(95,98),(101,106)],
            names = ['code','line','point','index','w_depth','easting','northing',
                     'deploy_jd','deploy_time','node_heading','deploy_year','bumper']
                    )
        df_out['deploy_time_str'] = df_out['deploy_time'].astype(str)
        df_out['deploy_time_str'] = df_out['deploy_time_str'].apply(lambda x: x.zfill(6))
        df_out['deploy_jd_str'] = df_out['deploy_jd'].astype(str)
        df_out['deploy_jd_str'] = df_out['deploy_jd_str'].apply( lambda x : x.zfill(3))
        df_out['deploy_datetime_str'] = df_out['deploy_year'].astype(str) + df_out['deploy_jd_str'] + df_out['deploy_time_str']
        df_out['deploy_dttm']  = df_out['deploy_datetime_str'].apply(lambda x: datetime.strptime(x, '%y%j%H%M%S'))
        
        df_out['dive_time_delta'] = datetime.now() - df_out['deploy_dttm']
        df_out['dive_time_days'] = df_out['dive_time_delta'].apply(lambda x: x.total_seconds()/86400)
        df_out['dive_time_days'] = df_out['dive_time_days'].apply(lambda x: round(x,2)) 
        
        df_out.drop(columns = ['deploy_datetime_str','deploy_time_str','deploy_jd_str'],inplace=True)
        return df_out
        
    else:
        print(f'No such file: {path_to_sps}')
        return None
        
def recovered_sps_to_df(path_to_sps):
    '''returns recovered rps as dataframe or None'''
    if os.path.exists(path_to_sps) and os.stat(path_to_sps).st_size>0: #check if file exists and not empty
        rows_to_skip= sps_to_frame_skip(path_to_sps,'R')
        try:
            df_out = pd.read_fwf(path_to_sps,
            skiprows = rows_to_skip,
            colspecs = [(0,1),(2,8),(12,18),(23,24),(40,46),(47,55),(57,65),
                        (71,74),(74,80),(80,86),(86,89),(89,95),(95,98),(98,101),(101,106)],
            names = ['code','line','point','index','w_depth','easting','northing',
                     'deploy_jd','deploy_time','node_heading','recov_jd','recov_time','deploy_year','recov_year','bumper'] 
                    )
            df_out['deploy_time_str'] = df_out['deploy_time'].astype(str)
            df_out['deploy_time_str'] = df_out['deploy_time_str'].apply(lambda x: x.zfill(6))
            df_out['deploy_jd_str'] = df_out['deploy_jd'].astype(str)
            df_out['deploy_jd_str'] = df_out['deploy_jd_str'].apply( lambda x : x.zfill(3))
            df_out['deploy_datetime_str'] = df_out['deploy_year'].astype(str) + df_out['deploy_jd_str'] + df_out['deploy_time_str']
            df_out['deploy_dttm']  = df_out['deploy_datetime_str'].apply(lambda x: datetime.strptime(x, '%y%j%H%M%S'))

            df_out['recov_time_str'] = df_out['recov_time'].astype(str)
            df_out['recov_time_str'] = df_out['recov_time_str'].apply(lambda x : x.zfill(6))
            df_out['recov_jd_str'] = df_out['recov_jd'].astype(str)
            df_out['recov_jd_str'] = df_out['recov_jd_str'].apply(lambda x : x.zfill(3))
            df_out['recovery_datetime_str'] = df_out['recov_year'].astype(str) + df_out['recov_jd_str'] + df_out['recov_time_str']
            df_out['recovery_dttm'] = df_out['recovery_datetime_str'].apply(lambda x : datetime.strptime(x, '%y%j%H%M%S'))

            df_out['dive_time_delta'] = (df_out['recovery_dttm'] - df_out['deploy_dttm'])
            df_out['dive_time_days'] = df_out['dive_time_delta'].apply(lambda x: x.total_seconds()/86400)
            df_out['dive_time_days'] = df_out['dive_time_days'].apply(lambda x: round(x,2))

            df_out.drop(columns = ['recov_time_str','deploy_time_str','recovery_datetime_str','deploy_datetime_str','deploy_jd_str','recov_jd_str'], inplace =True)

            return df_out           
        except Exception as exc:
            print(f"Couldn't produce the data frame from {path_to_sps} d/t: {exc}")
            return None #return something to use later in code
    else:
        print(f"File: {os.path.split(path_to_sps)[1]} doesn't exist or empty")
        return None


def get_rcv_line_df(rcv_df,line_nb,short = True):
    '''return dataframe for particular receiver line'''
    if int(line_nb) in rcv_df['line'].unique():
        df_out = rcv_df[rcv_df['line'] == int(line_nb)]
        if short:
            if 'recovery_dttm' in list(df_out):
                df_out = df_out[['line', 'point','index','deploy_dttm', 'recovery_dttm']]
                return(df_out)
            else:
                df_out = df_out[['line', 'point','index','deploy_dttm']]
                return(df_out)
        else:
            return(df_out)
    return None

def get_line_matrix_stats(df_in):
    ''' return stats for matrix in form of list
        take a certain line df as input
    '''
    line = df_in['line'].unique()[0]
    deployed_count = df_in['line'].count()    
    deploy_start = datetime.strftime(df_in['deploy_dttm'].min(),"%Y-%m-%d %H:%M:%S" )
    deploy_end = datetime.strftime(df_in['deploy_dttm'].max(),"%Y-%m-%d %H:%M:%S" )
    
    if 'recov_time' in df_in.columns:    
        recovered_count = df_in['recov_year'].count() 
        recover_start = datetime.strftime(df_in['recovery_dttm'].min(),"%Y-%m-%d %H:%M:%S" )
        recover_end = datetime.strftime(df_in['recovery_dttm'].max(),"%Y-%m-%d %H:%M:%S" )
        return (line, deployed_count,  deploy_start, deploy_end, recovered_count, recover_start, recover_end)
    
    return (line, deployed_count, deploy_start, deploy_end)   


def back_to_date(str_date):
    '''getting transformed dates back together'''
    year = str_date[:2]
    jd = str_date[2:5]
    time = str_date[5:]
    if int(jd) > 365:
        jd = str(int(jd) - 365).zfill(3)
        year = str(int(year)+1)
        str_datetime = f"{year}{jd}{time}"
    else:
        str_datetime = str_date   
    return(str_datetime)

    
def source_sps_to_df(path_to_sps):
    '''return source sps as dataframe'''
    if os.path.exists(path_to_sps) and os.stat(path_to_sps).st_size > 0:
        rows_to_skip= sps_to_frame_skip(path_to_sps,'S') 
        try:
            df_out=pd.read_fwf(path_to_sps,
            skiprows = rows_to_skip,
            colspecs = [(0,1),(2,8),(12,18),(23,24),(30,34),(40,46),(47,55),(56,65),
                        (65,71),(71,74),(74,80),(74,87),(88,92),(92,95),(95,97),
                        (97,98),(98,99),(99,100),(100,101),(101,102),(103,108)  ],
            names = ['code','line','point','index','gun_depth','w_depth','easting','northing',
                    'tide','sp_jd','sp_time','sp_time_ms','sequence','azimuth','sp_year',
                    'depth_edit','timing_edit','pressure_edit','repeatability','positioning','dither']
                    )
            #update df here as well
            df_out['str_time'] = df_out['sp_time'].astype(str)
            df_out['str_time'] = df_out['str_time'].apply(lambda x: x.zfill(6))
            df_out['str_jd'] = df_out['sp_jd'].astype(str)
            df_out['str_jd'] = df_out['str_jd'].apply(lambda x: x.zfill(3))
            df_out["str_datetime"] = df_out["sp_year"].astype(str) + df_out["str_jd"] + df_out["str_time"]
            df_out["str_datetime"] = df_out["str_datetime"].apply(lambda x: back_to_date(x))
            df_out["sp_datetime"] = df_out["str_datetime"].apply(lambda x: datetime.strptime(x, "%y%j%H%M%S"))
            df_out.drop(columns = ['str_time', 'str_jd', 'str_datetime'], inplace = True)
            
            return df_out
        except Exception as exc:
            print(f"Couldn't produce the data frame from {path_to_sps} d/t {exc}")
            return None
    else:
        print(f"File {os.path.split(path_to_sps)[1]} doesn't exist or empty")
        return None

def fetch_lines_list(path_to_sps):
    '''try to quickly retrieve the list of lines'''
    if os.path.exists(path_to_sps):
        rows_to_skip= sps_to_frame_skip(path_to_sps,'S') 
        try:
            fast_df = pd.read_fwf(path_to_sps, skiprows = rows_to_skip, colspecs=[(2,8)], names = ['line']) 
            return fast_df.line.unique()
        except Exception as exc:
            print(f"Couldn't produce the data frame from {path_to_sps} d/t {exc}")    
    else:
        print(f"Couldn't find the file {os.path.split(path_to_sps)[1]}")

def get_sequence_df(df_in,seq_nb):
    '''return particular sequence dateframe'''
    if int(seq_nb) in df_in['sequence'].unique():
        df_out = df_in[df_in['sequence'] == int(seq_nb)]
        return(df_out)
    else:
        return None 

def get_line_df(df_in, line_nb):
    '''return line dataframe'''
    if int(line_nb) in df_in.line.unique():
        df_out = df_in[df_in.line == int(line_nb)]
        return(df_out)
    else:
        return None
    

def get_matrix_stats(df_in):
    ''' return list from sequence df that can be used to fill the matrix file '''
    sp_count = df_in['sp_datetime'].count()
    time_min, time_max = datetime.strftime(df_in['sp_datetime'].min(),"%Y-%m-%d %H:%M:%S"), datetime.strftime(df_in['sp_datetime'].max(),"%Y-%m-%d %H:%M:%S")
    source_line = df_in['line'].unique()[0]
    
    return [source_line, sp_count, time_min, time_max ]


def get_flags_counts(df_in):
    '''return flags counts and some stats from spsS_df'''
    depth = [i for i in df_in.depth_edit if i == 2]
    timing = [i for i in df_in.timing_edit if i == 2]
    pressure =[i for i in df_in.pressure_edit if i == 2]
    repeat = int(df_in.repeatability.sum())
    position = int(df_in.positioning.sum())
    total_flags = len(depth) + len(timing) + len(pressure) + repeat + position
    total_shots = len(df_in)
    void_shots_percent = round(total_flags/total_shots*100, 2)
    return({"Total shots" : total_shots, "Flaged shots": total_flags, "Flagged to Total (%)": void_shots_percent,\
        "Depth": len(depth), "Timing": len(timing),"Pressure": len(pressure),\
        "Repeatability": repeat, "Position quality": position})

def get_valid_shots_counts(df_in):
    '''return valid shots counts inside NTBP ranges'''
    pass


def accumulate_by_flag(df_in):
    df_out = df_in[df_in['positioning'] == 1]
    acc_df = df_out.groupby('sequence').count()
    
    return acc_df

def get_flagged_points(df_in,number):
    '''get the df with only paticular flag'''
    flags = ['depth_edit','timing_edit','pressure_edit','repeatability','positioning','dither']
    if number not in range(1,6):
        print(f"Incorrect flag number {number}")
    else:
        df_out = df_in[df_in[flags[number] == 1]]
        return(df_out)


    
def main():
    '''main test function below'''
    
    
    #print(f'Rows to skip for SPS theo: {sps_to_frame_skip(my_sps,"S")}')
    #print(f'Rows to skip for RPS theo: {sps_to_frame_skip(my_rps,"R")}')
    
    #df_out=th_sps_to_df(my_sps)
    #print(df_out.head())
    #print(df_out.tail())
    
    dep_df = deployed_sps_to_df(my_dep_rps)
    for i in dep_df['line'].unique():
        print(get_line_matrix_stats(get_rcv_line_df(dep_df,i)))
    #print(dep_df.head())
    #print(dep_df.tail())
    #line_df = get_rcv_line_df(dep_df,1461)
    #print(get_line_matrix_stats(line_df))
    #print(dep_df.columns)
    
    #dep_df_upd = update_nodes_df(dep_df)
    #print(dep_df_upd.head())
    #print(dep_df_upd.columns)
    
    
    #rec_df = recovered_sps_to_df(my_recov_rps)
    #for i in rec_df["line"].unique():
    #    print(get_line_matrix_stats(get_rcv_line_df(rec_df,i)))
    #dep_df = deployed_sps_to_df(my_dep_rps)
    #dep_line_df = get_rcv_line_df(dep_df,3393)
    #print(dep_line_df)
    #for line in [4865, 4911]:
    #    print(get_rcv_line_df(dep_df,line))
    #print (rec_df[rec_df['line'] == 3163])
    #print(rec_df.describe())
    #print(dep_df.describe())


    #
    # 
    # print(rec_df.head())
    #print(rec_df.tail())
    #print('recov_jd' in rec_df.columns)
    #rec_df_upd = update_nodes_df(rec_df)
    #print(rec_df_upd.head())
    #for line in [1185,1231]:
    #    print(get_rcv_line_df(rec_df,line))
    #line_df = get_rcv_line_df(rec_df,4221,short=False)
    #print("+++++++++++++++++++++++++++++++++")
    #print(line_df)
    #print(line_df.tail())
    
    
    #sps_df1 = source_sps_to_df(my_sps_raw)
    #
    #
    #sps_df2 = source_sps_to_df(my_sps_clean)
    #print(sps_df1.describe())
    #print(sps_df2.describe())
    
    #print(accumulate_by_flag(sps_df2))
    
    #for i in sps_df2['line'].unique():
    #    print(get_matrix_stats(get_line_df(sps_df2,i)))
    #
    #print(sps_df2.head())
    #print(sps_df2.tail())
    #print(sps_df.describe())
    #print(sps_df.line.unique())
    
    #print(get_flags_counts(sps_df1))
    #print(get_flags_counts(sps_df2))
    
    #print(fetch_lines_list(my_sps_clean))
    #sps_sline = get_line_df(sps_df, 3086)
    #sps_seq = get_sequence_df(sps_df, 285)
    #print(sps_seq.head())
    #print(sps_seq.tail())
    #
    #print(get_matrix_stats(sps_seq))
    
    #print(get_matrix_stats(sps_sline))
    
    
    #df_to_plot = sps_df.iloc[[index for index,row in sps_df.iterrows() if row['line'] in [3230, 2798, 2528]]]
    
    #print(df_to_plot.line.unique())
    #print(len(sps_df.line))
    

if __name__ == "__main__":
    my_sps=r'/qc/ITAPU/nav/preplot.s01'
    my_rps=r'/qc/ITAPU/nav/preplot.r01'
    my_dep_rps = r'/qc/ARAM/nav/Postplot_R/R_Deployed/BR001522_Deploy_progress.rps'
    my_recov_rps = r'/qc/ITAPU/nav/Postplot_R/R_Recovered/MT1001021_Recovery_progress.rps'
    my_sps_clean = r'/qc/ITAPU/nav/Postplot_S/All_Seq_Clean.s01'
    my_sps_raw = r'/qc/ITAPU/nav/Postplot_S/All_Seq_Raw.s01'
    main()

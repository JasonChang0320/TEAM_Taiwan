from read_tsmip import *
import os
import pandas as pd
import numpy as np
from tqdm import tqdm

Afile_path="data/Afile"
traces=pd.read_csv(f"{Afile_path}/2012-2020 traces (no 2020_7-9, broken data, double event).csv")
sampling_rate=200

add_columns=["p_picks (sec)","s_picks (sec)","pga","pga_time","pgv","pgv_time"]

traces[add_columns]=np.nan

error_file={"year":[],"month":[],"file":[],"reason":[]}

for trace_index in tqdm(traces.index):
    year=traces["year"][trace_index]
    month=traces["month"][trace_index]
    path=f"data/waveform/{year}/{month}"
    file_name=traces["file_name"][trace_index]
    if len(str(month))<2:
        month="0"+str(month)
    path=f"data/waveform/{year}/{month}"
    file_name=file_name.strip()
    try:
        trace=read_tsmip(f"{path}/{file_name}.txt")
        #picking
        p_pick,s_pick=ar_pick(trace[0],trace[1],trace[2],
                        samp_rate=sampling_rate,
                        f1=1, #Frequency of the lower bandpass window
                        f2=20, #Frequency of the upper bandpass window
                        lta_p=1, #Length of LTA for the P arrival in seconds
                        sta_p=0.1, #Length of STA for the P arrival in seconds
                        lta_s=4.0, #Length of LTA for the S arrival in seconds
                        sta_s=1.0, #Length of STA for the P arrival in seconds
                        m_p=2, #Number of AR coefficients for the P arrival
                        m_s=8, #Number of AR coefficients for the S arrival
                        l_p=0.1,
                        l_s=0.2,
                        s_pick=True)
        # p_pick,s_pick,fig=trace_pick_plot(trace,file_name)
        #get pga
        pga,pga_times=get_peak_value(trace)
        #get pgv
        vel_stream = get_integrated_stream(trace)
        pgv, pgv_times = get_peak_value(vel_stream)
        traces.loc[trace_index,"p_picks (sec)"]=p_pick
        traces.loc[trace_index,"s_picks (sec)"]=s_pick
        traces.loc[trace_index,"pga"]=pga 
        traces.loc[trace_index,"pga_time"]=pga_times
        traces.loc[trace_index,"pgv"]=pgv
        traces.loc[trace_index,"pgv_time"]=pgv_times
    except Exception as reason:
        print(file_name,f"year:{year},month:{month}, {reason}")
        error_file["year"].append(year)
        error_file["month"].append(month)
        error_file["file"].append(file_name)
        error_file["reason"].append(reason)
        continue

error_file_df=pd.DataFrame(error_file)
error_file_df["reason"]=error_file_df["reason"].astype(str)
# traces.to_csv(f"{Afile_path}/2012-2020 traces with picking and label.csv",index=False)
# error_file_df.to_csv(f"{Afile_path}/2012-2020 error in picking and label.csv",index=False)

#picking again
traces=pd.read_csv(f"{Afile_path}/2012-2020 traces with picking and label.csv")
traces['file_name'] = traces['file_name'].str.strip()
pick_again_filter=error_file_df["reason"].str.contains(r'^exception')

pick_again_df=error_file_df[pick_again_filter]

for i in pick_again_df.index:
    year=pick_again_df["year"][i]
    month=pick_again_df["month"][i]
    path=f"data/waveform/{year}/{month}"
    file_name=pick_again_df["file"][i]
    if len(str(month))<2:
        month="0"+str(month)
    path=f"data/waveform/{year}/{month}"
    file_name=file_name.strip()
    trace=read_tsmip(f"{path}/{file_name}.txt")
    #picking
    p_pick,s_pick=ar_pick(trace[0],trace[1],trace[2],
                    samp_rate=sampling_rate,
                    f1=1, #Frequency of the lower bandpass window
                    f2=20, #Frequency of the upper bandpass window
                    lta_p=1, #Length of LTA for the P arrival in seconds
                    sta_p=0.1, #Length of STA for the P arrival in seconds
                    lta_s=4.0, #Length of LTA for the S arrival in seconds
                    sta_s=1.0, #Length of STA for the P arrival in seconds
                    m_p=2, #Number of AR coefficients for the P arrival
                    m_s=8, #Number of AR coefficients for the S arrival
                    l_p=0.1,
                    l_s=0.2,
                    s_pick=True)
    #get pga
    pga,pga_times=get_peak_value(trace)
    #get pgv
    vel_stream = get_integrated_stream(trace)
    pgv, pgv_times = get_peak_value(vel_stream)

    insert_filter=((traces["year"]==year) & (traces["month"]==int(month)) & (traces["file_name"]==file_name))
    trace_index=traces[insert_filter].index[0]
    traces.loc[trace_index,"p_picks (sec)"]=p_pick
    traces.loc[trace_index,"s_picks (sec)"]=s_pick
    traces.loc[trace_index,"pga"]=pga 
    traces.loc[trace_index,"pga_time"]=pga_times
    traces.loc[trace_index,"pgv"]=pgv
    traces.loc[trace_index,"pgv_time"]=pgv_times

# others error: not no file or picking problem. result: txt file format problem
others_err_filter=error_file_df["reason"].str.contains(r'^\[Errno 2\]')
others_err_df=error_file_df[(~others_err_filter) & (~pick_again_filter)]

#drop pga NaN value
traces.dropna()
# traces.to_csv(f"{Afile_path}/2012-2020 traces with picking and label.csv",index=False)

#drop event don't have at least one trace
catalog=pd.read_csv(f"{Afile_path}/2012-2020 catalog (no 2020_7-9).csv")

check_filter=catalog["EQ_ID"].isin(traces["EQ_ID"])

catalog.drop(catalog[~check_filter].index,inplace=True)
# catalog.to_csv(f"{Afile_path}/final catalog.csv",index=False)
import os
import re 
import sys
import random 
from itertools import cycle
from time import sleep

import pandas as pd

from aux_functions import source_sps_to_df, th_sps_to_df, get_flags_counts
from extra_functions import get_all_sps, get_sequence_by_nb, name_to_numbers


def read_shots_edits(path_to_file):
    if os.path.exists(path_to_file):
        try:
            df_out = pd.read_csv(path_to_file, skiprows = 1,
            names = ['line','sequence','point','index','jd','code','qc_skips','missed_shots','total_skips','comment'])
            return df_out
        except Exception as exc:
            print(f"Something went wrong: {exc}")
            return None
    else:
        return None

def get_sequence(df_in, seq):
    if isinstance(df_in, pd.DataFrame):
        if int(seq) in df_in.sequence.unique(): 
            df_out = df_in[df_in["sequence"] == int(seq)]
            return(df_out)
        else:
            print(f"Sequence {seq} not found: either 0 flagged sp or it hasn't been added")
            return None
    else:
        return None

def main():
    sps_list = get_all_sps(path_to_sps_dir)
    seq_paths = get_sequence_by_nb(sps_list, seq_nb)
    if seq_paths is None:
        print(f"Couldn'find any files for sequence {seq_nb}, check number please")
        sys.exit(0)
    #sps block
    #get line number from file name 
    
    seq_line = name_to_numbers(os.path.split(seq_paths[0])[1])['line']
    seq_type = name_to_numbers(os.path.split(seq_paths[0])[1])['type']
    seq_index = name_to_numbers(os.path.split(seq_paths[0])[1])['index']
    print(f'\nLine number from {os.path.split(seq_paths[0])[1]} file name: {seq_line}')
    
    if seq_type == "N":
        print(f"Sequence {seq_nb} is NTBP")
    
    
    theo_sps = th_sps_to_df(path_to_theo_sps)
    theo_line_sps = theo_sps[theo_sps['line'] == seq_line]
    theo_points = theo_line_sps.point
    theo_SP = len(theo_points)
    print(f"Preplot:\nShotpoints nb: {len(theo_points)}\nShotpoints range: {int(theo_points.min())} - {int(theo_points.max())}")
    
    all_seq_clean = source_sps_to_df(path_to_all_clean)
    clean_line_sps = all_seq_clean[all_seq_clean['line'] == seq_line]
    clean_points = clean_line_sps.point
    clean_SP = len(clean_points)
    print(f"\nLine {seq_line} in {os.path.split(path_to_all_clean)[1]}:\nShot points: {clean_SP} ({round(clean_SP/theo_SP*100,2)}% complete).")
    
    #first case we have S01 and clean.S01
    if len(seq_paths) == 2:
        seq_s01 = seq_paths[0]
        seq_clean = seq_paths[1]
        
        s01_df = source_sps_to_df(seq_s01)
        clean_df = source_sps_to_df(seq_clean)
        
        #make couple of assumptions
        s01_SP = len(s01_df)
        theo_vs_s01 = theo_SP - s01_SP
        
        if 1 <= theo_vs_s01 <= 15:
            print(f"\nProbably {theo_vs_s01} shots were missed") if theo_vs_s01 > 1 else print(f"\nProbably {theo_vs_s01} shot was missed")
        elif theo_vs_s01 > 15 and seq_index == 1:
            print(f"\nSP mising: {theo_vs_s01}. Incomplete Source line")
        elif theo_vs_s01 > 15 and seq_index > 1:
            print(f"\nSP mising: {theo_vs_s01}. Reshoot of line {seq_line}.")
        
        
        print(f"\n{os.path.split(seq_s01)[1]}")
        sp_range = s01_df.point
        print(f"Shotpoints range: {sp_range[0]} - {sp_range[len(sp_range)-1]}")
        for k, v in get_flags_counts(s01_df).items():
            if v != 0:
                print(f"{k}: {v}")
        
        print(f"\n{os.path.split(seq_clean)[1]}")
        sp_range = clean_df.point
        print(f"Shotpoints range: {sp_range[0]} - {sp_range[len(sp_range)-1]}")
        for k, v in get_flags_counts(clean_df).items(): # get flag counts function
            if v != 0:
                print(f"{k}: {v}")
    
    #second case: S01 only
    #make couple of assumptions
    elif len(seq_paths) == 1:
        seq_s01 = seq_paths[0]
        print(f"\n{os.path.split(seq_s01)[1]}")
        
        s01_df = source_sps_to_df(seq_s01)
        s01_SP = len(s01_df)
        
        theo_vs_s01 = theo_SP - s01_SP
        if 1 <= theo_vs_s01 <= 15:
            print(f"\nProbably {theo_vs_s01} shots were missed") if theo_vs_s01 > 1 else print(f"\nProbably {theo_vs_s01} shot was missed")
        elif theo_vs_s01 > 15 and seq_index == 1:
            print(f"\nSP mising: {theo_vs_s01}. Incomplete/aborted Source line.")
        elif theo_vs_s01 > 15 and seq_index > 1:
            print(f"\nSP mising: {theo_vs_s01}. Reshoot of line {seq_line}.")
        
        
        for k, v in get_flags_counts(s01_df).items():
            if v != 0:
                print(f"{k}: {v}")
    
    else:
        print(f"Too many SPS files {len(seq_paths)}")
        sys.exit(0)
    
    
    #QC shot edit files block
    print(f"\n{os.path.split(prod_shot_edit)[1]}: sequence {seq_nb}\n")
    
    shots_edit = read_shots_edits(prod_shot_edit)
    seq_df = get_sequence(shots_edit, seq_nb)
    
    if isinstance(seq_df, pd.DataFrame):
        SP_edit = len(seq_df)
    else:
        pass
    
    if isinstance(seq_df, pd.DataFrame):
        seq_df = seq_df.drop_duplicates(subset = ['point'])
        #print('\n')
        gr_df = seq_df.groupby(['comment'])[['code','total_skips']].count()
        comments = [' Missing SP.', 'missed shot, no trigger']
        remove_df = gr_df.query("comment != @comments")
        print(gr_df)
        to_remove = remove_df["total_skips"].sum()
        print(f"\nTotal:\n{SP_edit} SPs in the edit list\n{to_remove} SPs to be removed (Missed SPs not counted)")
    else: 
        pass

if __name__ == "__main__":
    #prod_shot_edit = r"X:\Projects\07_BR001522_ARAM_Petrobras\05_QC\03_GUNS\05_Sequences\01_Artemis_Odyssey\0256-QC_edited_shots.csv"
    path_to_sps_dir = r"X:\Projects\07_BR001522_ARAM_Petrobras\05_QC\03_GUNS\05_Sequences\01_Artemis_Odyssey"
    prod_shot_edit = os.path.join(path_to_sps_dir, "0256-QC_edited_shots.csv")
    path_to_theo_sps = r"Q:\06-ARAM\nav\preplot.s01"
    path_to_all_clean = r"Q:\06-ARAM\nav\Postplot_S\All_Seq_Clean.s01"

    
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]}: seq_nb, eg {random.randint(1,999)}")
        sys.exit(1)
    else:
        try:
            seq_nb = int(sys.argv[1])
        except ValueError as err:
            print(f"Incorrect value {sys.argv[1]}")
            sys.exit(1)
    main()
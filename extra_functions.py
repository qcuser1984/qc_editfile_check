#some functions for searching the sequnce files 
# in the current directory structure 
import os
import sys
import re 

def name_to_numbers(file_name):
    '''from name of the file return dictionary with line, type, index, sequence keys'''
    pattern = re.compile(r"\d+-(\d+)(\w{1})(\d{1})(\d{3})")
    try:
        line,acc_type,idx,sequence = pattern.search(file_name).groups()
        return({'line':int(line),'type': acc_type, 'index': int(idx), 'sequence': int(sequence)})
    except AttributeError as err:
        print(f'Bad value {file_name}: {err}')

def get_sequence(path_to_dir,sequence_nb):
    '''Recursively search for SPS file providing just the root directory'''
    try:
        my_list = [os.path.join(dirs, file) for dirs, subdirs, files in os.walk(path_to_dir) for file in files if file.endswith(".S01")]
        if len(my_list)>0:
            my_files = [file for file in my_list if name_to_numbers(os.path.split(file)[1])[3] == int(sequence_nb)]
            return(my_files)
        else:
            print(f"No sps for {sequnce_nb}")
    except Exception as exc:
        print(f"Couldn't get the list of files with extension {ext} d/t {exc}")




def get_all_sps(path_to_dir):
        try:
            sps_list = [os.path.join(dirs, file) for dirs, subdirs, files in os.walk(path_to_dir) for file in files if file.endswith(".S01")]
            return(sps_list)
        except Exception as exc:
            print(f"Couldn't make the lsit of SPS, d/t: {exc}")



def get_sequence_by_nb(sps_list,seq_nb):
    if len(sps_list) > 0:
        unq_seq_list = set([name_to_numbers(os.path.split(file)[1])['sequence'] for file in sps_list])
        if seq_nb in unq_seq_list:
            seq_files = [file for file in sps_list if name_to_numbers(os.path.split(file)[1])['sequence'] == seq_nb ]
            return seq_files
        else:
            print(f'Sequence {seq_nb} not in provided list of paths ')
            return
    else:
        print(f'No paths in the list')
        return

def get_file_stats(path_to_file):
    #assert os.path.exists(path_to_file), f"No such file {path_to_file}"
    if os.path.exists(path_to_file) and os.stat(path_to_file).st_size > 0:
        file_m_time = os.stat(path_to_file).st_mtime 
        file_size = os.stat(path_to_file).st_size
        return (file_m_time, file_size)
    return None



def main():
    sps_list = get_all_sps(path_to_sps_dir)
    print(len(sps_list))
    my_seq_list =  get_sequence_by_nb(sps_list, seq_nb)
    print(my_seq_list)
    
    

if __name__ == "__main__":
    path_to_sps_dir = r"X:\Projects\06_BR21T01_ITAPU_Petrobras\05_QC\03_GUNS\05_Sequences\01_Artemis_Odyssey"
    seq_nb = int(sys.argv[1])
    main()


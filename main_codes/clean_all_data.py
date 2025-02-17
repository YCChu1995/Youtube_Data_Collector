from time import time
import os
from sys import path as sys_path
sys_path += ['modules']
from utilities import load_configs, get_refined_time_string

def clean_all_data():
    start_time: float = time()

    DIRECTORIES: dict[str, str] = load_configs()['folder_name_to_save_data']
    cleaned_data_count: int = 0

    for DIRECTORY in DIRECTORIES.values():
        for file_name in os.listdir(DIRECTORY):
            os.remove(DIRECTORY+'/'+file_name)
            cleaned_data_count += 1

    if cleaned_data_count == 0:
        print(f"Data folders were all empty !", end='\n', flush=True)
    else:
        running_time: str = get_refined_time_string(time() - start_time)
        print(f"\033[92m{cleaned_data_count}\033[0m data files cleaned in \033[92m{running_time}\033[0m !", end='\n', flush=True)

if __name__ == '__main__':
    clean_all_data()
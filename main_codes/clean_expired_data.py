from datetime import datetime
from time import time
import os
from sys import path as sys_path
sys_path += ['modules']
from utilities import load_configs, get_refined_time_string

def get_date_a_month_ago() -> int:
    CURRENT_DATE: int = int(datetime.now().strftime("%Y%m%d"))
    CURRENT_MONTH: int = CURRENT_DATE // 100 % 100

    if CURRENT_MONTH == 1:
        return CURRENT_DATE - 8900
    else:
        return CURRENT_DATE - 100

def clean_expired_data():
    start_time: float = time()

    DIRECTORIES: dict[str, str] = load_configs()['folder_name_to_save_data']
    EXPIRED_DATE: int = get_date_a_month_ago()
    expired_data_count: int = 0

    for DIRECTORY in DIRECTORIES.values():
        for file_name in os.listdir(DIRECTORY):
            if int(file_name[:8]) < EXPIRED_DATE:
                os.remove(DIRECTORY+'/'+file_name)
                expired_data_count += 1

    if expired_data_count == 0:
        print(f"Data folder had no expired data !", end='\n', flush=True)
    else:
        running_time: str = get_refined_time_string(time() - start_time)
        print(f"\033[92m{expired_data_count}\033[0m expired data files cleaned in \033[92m{running_time}\033[0m !", end='\n', flush=True)

if __name__ == '__main__':
    clean_expired_data()
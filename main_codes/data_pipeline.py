from sys import path as sys_path
sys_path += ['modules', 'modules/data collector']
from data_collector import DataCollector
from utilities import load_configs

if __name__ == '__main__':
    data_collector = DataCollector('TW', show_progress_bar=False)

    for interested_category in load_configs()['folder_name_to_save_data'].keys():
        data_collector.set_interest_categories(interested_category)
        data_collector.collect_videos(max_videos=10, max_comments=100)
        data_collector.store_data()
        data_collector.clean_cached_data()

    data_collector.upload_data_to_google_drive()

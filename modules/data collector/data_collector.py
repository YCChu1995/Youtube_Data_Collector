from enum import Enum
from dataclasses import dataclass
import pandas as pd
import datetime
from googleapiclient.http import MediaFileUpload
from time import time
from sys import path as sys_path
sys_path += ['modules']
from utilities import load_configs, get_progress_bar_text, get_refined_time_string, build_google_drive_service
from youtube_crawler import YouTubeVideo, YouTubeCrawler
from youtube_data import YouTubeVideoInfo, YouTubeVideoStatistics, YouTubeVideoComments

@dataclass
class DataCollector:
    __youtube_videos: list[YouTubeVideo]
    __youtube_crawler: YouTubeCrawler
    __show_progress_bar: bool
    __current_timestamp: str
    __interested_category: str = "trending"

    def __init__(self, location: str, show_progress_bar: bool = True):
        start_time: float = time()
        
        self.__youtube_crawler = YouTubeCrawler(location)
        self.__youtube_videos = []
        self.__show_progress_bar = show_progress_bar
        self.__current_timestamp = datetime.datetime.now().strftime("%Y%m%d%H")
        
        running_time: str = get_refined_time_string(time() - start_time)
        print(f"Data_Collector initialized in \033[92m{running_time}\033[0m !", end='\n', flush=True)
    
    def clean_cached_data(self):
        self.__youtube_videos = []

    def set_interest_categories(self, interested_category: str):
        if interested_category not in load_configs()['folder_name_to_save_data'].keys():
            raise ValueError(f"\n\033[91mInvalid input of \"interested_category\"\033[0m: {interested_category}\n\033[92mValid input\033[0m: the key of \"config.yaml[folder_name_to_save_data]\".\n\033[96mExample\033[0m: {tuple(load_configs()['folder_name_to_save_data'].keys())}")

        self.__interested_category = interested_category

    def collect_videos(self, max_videos: int, max_comments: int):
        if self.__interested_category == "trending":
            self.__collect_trending_videos(max_videos=max_videos, max_comments=max_comments)
        else:
            self.__collect_searched_videos(query=self.__interested_category, max_videos=max_videos, max_comments=max_comments)
 
    def __collect_trending_videos(self, max_videos: int, max_comments: int):
        start_time: float = time()

        videos = self.__youtube_crawler.get_trending_videos(max_videos)

        for index_video, video in enumerate(videos):
            self.__youtube_videos.append(
                YouTubeVideo(
                    info=video, 
                    statistics=self.__youtube_crawler.get_video_statistics(video.video_id), 
                    comments=self.__youtube_crawler.get_video_comments(video.video_id, max_comments)
                )
            )

            if self.__show_progress_bar:
                print(f"\rCollecting Data: {get_progress_bar_text( (index_video + 1) / len(videos) )}", end='', flush=True)
        else:
            if self.__show_progress_bar: print()

            running_time: str = get_refined_time_string(time() - start_time)
            print(f"Data (trending) collected in \033[92m{running_time}\033[0m !", end='\n', flush=True)
    
    def __collect_searched_videos(self, query: str, max_videos: int, max_comments: int):
        start_time: float = time()

        videos = self.__youtube_crawler.get_searched_videos(query, max_videos)

        for index_video, video in enumerate(videos):
            self.__youtube_videos.append(
                YouTubeVideo(
                    info=video, 
                    statistics=self.__youtube_crawler.get_video_statistics(video.video_id), 
                    comments=self.__youtube_crawler.get_video_comments(video.video_id, max_comments)
                )
            )
            
            if self.__show_progress_bar:
                print(f"\rCollecting Data: {get_progress_bar_text( index_video / len(videos))}", end='', flush=True)
        else:
            if self.__show_progress_bar: print()

            running_time: str = get_refined_time_string(time() - start_time)
            print(f"Data ({query}) collected in \033[92m{running_time}\033[0m !", end='\n', flush=True)

    def __prepare_data_to_store(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        '''
        Prepare data to store in local or online storage
        
        Returns:
            (video_info_df, video_comments_df, channels_df) : tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        
        Example:
            video_info_df: pd.DataFrame
            video_comments_df: pd.DataFrame
            channels_df: pd.DataFrame
            video_info_df, video_comments_df, channels_df = self.__prepare_data_to_store()
        '''
        video_info_list = [['video_id', 'title', 'channel', 'published_time', 'description', 'thumbnails', 'view_count', 'like_count']]
        video_comments_list = [['video_id', 'text', 'like_count', 'reply_count']]
        channels_list = [['channel_id', 'title', 'description', 'subscribers', 'thumbnails']]
        seen_channel_ids = set()

        for index_video, video in enumerate(self.__youtube_videos):
            video_info: YouTubeVideoInfo = video.get_info()
            statistics: YouTubeVideoStatistics = video.get_statistics()
            video_comments:YouTubeVideoComments = video.get_comments()
            video_info_list.append([video_info.video_id, video_info.title, video_info.channel, video_info.published_time, video_info.description, video_info.thumbnails, statistics.view_count, statistics.like_count])
            for video_comment in video_comments:
                video_comments_list.append([video_info.video_id, video_comment.text, video_comment.like_count, video_comment.reply_count])
            if video_info.channel_id not in seen_channel_ids:
                seen_channel_ids.add(video_info.channel_id)
                channels_list.append([video_info.channel_id, video_info.channel, None, None, None])

            if self.__show_progress_bar:
                print(f"\rPreparing data to store: {get_progress_bar_text( index_video / len(self.__youtube_videos) )}", end='', flush=True)
        else:
            if self.__show_progress_bar: print(f"\rPreparing data to store: {get_progress_bar_text(1)}")

        video_info_df = pd.DataFrame(video_info_list[1:], columns=video_info_list[0])
        video_comments_df = pd.DataFrame(video_comments_list[1:], columns=video_comments_list[0])
        channels_df = pd.DataFrame(channels_list[1:], columns=channels_list[0])

        return video_info_df, video_comments_df, channels_df

    def store_data(self):
        start_time: float = time()

        config: dict[str, any] = load_configs()
        FOLDER_PATH: str = config['folder_name_to_save_data'][self.__interested_category]
        FILE_NAMES: dict[str, str] = config['file_names_of_saved_data']

        video_info_df: pd.DataFrame
        video_comments_df: pd.DataFrame
        channels_df: pd.DataFrame
        video_info_df, video_comments_df, channels_df = self.__prepare_data_to_store()

        video_info_df.to_parquet(f"{FOLDER_PATH}/{self.__current_timestamp}_{FILE_NAMES['video_info']}", index=False)
        video_comments_df.to_parquet(f"{FOLDER_PATH}/{self.__current_timestamp}_{FILE_NAMES['video_comments']}", index=False)
        channels_df.to_parquet(f"{FOLDER_PATH}/{self.__current_timestamp}_{FILE_NAMES['channel_info']}", index=False)

        running_time: str = get_refined_time_string(time() - start_time)
        print(f"Data ({self.__interested_category}) stored in \033[92m{running_time}\033[0m !", end='\n', flush=True)

    def __upload_a_category_data_to_google_drive(self, interested_category: str):
        if interested_category not in load_configs()['folder_name_to_save_data'].keys():
            raise ValueError(f"\n\033[91mInvalid input of \"interested_category\"\033[0m: {interested_category}\n\033[92mValid input\033[0m: the key of \"config.yaml[folder_name_to_save_data]\".\n\033[96mExample\033[0m: {tuple(load_configs()['folder_name_to_save_data'].keys())}")

        config: dict[str, any] = load_configs()
        FOLDER_PATH: str = config['folder_name_to_save_data'][interested_category]
        FILE_NAMES: dict[str, str] = config['file_names_of_saved_data']
        PARENT_FOLDER_ID: str = config['parent_folder_id_to_upload_data'][interested_category]

        google_drive_service: any = build_google_drive_service()

        for file_name in FILE_NAMES.values():
            file_metadata: dict[str, any] = {
                'name': self.__current_timestamp+'_'+file_name,
                'parents': [PARENT_FOLDER_ID]
            }
            media = MediaFileUpload(f'{FOLDER_PATH}/{self.__current_timestamp}_{file_name}', mimetype='application/octet-stream')
            google_drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    def upload_data_to_google_drive(self):
        start_time: float = time()

        for interested_category in load_configs()['folder_name_to_save_data'].keys():
            self.__upload_a_category_data_to_google_drive(interested_category)

        running_time: str = get_refined_time_string(time() - start_time)
        print(f"Data uploaded in \033[92m{running_time}\033[0m !", end='\n', flush=True)

if __name__ == '__main__':
    data_collector = DataCollector('TW', show_progress_bar=False)

    data_collector.set_interest_categories('trending')
    data_collector.collect_videos(max_videos=1, max_comments=1)
    data_collector.store_data()
    data_collector.clean_cached_data()

    data_collector.set_interest_categories('news')
    data_collector.collect_videos(max_videos=1, max_comments=1)
    data_collector.store_data()
    data_collector.clean_cached_data()

    data_collector.set_interest_categories('politics')
    data_collector.collect_videos(max_videos=1, max_comments=1)
    data_collector.store_data()
    data_collector.clean_cached_data()

    data_collector.upload_data_to_google_drive()

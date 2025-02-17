from dataclasses import dataclass
from typing import Optional
from googleapiclient.discovery import build, Resource
import os
from sys import path as sys_path
sys_path += ['modules']
from utilities import load_configs
from youtube_data import YouTubeVideoInfo, YouTubeVideoStatistics, YouTubeVideoComments
from datetime import datetime, timedelta

@dataclass
class YouTubeCrawler:
    __youtube_service: Resource
    __region_code: str
    __show_errors: bool = False

    def __init__(self, location: str):
        self.__youtube_service = build(serviceName='youtube', version='v3', developerKey=os.getenv('YOUTUBE_API_KEY'))
        self.__region_code = location

    def set_region_code(self, location: str):
        self.__region_code = location

    def set_show_errors(self, show_errors: bool):
        self.__show_errors = show_errors

    def get_searched_videos(self, query: str, max_results: int) -> list[YouTubeVideoInfo]:
        # Calculate the date one week ago from today
        one_week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat("T") + "Z"

        searched_response = self.__youtube_service.search().list(
            q=query,
            part='id,snippet',
            regionCode=self.__region_code,
            maxResults=max_results,
            publishedAfter=one_week_ago,
            order='viewCount'
        ).execute()

        videos: list[YouTubeVideoInfo] = []
        for searched_result in searched_response.get('items', []):
            if searched_result['id']['kind'] == 'youtube#video':
                videos.append(
                    YouTubeVideoInfo(
                        title=searched_result['snippet']['title'],
                        channel=searched_result['snippet']['channelTitle'],
                        channel_id=searched_result['snippet']['channelId'],
                        published_time=searched_result['snippet']['publishedAt'],
                        description=searched_result['snippet']['description'],
                        video_id=searched_result['id']['videoId'],
                        thumbnails=searched_result['snippet']['thumbnails']
                    )
                )

        return videos

    def get_trending_videos(self, max_results: int) -> list[YouTubeVideoInfo]:
        trending_response = self.__youtube_service.videos().list(
            part='id,snippet',
            chart='mostPopular',
            regionCode=self.__region_code,
            maxResults=max_results
        ).execute()

        videos: list[YouTubeVideoInfo] = []
        for trending_result in trending_response.get('items', []):
            videos.append(
                YouTubeVideoInfo(
                    title=trending_result['snippet']['title'],
                    channel=trending_result['snippet']['channelTitle'],
                    channel_id=trending_result['snippet']['channelId'],
                    published_time=trending_result['snippet']['publishedAt'],
                    description=trending_result['snippet']['description'],
                    video_id=trending_result['id'],
                    thumbnails=trending_result['snippet']['thumbnails']
                )
            )

        return videos

    def get_video_statistics(self, video_id: str) -> YouTubeVideoStatistics:
        video_response = self.__youtube_service.videos().list(
            part='statistics',
            id=video_id
        ).execute()

        video_statistics: YouTubeVideoStatistics = YouTubeVideoStatistics(view_count=None, like_count=None, dislike_count=None, comment_count=None)
        if 'items' in video_response and len(video_response['items']) > 0:
            video_statistics.view_count = int(video_response['items'][0]['statistics'].get('viewCount', 0))
            video_statistics.like_count = int(video_response['items'][0]['statistics'].get('likeCount', 0))
            video_statistics.dislike_count = int(video_response['items'][0]['statistics'].get('dislikeCount', 0))
            video_statistics.comment_count = int(video_response['items'][0]['statistics'].get('commentCount', 0))
        return video_statistics

    def get_video_comments(self, video_id: str, max_comments: int) -> list[YouTubeVideoComments]: # FIXME handle error when there are no comments
        comments:list[YouTubeVideoComments] = []
        next_page_token = None

        while True:
            try:
                comments_response = self.__youtube_service.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=3, # FIXME for testing purposes, change this to 100
                    pageToken=next_page_token,
                    order='relevance'
                ).execute()
            except Exception as e:
                if self.__show_errors:
                    print('-'*50)
                    print(f"\033[91mAn error occurred\033[0m:\n{e}")
                    print('-'*50)
                break

            for comment_thread in comments_response.get('items', []):
                comment_info = comment_thread['snippet']['topLevelComment']['snippet']
                total_reply_count=comment_thread['snippet']['totalReplyCount']
                comments.append(
                    YouTubeVideoComments(
                        author=comment_info['authorDisplayName'],
                        text=comment_info['textDisplay'],
                        like_count=comment_info['likeCount'],
                        reply_count=total_reply_count,
                        published_time=comment_info['publishedAt']
                    )
                )
                if len(comments) >= max_comments: break

            next_page_token = comments_response.get('nextPageToken')
            if not next_page_token or len(comments) >= max_comments: break

        return comments

    def __clean_text_with_special_strings(self, text: str) -> str:
        special_strings             = ['\n', '\r', '\t', '\\', '&#39;', '&amp;']#, '&quot;', '&lt;', '&gt;']
        special_string_replacements = [''  , ''  , ' ' , ''  , '\''   , '&'    ]#, '\"'    , '<'    , '>'  ]
        return text.replace(special_strings[0], special_string_replacements[0]).replace(special_strings[1], special_string_replacements[1]).replace(special_strings[2], special_string_replacements[2]).replace(special_strings[3], special_string_replacements[3]).replace(special_strings[4], special_string_replacements[4]).replace(special_strings[5], special_string_replacements[5])#.replace(special_strings[6], special_string_replacements[6]).replace(special_strings[7], special_string_replacements[7]).replace(special_strings[8], special_string_replacements[8])
@dataclass
class YouTubeVideo:
    __info: YouTubeVideoInfo
    __statistics: Optional[YouTubeVideoStatistics]
    __comments: list[YouTubeVideoComments]

    def __init__(self, info: YouTubeVideoInfo, statistics: Optional[YouTubeVideoStatistics] = None, comments: list[YouTubeVideoComments] = []):
        self.__info = info
        self.__statistics = statistics
        self.__comments = comments

    def get_info(self) -> YouTubeVideoInfo:
        return self.__info
    
    def get_statistics(self) -> Optional[YouTubeVideoStatistics]:
        return self.__statistics
    
    def get_comments(self) -> list[YouTubeVideoComments]:
        return self.__comments
    
    def set_statistics(self, statistics: YouTubeVideoStatistics):
        self.__statistics = statistics
    
    def clean_comments(self):
        self.__comments = []
    
    def append_comments(self, comments: list[YouTubeVideoComments]):
        self.__comments += comments

# Test 'YouTubeCrawler'
if __name__ == "__main__":
    # Initialize the YouTubeCrawler with a region code
    crawler = YouTubeCrawler(location='TW')

    # Search for videos with a specific query
    search_query = "政治新聞"
    searched_videos = crawler.get_searched_videos(query=search_query, max_results=3)
    print(f"Searched Videos for query '{search_query}':")
    for video in searched_videos:
        print(f"Title: {video.title}, Channel: {video.channel}, Published At: {video.published_time}")

    # Get trending videos
    # trending_videos = crawler.get_trending_videos(max_results=1)
    # print("\nTrending Videos:")
    # for video in trending_videos:
    #     print(f"Title: {video.title}, Channel: {video.channel}, Published At: {video.published_time}")

    # Get statistics for a specific video
    if searched_videos:
        video_id = searched_videos[0].video_id
        # video_id = trending_videos[0].video_id
        video_statistics = crawler.get_video_statistics(video_id=video_id)
        print(f"\nStatistics for video ID '{video_id}':")
        print(f"Views: {video_statistics.view_count}, Likes: {video_statistics.like_count}, Comments: {video_statistics.comment_count}")

    # Get comments for a specific video
    if searched_videos:
        video_id = searched_videos[0].video_id
        # video_id = trending_videos[0].video_id
        video_comments = crawler.get_video_comments(video_id=video_id, max_comments=5)
        print(f"\nComments for video ID '{video_id}':")
        for comment in video_comments:
            print(f"Author: {comment.author}, Comment: {comment.text}, Likes: {comment.like_count}, Replies: {comment.reply_count}")

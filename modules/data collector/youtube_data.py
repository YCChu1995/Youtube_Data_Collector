from dataclasses import dataclass

@dataclass
class YouTubeVideoStatistics:
    view_count: int
    like_count: int
    dislike_count: int
    comment_count: int
    
@dataclass
class YouTubeVideoComments:
    author: str
    text: str
    like_count: int
    reply_count: int
    published_time: str

@dataclass
class YouTubeVideoInfo:
    title: str
    channel: str
    channel_id: str
    published_time: str
    description: str
    video_id: str
    thumbnails: dict

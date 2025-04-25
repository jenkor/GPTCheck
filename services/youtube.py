import re
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, List, Dict, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_video_id(url: str) -> Optional[str]:
    """
    Extract the YouTube video ID from a URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Video ID or None if extraction fails
    """
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

def get_youtube_video_title(url: str) -> Optional[str]:
    """
    Get the title of a YouTube video from its URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Video title or None if retrieval fails
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find("meta", property="og:title")
            if title_tag:
                return title_tag["content"]
            else:
                logger.warning("Title tag not found.")
                return None
        else:
            logger.error(f"Failed to fetch the YouTube page. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"An error occurred while fetching video title: {e}")
        return None

def get_transcript(video_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get the transcript for a YouTube video.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        List of transcript segments or None if retrieval fails
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])
        return transcript.fetch()
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        return None

def split_transcript_with_timestamps(transcript_data: List[Dict[str, Any]], max_length: int = 15385) -> List[Dict[str, Any]]:
    """
    Split a transcript into parts, each with a maximum text length.
    
    Args:
        transcript_data: List of transcript segments
        max_length: Maximum text length for each part
        
    Returns:
        List of transcript parts with start and end timestamps
    """
    parts = []
    current_part = []
    current_length = 0
    start_time = 0

    for item in transcript_data:
        text = item['text']
        start = item['start']
        duration = item['duration']
        end_time = start + duration
        
        if current_length + len(text) + 1 > max_length:
            parts.append({
                "text": " ".join(current_part),
                "start_time": start_time,
                "end_time": start
            })
            current_part = [text]
            current_length = len(text)
            start_time = start
        else:
            current_part.append(text)
            current_length += len(text) + 1

    if current_part:
        parts.append({
            "text": " ".join(current_part),
            "start_time": start_time,
            "end_time": end_time
        })

    return parts 
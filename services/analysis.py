import openai
import logging
from typing import List, Dict, Any, Optional
from .youtube import get_video_id, get_youtube_video_title, get_transcript, split_transcript_with_timestamps
import asyncio
import os
import json
import hashlib
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)

def process_video(youtube_url: str, api_key: str) -> str:
    """
    Process a YouTube video for analysis.
    
    Args:
        youtube_url: YouTube video URL
        api_key: OpenAI API key
        
    Returns:
        HTML-formatted analysis result
    """
    video_id = get_video_id(youtube_url)
    if video_id is None:
        return "Failed to extract video ID."
    
    video_title = get_youtube_video_title(youtube_url)
    if video_title is None:
        video_title = "Unknown Title"

    # Check if we have a cached result
    if current_app:
        cache_dir = current_app.config.get('CACHE_DIR')
        if cache_dir:
            cache_key = hashlib.md5(video_id.encode('utf-8')).hexdigest()
            cache_file = os.path.join(cache_dir, f"{cache_key}.json")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    if 'analysis' in cached_data:
                        logger.info(f"Using cached analysis for video {video_id}")
                        return cached_data['analysis']

    transcript_data = get_transcript(video_id)
    if not transcript_data:
        return "Failed to retrieve transcript."

    transcript_parts_with_timestamps = split_transcript_with_timestamps(transcript_data)
    
    # Process each transcript part
    analyses = []
    for part in transcript_parts_with_timestamps:
        section = part['text']
        analysis_result = analyze_and_summarize_section(section, api_key)
        analyses.append(analysis_result)

    if not analyses:
        return "No analyses were generated."

    # Generate a comprehensive summary from all analyses
    comprehensive_summary = generate_comprehensive_summary(analyses, video_title, api_key)
    
    # Cache result if possible
    if current_app and cache_dir:
        try:
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump({
                    'title': video_title,
                    'video_id': video_id,
                    'analysis': comprehensive_summary
                }, f)
        except Exception as e:
            logger.error(f"Error caching analysis: {e}")
    
    return comprehensive_summary

def analyze_and_summarize_section(section: str, api_key: str) -> str:
    """
    Analyze a section of transcript text using OpenAI.
    
    Args:
        section: Transcript text section
        api_key: OpenAI API key
        
    Returns:
        Analysis text
    """
    try:
        # Use the provided API key for this request
        openai.api_key = api_key
        
        analysis_prompt = ("Please analyze the following text and provide a structured response with the following headings: "
                           "Historical Accuracy, Scientific Accuracy, Speculative Claims, and Religious/Mythological References.\n\n"
                           "Text: \"" + section + "\"\n\n"
                           "Response:")
        
        analysis_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": analysis_prompt}
            ],
            temperature=0.5,
            max_tokens=4096,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return analysis_response.choices[0].message['content']
    except Exception as e:
        logger.error(f"Error in section analysis: {e}")
        return "Analysis failed."

def create_summary_prompt(analysis_results: List[str], video_title: str) -> str:
    """
    Create a prompt for generating a comprehensive summary from section analyses.
    
    Args:
        analysis_results: List of section analysis results
        video_title: Title of the video
        
    Returns:
        Summary prompt text
    """
    prompt = (f"Based on the following section analyses for the video titled '{video_title}', please create a comprehensive summary that includes key findings "
              "under the headings of Historical Accuracy, Scientific Accuracy, Speculative Claims, and "
              "Religious/Mythological References.\n\n")
    
    for i, result in enumerate(analysis_results, start=1):
        prompt += f"Section {i} Analysis:\n{result}\n\n"
    
    prompt += "Please integrate all key points from the above analyses into a final structured summary."
    return prompt

def generate_comprehensive_summary(analysis_results: List[str], video_title: str, api_key: str) -> str:
    """
    Generate a comprehensive summary from all section analyses.
    
    Args:
        analysis_results: List of section analysis results
        video_title: Title of the video
        api_key: OpenAI API key
        
    Returns:
        HTML-formatted comprehensive summary
    """
    summary_prompt = create_summary_prompt(analysis_results, video_title)
    try:
        # Use the provided API key for this request
        openai.api_key = api_key
        
        summary_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": summary_prompt}
            ],
            temperature=0.5,
            max_tokens=4096,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        content = summary_response.choices[0].message['content']
        
        # Format the content into HTML
        html_content = ""
        sections = ["Summary", "Historical Accuracy", "Scientific Accuracy", "Speculative Claims", "Religious/Mythological References"]
        section_contents = {section: "" for section in sections}
        
        # Initialize variables to keep track of the current section being processed
        current_section = None
        for line in content.split('\n'):
            # Check if the line starts with one of the section headings
            for section in sections:
                if line.startswith(section) or line.startswith("## " + section) or line.startswith("# " + section):
                    current_section = section
                    break
            
            if current_section and not any(line.startswith(section) or line.startswith("## " + section) or line.startswith("# " + section) for section in sections):
                # Append the line to the appropriate section
                section_contents[current_section] += line + '\n'
        
        # Construct the HTML content using section headings and their contents
        for section in sections:
            if section_contents[section].strip():
                html_content += f"<div class='analysis-section'><h2>{section}</h2><div class='section-content'>{section_contents[section]}</div></div>"
        
        return html_content

    except Exception as e:
        logger.error(f"Error generating comprehensive summary: {e}")
        return "<h2>Error</h2><p>Summary generation failed.</p>"

# Async version for future implementation
async def process_video_async(youtube_url: str, api_key: str) -> str:
    """
    Process a YouTube video for analysis asynchronously.
    
    This is a placeholder for future async implementation.
    
    Args:
        youtube_url: YouTube video URL
        api_key: OpenAI API key
        
    Returns:
        HTML-formatted analysis result
    """
    # This is a placeholder for future async implementation
    return process_video(youtube_url, api_key) 
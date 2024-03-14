import re
import time
from youtube_transcript_api import YouTubeTranscriptApi
import openai
import requests
from bs4 import BeautifulSoup


def get_video_id(url):
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

def get_youtube_video_title(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find("meta", property="og:title")
            if title_tag:
                return title_tag["content"]
            else:
                print("Title tag not found.")
                return None
        else:
            print("Failed to fetch the YouTube page.")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])
        return transcript.fetch()
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None
    
def process_video(youtube_url, api_key):
    video_id = get_video_id(youtube_url)
    if video_id is None:
        return "Failed to extract video ID."
    
    video_title = get_youtube_video_title(youtube_url)
    if video_title is None:
        video_title = "Unknown Title"

    transcript_data = get_transcript(video_id)
    if not transcript_data:
        return "Failed to retrieve transcript."

    transcript_parts_with_timestamps = split_transcript_with_timestamps(transcript_data)
    analyses = []
    for part in transcript_parts_with_timestamps:
        section = part['text']
        analysis_result = analyze_and_summarize_section(section, api_key)
        analyses.append(analysis_result)

    if not analyses:
        return "No analyses were generated."

    comprehensive_summary = generate_comprehensive_summary(analyses, video_title)
    return generate_comprehensive_summary(analyses, video_title)




def analyze_and_summarize_section(section, api_key):
    try:
        # Use the provided API key for this request
        openai.api_key = api_key
        
        analysis_prompt = ("Please analyze the following text and provide a structured response with the following headings: "
                           "Historical Accuracy, Scientific Accuracy, Speculative Claims, and Religious/Mythological References.\n\n"
                           "Text: \"" + section + "\"\n\n"
                           "Response:")
        
        analysis_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
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
        print(f"Error in section analysis: {e}")
        return "Analysis failed."



def split_transcript_with_timestamps(transcript_data, max_length=15385):
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

def create_summary_prompt(analysis_results, video_title):
    prompt = (f"Based on the following section analyses for the video titled '{video_title}', please create a comprehensive summary that includes key findings "
              "under the headings of Historical Accuracy, Scientific Accuracy, Speculative Claims, and "
              "Religious/Mythological References.\n\n")
    
    for i, result in enumerate(analysis_results, start=1):
        prompt += f"Section {i} Analysis:\n{result}\n\n"
    
    prompt += "Please integrate all key points from the above analyses into a final structured summary."
    return prompt



def generate_comprehensive_summary(analysis_results, video_title):
    summary_prompt = create_summary_prompt(analysis_results, video_title)
    try:
        summary_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
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
            if any(line.startswith(section) for section in sections):
                current_section = line.split(':')[0]
                continue
            if current_section:
                # Append the line to the appropriate section
                section_contents[current_section] += line + '\n'
        
        # Construct the HTML content using section headings and their contents
        for section in sections:
            html_content += f"<h2>{section}</h2><p>{section_contents[section]}</p>"
        
        return html_content

    except Exception as e:
        print(f"Error generating comprehensive summary: {e}")
        return "Summary generation failed."




if __name__ == "__main__":
    video_id = get_video_id(youtube_video_url)
    if video_id is None:
        print("Failed to extract video ID.")
    else:
        video_title = get_youtube_video_title(youtube_video_url)
        if video_title is None:
            print("Failed to fetch video title.")
            video_title = "Unknown Title"

        transcript_data = get_transcript(video_id)
        if transcript_data:
            transcript_parts_with_timestamps = split_transcript_with_timestamps(transcript_data)
            analyses = []  # Initialize analyses list here
            for part in transcript_parts_with_timestamps:
                text = part['text']
                analysis_result = analyze_and_summarize_section(text)
                analyses.append(analysis_result)

            if analyses:  # Check if analyses list is not empty
                comprehensive_summary = generate_comprehensive_summary(analyses, video_title)
                print(comprehensive_summary)
            else:
                print("No analyses were generated.")

        else:
            print("Failed to retrieve transcript.")

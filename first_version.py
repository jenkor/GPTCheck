import re
from youtube_transcript_api import YouTubeTranscriptApi
import openai

# Input your YouTube video URL here
youtube_video_url = 'https://www.youtube.com/watch?v=0aRBV2O2WEQ'
# Extract video ID from the URL
video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_video_url)
if video_id_match:
    video_id = video_id_match.group(1)
else:
    raise ValueError("Could not extract video ID from the URL.")

# Function to get the transcript
def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])
        return transcript.fetch()
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

# Function to analyze text for historical and scientific accuracy
openai.api_key = ''

def analyze_text(text):
    try:
        # Adjusting the prompt for the Chat API
        system_message = "You are a highly knowledgeable assistant. Given the following transcript, please provide an analysis of its historical and scientific accuracy. Also, assess if there is any political, religious, or any other kind of agenda. Present data in short sentences and also add references so users can check facts and sources."
        user_message = text  # The transcript text to be analyzed
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=4096,  # Adjust based on your needs and the limits of the API
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        # Extracting the response text from the Chat API response
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error in analysis: {e}")
        return None


# Main script execution
if __name__ == "__main__":
    transcript_data = get_transcript(video_id)
    if transcript_data:
        # Joining the entire transcript for analysis
        transcript_text = " ".join([item['text'] for item in transcript_data])
        analysis_result = analyze_text(transcript_text)
        print("Analysis Result:", analysis_result)
    else:
        print("Failed to retrieve transcript.")

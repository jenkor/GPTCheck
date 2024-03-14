from flask import Flask, request, render_template, Markup
from analysis import process_video, get_youtube_video_title

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_video():
    if request.method == 'POST':
        youtube_url = request.form['youtube_url']
        api_key = request.form['api_key']

        # Get the video title
        video_title = get_youtube_video_title(youtube_url)
        
        # Use the process_video function to get the analysis result
        result = process_video(youtube_url, api_key)

        # Debug: Print the result to the console to check the content
        print(result)  # Check the server console for this output

        # Assuming 'result' contains HTML content with headings and paragraphs
        safe_result = Markup(result)
        return render_template('result.html', result=safe_result, video_title=video_title)

if __name__ == '__main__':
    app.run(debug=True)

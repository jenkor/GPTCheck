
# YouTube Video Analyzer

## Description

The YouTube Video Analyzer is a web-based tool that allows users to input a YouTube video URL and an OpenAI API key to perform detailed analysis on the video. This analysis could range from content summarization, sentiment analysis of the comments, to more complex insights. The result is presented in a user-friendly web interface, leveraging the power of OpenAI's advanced AI models.

## Features

- Web interface for easy submission of YouTube videos for analysis.
- Utilizes OpenAI API for sophisticated video analysis.
- Presents analysis results in a clean, readable format.

## Prerequisites

- Python 3.x
- Flask
- An OpenAI API key

## Installation

1. Clone the repository to your local machine.
2. Install the required dependencies by running:
   ```bash
   pip install -r requirements.txt
   ```
   (Ensure you have Python installed on your machine).
3. Set your OpenAI API key in the environment variables or directly in the application, as per security best practices.
4. Run the Flask application using:
   ```bash
   python app.py
   ```

## Usage

1. Navigate to the application URL in your web browser.
2. Enter the YouTube video URL you wish to analyze in the provided field.
3. Enter your OpenAI API key.
4. Submit the form to receive the video analysis results.

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change. Please ensure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

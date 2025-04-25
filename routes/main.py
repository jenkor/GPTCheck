from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, Markup, session
from werkzeug.utils import secure_filename
from services.youtube import get_youtube_video_title, get_video_id
from services.analysis import process_video
from services.tasks import get_or_create_video_analysis_task, get_task_status, run_task_in_thread
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@main_bp.route('/analyze', methods=['POST'])
def analyze_video():
    """Handle video analysis form submission"""
    if request.method == 'POST':
        youtube_url = request.form['youtube_url']
        
        # Get API key from form or use from environment if configured
        api_key = request.form.get('api_key') or current_app.config.get('OPENAI_API_KEY')
        
        if not api_key:
            flash('OpenAI API key is required', 'error')
            return redirect(url_for('main.index'))
        
        try:
            # Get or create task for this analysis
            task_id = get_or_create_video_analysis_task(youtube_url, api_key)
            
            # Get the current task status
            task_status = get_task_status(task_id)
            
            # If the task is not already running or completed, start it
            if task_status['status'] == 'pending':
                # Start the task in a background thread
                run_task_in_thread(task_id, process_video, youtube_url, api_key)
            
            # Store task ID in session for progress tracking
            session['current_task_id'] = task_id
            
            # Redirect to the waiting page
            return redirect(url_for('main.task_status', task_id=task_id))
            
        except Exception as e:
            flash(f'Error analyzing video: {str(e)}', 'error')
            return redirect(url_for('main.index'))
            
    return redirect(url_for('main.index'))

@main_bp.route('/tasks/<task_id>', methods=['GET'])
def task_status(task_id):
    """Show the task status and progress page"""
    try:
        # Get the task status
        task_status = get_task_status(task_id)
        
        if task_status['status'] == 'not_found':
            flash('Task not found', 'error')
            return redirect(url_for('main.index'))
        
        # Get video info
        youtube_url = task_status['params'].get('youtube_url')
        video_id = get_video_id(youtube_url) if youtube_url else None
        video_title = get_youtube_video_title(youtube_url) if youtube_url else "Unknown Video"
        
        # If the task is completed, show the results
        if task_status['status'] == 'completed' and task_status.get('result'):
            # Make HTML content safe
            safe_result = Markup(task_status['result'])
            
            return render_template('result.html', 
                                  result=safe_result, 
                                  video_title=video_title,
                                  video_url=youtube_url)
        
        # If the task is still processing, show the waiting page
        return render_template('processing.html',
                              task_id=task_id,
                              task_status=task_status,
                              video_title=video_title,
                              video_url=youtube_url,
                              progress=task_status.get('progress', 0))
    
    except Exception as e:
        flash(f'Error checking task status: {str(e)}', 'error')
        return redirect(url_for('main.index')) 
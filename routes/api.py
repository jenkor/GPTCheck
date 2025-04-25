from flask import Blueprint, request, jsonify, current_app
from services.youtube import get_youtube_video_title, get_video_id
from services.analysis import process_video
from services.tasks import get_or_create_video_analysis_task, get_task_status, run_task_in_thread
import os
import json
import hashlib

api_bp = Blueprint('api', __name__)

@api_bp.route('/analyze', methods=['POST'])
def analyze_video():
    """API endpoint for video analysis"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    youtube_url = data.get('youtube_url')
    api_key = data.get('api_key') or current_app.config.get('OPENAI_API_KEY')
    
    if not youtube_url:
        return jsonify({'error': 'YouTube URL is required'}), 400
    
    if not api_key:
        return jsonify({'error': 'OpenAI API key is required'}), 400
    
    try:
        # Get or create a task for this video analysis
        task_id = get_or_create_video_analysis_task(youtube_url, api_key)
        
        # Get the current task status
        task_status = get_task_status(task_id)
        
        # If the task is not already running or completed, start it
        if task_status['status'] == 'pending':
            # Start the task in a background thread
            run_task_in_thread(task_id, process_video, youtube_url, api_key)
        
        # Return the task ID and status
        return jsonify({
            'task_id': task_id,
            'status': task_status['status'],
            'progress': task_status.get('progress', 0)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get the status of a specific task"""
    task_status = get_task_status(task_id)
    
    if task_status['status'] == 'not_found':
        return jsonify({'error': 'Task not found'}), 404
    
    # If the task is completed, include the result
    if task_status['status'] == 'completed' and task_status.get('result'):
        return jsonify({
            'task_id': task_id,
            'status': task_status['status'],
            'progress': task_status.get('progress', 100),
            'result': task_status['result'],
            'created_at': task_status.get('created_at'),
            'updated_at': task_status.get('updated_at')
        })
    
    # Otherwise, just return the status information
    return jsonify({
        'task_id': task_id,
        'status': task_status['status'],
        'progress': task_status.get('progress', 0),
        'error': task_status.get('error'),
        'created_at': task_status.get('created_at'),
        'updated_at': task_status.get('updated_at')
    })

@api_bp.route('/status', methods=['GET'])
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'online',
        'version': '1.0.0'
    }) 
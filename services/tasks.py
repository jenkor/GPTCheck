import asyncio
import threading
import logging
import time
import os
import json
from flask import current_app
import hashlib
from typing import Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

# In-memory task storage
tasks = {}

class TaskStatus:
    """Task status constants"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a task.
    
    Args:
        task_id: The ID of the task
        
    Returns:
        Dictionary with task status information
    """
    if task_id in tasks:
        return tasks[task_id]
    return {"status": "not_found", "error": "Task not found"}

def create_task(task_type: str, params: Dict[str, Any]) -> str:
    """
    Create a new task and return its ID.
    
    Args:
        task_type: Type of task (e.g., 'video_analysis')
        params: Parameters for the task
        
    Returns:
        Task ID
    """
    # Generate a unique task ID
    task_id = hashlib.md5(f"{task_type}_{time.time()}_{params}".encode('utf-8')).hexdigest()
    
    # Create task record
    tasks[task_id] = {
        "id": task_id,
        "type": task_type,
        "params": params,
        "status": TaskStatus.PENDING,
        "created_at": time.time(),
        "updated_at": time.time(),
        "progress": 0,
        "result": None,
        "error": None
    }
    
    return task_id

def update_task_status(task_id: str, status: str, progress: int = None, 
                      result: Any = None, error: str = None) -> None:
    """
    Update the status of a task.
    
    Args:
        task_id: The ID of the task
        status: New status (pending, processing, completed, failed)
        progress: Optional progress percentage (0-100)
        result: Optional task result
        error: Optional error message
    """
    if task_id in tasks:
        if progress is not None:
            tasks[task_id]["progress"] = progress
        
        if result is not None:
            tasks[task_id]["result"] = result
            
        if error is not None:
            tasks[task_id]["error"] = error
            
        tasks[task_id]["status"] = status
        tasks[task_id]["updated_at"] = time.time()
        
        logger.info(f"Task {task_id} updated: status={status}, progress={progress}")

def run_task_in_thread(task_id: str, func, *args, **kwargs):
    """
    Run a task in a separate thread.
    
    Args:
        task_id: The ID of the task
        func: The function to run
        *args, **kwargs: Arguments to pass to the function
    """
    def task_wrapper():
        # Update status to processing
        update_task_status(task_id, TaskStatus.PROCESSING, progress=0)
        
        try:
            # Run the task
            result = func(*args, **kwargs)
            
            # Update status to completed
            update_task_status(task_id, TaskStatus.COMPLETED, progress=100, result=result)
            
            # Cache the result if caching is enabled
            if current_app and 'CACHE_DIR' in current_app.config:
                cache_dir = current_app.config['CACHE_DIR']
                os.makedirs(cache_dir, exist_ok=True)
                
                cache_file = os.path.join(cache_dir, f"{task_id}.json")
                with open(cache_file, 'w') as f:
                    json.dump({
                        "task_id": task_id,
                        "result": result,
                        "completed_at": time.time()
                    }, f)
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            update_task_status(task_id, TaskStatus.FAILED, error=str(e))
    
    # Start the thread
    thread = threading.Thread(target=task_wrapper)
    thread.daemon = True
    thread.start()
    
    return task_id

def get_or_create_video_analysis_task(video_url: str, api_key: str) -> str:
    """
    Get an existing task for a video analysis or create a new one.
    
    Args:
        video_url: YouTube video URL
        api_key: OpenAI API key
        
    Returns:
        Task ID
    """
    # Check if there's an existing task for this video
    for task_id, task in tasks.items():
        if (task['type'] == 'video_analysis' and 
            task['params'].get('youtube_url') == video_url and
            task['status'] in [TaskStatus.PENDING, TaskStatus.PROCESSING, TaskStatus.COMPLETED]):
            return task_id
    
    # Create a new task
    return create_task('video_analysis', {
        'youtube_url': video_url,
        'api_key': api_key[:10] + '...'  # Store partial API key for reference
    }) 
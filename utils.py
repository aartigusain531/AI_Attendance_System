"""
AI Attendance System - Python Utilities
Handles common functions for the application
"""

import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash

def admin_required(f):
    """Decorator to check admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in as admin to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def get_current_admin():
    """Get current admin username from session"""
    return session.get("admin_username")

def format_date(date_obj):
    """Format date object to readable string"""
    if not date_obj:
        return "N/A"
    return date_obj.strftime("%B %d, %Y")

def format_time(time_obj):
    """Format time object to readable string"""
    if not time_obj:
        return "N/A"
    return time_obj.strftime("%I:%M %p")

def get_attendance_stats():
    """Calculate attendance statistics"""
    from models.database import Student, Attendance
    from datetime import date
    
    total_students = Student.query.count()
    today_attendance = Attendance.query.filter_by(date=date.today()).count()
    total_attendance = Attendance.query.count()
    
    return {
        "total_students": total_students,
        "today_attendance": today_attendance,
        "total_attendance": total_attendance,
        "percentage": round((today_attendance / total_students * 100) if total_students > 0 else 0, 2)
    }

def save_json_file(filepath, data):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_json_file(filepath):
    """Load data from JSON file"""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def create_response(success, message, data=None, status_code=200):
    """Create standardized JSON response"""
    response = {
        "success": success,
        "message": message
    }
    if data:
        response["data"] = data
    return response, status_code

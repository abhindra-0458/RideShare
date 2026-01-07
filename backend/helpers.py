import random
import string
from datetime import datetime
import re

def generate_id():
    """Generate a random ID similar to JS Math.random().toString(36)"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))

def format_timestamp(date):
    """Format datetime to ISO format string"""
    if isinstance(date, datetime):
        return date.isoformat()
    return datetime.fromisoformat(str(date)).isoformat()

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

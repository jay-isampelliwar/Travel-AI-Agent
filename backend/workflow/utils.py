from datetime import datetime

def get_current_date_time() -> str:
    return datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
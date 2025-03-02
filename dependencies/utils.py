from datetime import datetime


def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None

    # Handle different date formats
    formats = ["%Y-%m-%d", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def format_date(date_obj):
    """Format datetime object to string."""
    if not date_obj:
        return None
    return date_obj.strftime("%Y-%m-%d")

# Standard library imports
from datetime import datetime


def convert_to_dd_mm_yyyy(date_str: str) -> str:
    """
    Convert any date format to dd-mm-yyyy format.
    """
    # List of possible date formats to try
    date_formats = [
        '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y',  # DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
        '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',  # YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
        '%m-%d-%Y', '%m/%d/%Y', '%m.%d.%Y',  # MM-DD-YYYY, MM/DD/YYYY, MM.DD.YYYY
        '%d-%m-%y', '%d/%m/%y', '%d.%m.%y',  # DD-MM-YY, DD/MM/YY, DD.MM.YY
        '%y-%m-%d', '%y/%m/%d', '%y.%m.%d',  # YY-MM-DD, YY/MM/DD, YY.MM.DD
        '%m-%d-%y', '%m/%d/%y', '%m.%d.%y',  # MM-DD-YY, MM/DD/YY, MM.DD.YY
    ]

    for fmt in date_formats:
        try:
            # Try to parse the date string using the current format
            date_obj = datetime.strptime(date_str, fmt)
            # If successful, format it to dd-mm-yyyy
            return date_obj.strftime('%d-%m-%Y')
        except ValueError:
            continue

    # If no format matches, raise an error
    raise ValueError(
        f"Unable to parse the date: {date_str}. Supported formats include DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD, etc.")

from datetime import datetime, timedelta
from dateutil import parser
import pytz
from typedargs.exceptions import ArgumentError

def convert_str_to_dt(str_dt):
    """Convert string to UTC datetime"""
    dt = parser.parse(str_dt)
    return dt

def convert_or_force_utc(dt):
    """Convert timezone to UTC or force UTC to incoming datetime

    Args:
        dt (datetime): A tz-aware or tz-naive datetime

    Returns:
        dt_utc (datetime): UTC datetime
    """
    if dt.tzinfo:
        dt_utc = dt.astimezone(pytz.timezone('UTC'))
    else:
        dt_utc = pytz.timezone('UTC').localize(dt)

    return dt_utc

def formatted_ts(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

def get_utc_ts(str_or_dt):
    """Get UTC timestamp in ISO format.

    Args:
        str_or_dt (str or datetime): A string representing a valid datetime or
            datetime-compatible string

    Returns:
        ts (str): UTC timestamp in ISO format
    """
    if str_or_dt is None:
        return None

    if not isinstance(str_or_dt, (str, datetime)):
        raise ArgumentError("""Incoming argument is not a valid string or a datetime""",
                            str_or_dt=str_or_dt, type=type(str_or_dt))

    if isinstance(str_or_dt, datetime):
        ts = convert_or_force_utc(str_or_dt)
        return formatted_ts(ts)

    if isinstance(str_or_dt, str):
        ts = convert_str_to_dt(str_or_dt)
        ts = convert_or_force_utc(ts)
        return formatted_ts(ts)

    return None

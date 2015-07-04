"""Utility functionality."""

from __future__ import division, print_function
import os

import datetime
import time

def now():
    """Get current time as seconds."""
    return int(time.time())

def time_fmt(secs):
    """Format time represented as seconds."""
    #fmt = '%Y-%m-%d %H:%M %Z'
    fmt = '%a, %d %b %Y %H:%M %Z'
    return time.strftime(fmt, time.localtime(secs))

def file_age(filename):
    """Return file age as a timedelta, with second precision."""
    seconds = int(time.time() - os.path.getmtime(filename))
    age = datetime.timedelta(seconds=seconds)
    return age

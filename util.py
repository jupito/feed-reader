"""Utility functionality."""

from __future__ import division, print_function
from HTMLParser import HTMLParser
import datetime
import os
import time

class HTMLStripper(HTMLParser):
    """HTML markup stripper."""
    def __init__(self):
        HTMLParser.__init__(self)
        self.fed = []

    def handle_data(self, data):
        self.fed.append(data)

    def get_data(self):
        return ''.join(self.fed)

    @classmethod
    def strip(cls, text):
        """Strip markup from text, returning only the plaintext."""
        parser = cls()
        parser.feed(text)
        return parser.get_data()

def now():
    """Get current time as seconds."""
    return int(time.time())

def time_fmt(secs=None, local=False, fmt='rfc2822'):
    """Format time represented as seconds since the epoch."""
    formats = dict(
            iso8601='%Y-%m-%dT%H:%M %z',
            rfc2822='%a, %d %b %Y %H:%M %z',
            locale='%c',
            )
    if fmt in formats:
        fmt = formats[fmt]
    if secs is None:
        secs = time.time()
    if local:
        t = time.localtime(secs)
    else:
        t = time.gmtime(secs)
    s = time.strftime(fmt, t)
    return s

def file_age(filename):
    """Return file age as a timedelta, with second precision."""
    seconds = int(time.time() - os.path.getmtime(filename))
    age = datetime.timedelta(seconds=seconds)
    return age

def first_line(s):
    """Return the first line with characters from a string, stripped."""
    lines = s.lstrip().splitlines() or ['']
    line = lines[0].rstrip()
    return line

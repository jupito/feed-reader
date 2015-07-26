"""General utility functionality."""

from __future__ import absolute_import, division, print_function
from HTMLParser import HTMLParser
from functools import partial
from itertools import islice
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
        """Return processed text."""
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
    return time.strftime(fmt, t)


def file_age(filename):
    """Return file age as a timedelta, with second precision."""
    seconds = int(time.time() - os.path.getmtime(filename))
    return datetime.timedelta(seconds=seconds)


def first_line(s):
    """Return the first line with characters from a string, stripped."""
    lines = s.lstrip().splitlines() or ['']
    return lines[0].rstrip()


def take(n, iterable):
    """Return first n items of the iterable as a list."""
    return list(islice(iterable, n))


def sole(it):
    """Make sure that iterable has only one element, and return it."""
    lst = take(2, it)
    n = len(lst)
    if n != 1:
        msg = 'Element count not exactly one, observed {}.'
        raise ValueError(msg.format(n))
    return lst[0]


def tokens(s, factory=None, filt=None, sep=',', strip=True):
    """Simple string tokenizer primarily meant for CGI parameters."""
    tokens = s.split(sep)
    if strip:
        tokens = [x.strip() for x in tokens]
    if filt:
        tokens = filter(filt, tokens)
    if factory:
        tokens = [factory(x) for x in tokens]
    return tokens


int_tokens = partial(tokens, factory=int, filt=lambda x: x.isdigit())

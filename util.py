"""General utility functionality."""

from __future__ import absolute_import, division, print_function
import codecs
from collections import OrderedDict
import datetime
from functools import partial
from HTMLParser import HTMLParser
from itertools import islice
import os
import sys
import time


class CGIArgs(object):
    """CGI URL argument handling."""
    def __init__(self, scriptname):
        self.scriptname = scriptname
        self.args = OrderedDict()

    def add_arg(self, name, decoder=str, encoder=str, default=None):
        """Add an argument definition."""
        self.args[name] = dict(decoder=decoder, encoder=encoder,
                               default=default, value=default)

    def parse(self, cgi):
        """Parse arguments from the form."""
        form = cgi.FieldStorage()
        for name, arg in self.args.iteritems():
            value = form.getfirst(name)
            if value is None:
                value = arg['default']
            else:
                try:
                    value = arg['decoder'](value)
                except ValueError:
                    value = arg['default']
            arg['value'] = value

    def __getitem__(self, name):
        """Get argument value."""
        return self.args[name]['value']

    def link(self, **kwargs):
        """Create a URL with GET arguments."""
        strings = []
        for name, arg in self.args.iteritems():
            value = arg['value']
            if name in kwargs:
                value = kwargs[name]
            if value is not None and value != arg['default']:
                value = arg['encoder'](value)
                strings.append('{}={}'.format(name, value))
        url = '{}?{}'.format(self.scriptname, '&'.join(strings))
        return url


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


def tokenize(s, factory=None, filt=None, sep=',', strip=True):
    """Simple string tokenizer primarily meant for CGI parameters."""
    tokens = s.split(sep)
    if strip:
        tokens = [x.strip() for x in tokens]
    if filt:
        # tokens = filter(filt, tokens)
        tokens = [x for x in tokens if filt(x)]
    if factory:
        tokens = [factory(x) for x in tokens]
    return tokens


int_tokens = partial(tokenize, factory=int, filt=lambda x: x.isdigit())


def token_str(tokens, sep=','):
    """Tokens as string."""
    return sep.join(str(x) for x in tokens)


def install_utf8_conversion():
    """Install UTF-8 conversion wrapper for output."""
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'strict')
    if sys.stderr.encoding != 'UTF-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr, 'strict')

from __future__ import division, print_function
import time

import feedparser

import util

def parse_url(url):
    """Parse a feed and its entries."""
    d = feedparser.parse(url)
    feed = parse_feed(url, d.feed)
    entries = [parse_entry(e) for e in d.entries]
    if entries:
        # Set feed publish time as newest entry publish time.
        feed['updated'] = max(e['updated'] for e in entries)
        return feed, entries
    else:
        raise Exception('No entries in feed: {}'.format(url), feed)

def parse_feed(url, f):
    return {
        'url': url,
        'refreshed': util.now(),
        'updated': get_updated(f),
        'title': getattr(f, 'title', '(no title)'),
        'link': get_link(f),
        'description': get_description(f),
        }

def parse_entry(e):
    enc_url, enc_length, enc_type = get_enc(e)
    return {
        'guid': e['guid'],
        'refreshed': util.now(),
        'updated': get_updated(e),
        'title': getattr(e, 'title', '(no title)'),
        'link': get_link(e),
        'description': get_description(e),
        'enc_url': enc_url,
        'enc_length': enc_length,
        'enc_type': enc_type,
        }

def get_updated(x):
    """Get updated field or current time as seconds."""
    if 'published_parsed' in x:
        return int(time.mktime(x['published_parsed']))
    else:
        return 0

def get_description(x):
    return elem_or(x, 'description')

def get_link(x):
    return elem_or(x, 'link')

def get_enc(x):
    if 'enclosures' in x and len(x.enclosures) > 0:
        enc = x.enclosures[0]
        return elem_or(enc, 'url'), elem_or(enc, 'length'), elem_or(enc, 'type')
    else:
        return None, None, None

def elem_or(x, elem, default=None):
    return getattr(x, elem) if elem in x else default

def field_fmt(k, v):
    """Return object field name and value formatted."""
    if k == 'refreshed' or k == 'updated':
        return k, util.time_fmt(v)
    elif k == 'description':
        return k, util.first_line(v or '')
    else:
        return k, v

def describe(x, verbosity):
    """Describe a feed or an entry."""
    if verbosity:
        max_keylen = max(len(k) for k in x.keys())
        pairs = [field_fmt(k, x[k]) for k in x.keys()]
        s = u'{k:%i}: {v}' % max_keylen
        lines = [s.format(k=k, v=v) for k, v in pairs]
        return '\n'.join(lines) + '\n'
    else:
        return u'{id}: {title}'.format(**x)

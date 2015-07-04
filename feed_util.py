from __future__ import division, print_function
import time
import feedparser

import util

def parse_url(url):
    """Parse a feed and its entries."""
    d = feedparser.parse(url)
    feed = parse_feed(url, d.feed)
    entries = [parse_entry(e) for e in d.entries]
    # Set feed publish time as newest entry publish time.
    feed['updated'] = max(e['updated'] for e in entries)
    return feed, entries

def parse_feed(url, f):
    return {
        'url': url,
        'refreshed': util.now(),
        'updated': get_updated(f),
        'title': get_title(f),
        'link': get_link(f),
        'description': get_description(f),
        }

def parse_entry(e):
    enc_url, enc_length, enc_type = get_enc(e)
    return {
        'guid': get_guid(e),
        'refreshed': util.now(),
        'updated': get_updated(e),
        'title': get_title(e),
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

def get_title(x):
    return elem_or(x, 'title', get_updated(x))

def get_guid(x):
    return elem_or(x, 'guid', get_title(x))

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
        return k, '\n' + (v or '')
    else:
        return k, v

def describe(x, verbosity):
    """Describe a feed or an entry."""
    if verbosity:
        lines = ['%s:\t%s' % field_fmt(k, x[k]) for k in x.keys()]
        return '\n'.join(lines) + '\n'
    else:
        return u'{id}: {title}'.format(**x)

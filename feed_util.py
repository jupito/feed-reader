from __future__ import division, print_function
import logging
import pprint
import time

import feedparser

import util

def parse_url(url):
    """Parse a feed and its entries."""
    d = feedparser.parse(url)
    if d.status > 299:
        logging.error('Cannot read feed: {d.status}: {u}'.format(d=d, u=url))
        logging.debug(pprint.pformat(d))
        raise IOError(d.status)
    feed = parse_feed(url, d.feed)
    entries = [parse_entry(e) for e in d.entries]
    if entries:
        # Set feed publish time as newest entry publish time.
        feed['updated'] = max(e['updated'] for e in entries)
    else:
        logging.error('Feed with no entries: {}'.format(url))
        logging.debug(pprint.pformat(d))
    return feed, entries

def parse_feed(url, x):
    logging.debug('Parsing feed {}'.format(url))
    d = dict(
        url=url,
        refreshed=util.now(),
        updated=get_updated(x),
        title=getattr(x, 'title', '(no title)'),
        link=getattr(x, 'link', '(no link)'),
        description=getattr(x, 'description', '(no description)'),
        )
    return d

def parse_entry(x):
    if 'id' not in x:
        logging.debug('Entry without GUID, using link: {link}'.format(**x))
    enc_url, enc_length, enc_type = get_enc(x)
    d = dict(
        guid=getattr(x, 'id', x['link']),
        refreshed=util.now(),
        updated=get_updated(x),
        title=getattr(x, 'title', '(no title)'),
        link=getattr(x, 'link', '(no link)'),
        description=getattr(x, 'description', '(no description)'),
        enc_url=enc_url,
        enc_length=enc_length,
        enc_type=enc_type,
        )
    return d

def get_updated(x):
    """Get updated field or current time as seconds."""
    st = getattr(x, 'published_parsed', time.gmtime(0))
    seconds = int(time.mktime(st))
    return seconds

def get_enc(x):
    """Return the first enclosure."""
    names = 'url', 'length', 'type'
    if 'enclosures' in x and x.enclosures:
        enc = x.enclosures[0]
        return tuple(getattr(enc, s, None) for s in names)
    else:
        return tuple(None for _ in names)

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

"""Parsing feeds and handling them as objects."""

from __future__ import absolute_import, division, print_function
import time

import feedparser

import util


def parse_url(url, etag, modified, debug=None):
    """Parse a feed and its entries."""
    d = feedparser.parse(url, etag=etag, modified=modified)
    status = d.get('status', -1)
    if status == -1:
        if 'bozo_exception' in d:
            raise d['bozo_exception']
        raise IOError(-1, 'Bozo content', url)
    elif status > 299:
        raise IOError(status, 'Link error', url)
    elif status == 304:
        return False, False  # No need to download. Don't change anything.
    href = d.get('href', None)
    if debug and href is not None and href != url:
        debug('Redirection from {} to {}'.format(url, href))

    feed = parse_feed(url, d.feed)
    entries = [parse_entry(e, debug) for e in d.entries]
    if entries:
        # Set feed publish time as newest entry publish time.
        feed['updated'] = max(e['updated'] for e in entries)
    if debug and not entries:
        debug('Feed with no entries: {}'.format(url))
    return feed, entries


def parse_feed(url, x):
    d = dict(
        url=url,
        etag=x.get('etag'),
        modified=x.get('modified'),
        refreshed=util.now(),  # TODO: Use x.headers.date instead (TZ?).
        updated=get_updated(x),
        title=x.get('title', '(no title)'),
        link=x.get('link', '(no link)'),
        description=x.get('description', '(no description)'),
        )
    return d


def parse_entry(x, debug=None):
    if debug and 'id' not in x:
        debug('Entry without GUID, using link: {link}'.format(**x))
    enc_url, enc_length, enc_type = get_enc(x)
    d = dict(
        guid=x.get('id', x.link),
        refreshed=util.now(),  # TODO: Remove, use one from feed instead.
        updated=get_updated(x),
        title=x.get('title', '(no title)'),
        link=x.get('link', '(no link)'),
        description=x.get('description', '(no description)'),
        enc_url=enc_url,
        enc_length=enc_length,
        enc_type=enc_type,
        )
    return d


def get_updated(x):
    """Get updated field or current time as seconds."""
    # TODO: Feeds have 'updated_parsed', is it the same?
    st = x.get('published_parsed', time.gmtime(0))
    seconds = int(time.mktime(st))
    return seconds


def get_enc(x):
    """Return the first enclosure."""
    names = 'url', 'length', 'type'
    enclosures = x.get('enclosures', None)
    if enclosures:
        return tuple(enclosures[0].get(s, None) for s in names)
    else:
        return tuple(None for _ in names)


def field_fmt(k, v):
    """Return object field name and value formatted."""
    if k == 'refreshed' or k == 'updated':
        v = util.time_fmt(v)
    elif k == 'description':
        v = util.HTMLStripper.strip(util.first_line(v or str(v)))[:66]
    return k, unicode(v)


def describe(x, verbosity):
    """Describe a feed or an entry."""
    if verbosity:
        max_keylen = max(len(k) for k in x.keys())
        pairs = [field_fmt(k, x[k]) for k in x.keys()]
        s = u'{k:{l}}: {v}'
        lines = [s.format(k=k, v=v, l=max_keylen) for k, v in pairs]
        return '\n'.join(lines) + '\n'
    else:
        return u'{id}: {title}'.format(**x)

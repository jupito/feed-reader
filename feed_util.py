from __future__ import division, print_function
import time
import feedparser

def get_now():
    "Get current time as seconds."
    return int(time.time())

def parse_url(url):
    "Parse a feed and its entries."
    d = feedparser.parse(url)
    feed = parse_feed(url, d.feed)
    entries = [parse_entry(e) for e in d.entries]
    return feed, entries

def parse_feed(url, f):
    return {
        'url': url,
        'refreshed': get_now(),
        'updated': get_updated(f),
        'title': get_title(f),
        'link': get_link(f),
        'description': get_description(f),
        }

def parse_entry(e):
    enc_url, enc_length, enc_type = get_enc(e)
    return {
        'guid': get_guid(e),
        'refreshed': get_now(),
        'updated': get_updated(e),
        'title': get_title(e),
        'link': get_link(e),
        'description': get_description(e),
        'enc_url': enc_url,
        'enc_length': enc_length,
        'enc_type': enc_type,
        }

def get_updated(x):
    "Get updated field or current time as seconds."
    return time.mktime(x.updated_parsed) if 'updated' in x else get_now()

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
        return (elem_or(enc, 'url'),
                elem_or(enc, 'length'),
                elem_or(enc, 'type'))
    else:
        return (None, None, None)

def elem_or(x, elem, default = None):
    return getattr(x, elem) if elem in x else default

def time_fmt(secs):
    "Format time represented as seconds."
    TIME_FMT = '%Y-%m-%d %H:%M'
    return time.strftime(TIME_FMT, time.gmtime(secs))

def field_fmt(x, k):
    "Return object field name and value formatted."
    if k == 'refreshed' or k == 'updated':
        return k, time_fmt(x[k])
    elif k == 'description':
        return k, '\n' + (x[k] or '')
    else:
        return k, x[k]

def describe_short(x):
    return "%i: %s" % (x['id'], x['title'])

def describe_long(x):
    return '\n'.join(["%s:\t%s" % field_fmt(x, k) for k in x.keys()]) + '\n'

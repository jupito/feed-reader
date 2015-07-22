#!/usr/bin/env python2

"""Manage feeds."""

from __future__ import division, print_function
import argparse
import codecs
import csv
import logging
import sys

import feed_db
import feed_util

LOGLEVELS = 'DEBUG INFO WARNING ERROR CRITICAL'.split()

def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', metavar='DB_FILE',
                   help='Database file name')
    p.add_argument('--add', nargs='+', metavar='STRING',
                   help='add feeds from strings (category,priority,url)')
    p.add_argument('--addcsv', nargs='+', metavar='CSV_FILE',
                   help='add feeds from CSV file (category,priority,url)')
    p.add_argument('--remove', nargs='+', metavar='FEED_ID', type=int,
                   help='remove feeds')
    p.add_argument('--category',
                   help='category')
    p.add_argument('--priority', type=int, default=0,
                   help='priority')
    p.add_argument('--refresh', action='store_true',
                   help='refresh feeds')
    p.add_argument('--feeds', '-f', nargs='*', metavar='FEED_ID', type=int,
                   help='list feeds')
    p.add_argument('--entries', '-e', nargs='*', metavar='ENTRY_ID', type=int,
                   help='list entries')
    p.add_argument('--categories', action='store_true',
                   help='list categories')
    p.add_argument('--get', action='store_true',
                   help='show next unread')
    p.add_argument('--verbose', '-v', action='count',
                   help='be more verbose')
    p.add_argument('--log', metavar='LOGLEVEL', default='WARNING',
                   help='set loglevel ({})'.format(', '.join(LOGLEVELS)))
    p.add_argument('--logfile',
                   help='set logfile')
    return p.parse_args()

def print_feeds(db, ids, v):
    """Print feeds."""
    if ids:
        xs = (db.get_feed(i) for i in ids)
    else:
        xs = db.get_feeds()
    for x in xs:
        print(feed_util.describe(x, v))

def print_entries(db, ids, v):
    """Print entries."""
    if ids:
        xs = (db.get_entry(i) for i in ids)
    else:
        xs = db.get_entries()
    for x in xs:
        print(feed_util.describe(x, v))

def add_feed(db, params, v):
    """Add feed tuple."""
    category, priority, url = params
    if v:
        print('Adding {}'.format(params))
    db.add_feed(url, category, int(priority))

def remove_feed(db, i, v):
    """Remove feed."""
    if v:
        feed = db.get_feed(i)
        print('Removing {title} ({url})'.format(**feed))
    db.remove_feed(i)

def main():
    # Install UTF-8 conversion wrapper for output.
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'strict')
    if sys.stderr.encoding != 'UTF-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr, 'strict')

    args = parse_args()
    d = dict(
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M',
        filename=args.logfile,
        level=getattr(logging, args.log.upper(), None),
        )
    if d['level'] is None:
        raise ValueError('Invalid log level: {}'.format(args.log))
    logging.basicConfig(**d)
    logging.captureWarnings(True)

    db = feed_db.FeedDb(args.file)

    # Add and remove.
    for s in args.add or []:
        params = [x.strip().strip('"') for x in s.split(',')]
        add_feed(db, params, args.verbose)
    for f in args.addcsv or []:
        with open(f, 'rb') as csvfile:
            for row in csv.reader(csvfile):
                add_feed(db, row, args.verbose)
    for i in args.remove or []:
        remove_feed(db, i, args.verbose)

    # Refresh.
    if args.refresh:
        if args.verbose:
            print('Refreshing...')
        db.refresh_all(feed_util.parse_url)
        if args.verbose:
            print('Done.')

    # List things.
    if args.feeds is not None:
        print_feeds(db, args.feeds, args.verbose)
    if args.entries is not None:
        print_entries(db, args.entries, args.verbose)
    if args.categories:
        for cat in db.get_categories():
            print(cat, str(db.n_entries(maxprg=0, cat=cat)))

    # Print entry.
    if args.get:
        print(feed_util.describe(db.get_next(maxprg=0, cat=args.category,
                                             limit=1, priority=1)[0], 1))

    # Print general info.
    if args.verbose:
        print('Total {nf} feeds, {ne} entries, {nu} unread.'.format(
            nf=db.n_feeds(), ne=db.n_entries(maxprg=1),
            nu=db.n_entries(maxprg=0)))

    db.close()

if __name__ == '__main__':
    main()

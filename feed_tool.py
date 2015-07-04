#!/usr/bin/env python2

"""Manage feeds."""

from __future__ import division, print_function
import argparse
import csv

import feed_db
import feed_util

ENC = 'utf-8'

def db_info(db):
    return 'Total %i feeds, %i entries (%i unread).' % (
            db.n_feeds(), db.n_entries(1), db.n_entries(0))

def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file',
            help='Database file name')
    p.add_argument('--add', nargs='+', metavar='string',
            help='add feeds from strings (category,priority,url)')
    p.add_argument('--addcsv', nargs='+', metavar='file',
            help='add feeds from CSV file (category,priority,url)')
    p.add_argument('--remove', nargs='+', metavar='id', type=int,
            help='remove feeds')
    p.add_argument('--category', metavar='category',
            help='category')
    p.add_argument('--priority', metavar='priority', type=int, default=0,
            help='priority')
    p.add_argument('--refresh', action='store_true',
            help='refresh feeds')
    p.add_argument('--feeds', '-f', nargs='*', metavar='id', type=int,
            help='list feeds')
    p.add_argument('--entries', '-e', nargs='*', metavar='id', type=int,
            help='list entries')
    p.add_argument('--categories', action='store_true',
            help='list categories')
    p.add_argument('--get', action='store_true',
            help='show next unread')
    p.add_argument('--pop', action='store_true',
            help='show next unread and mark it read')
    p.add_argument('--verbose', '-v', action='count',
            help='be more verbose')
    args = p.parse_args()
    return args

def print_feeds(db, ids, v):
    describe = feed_util.describe_long if v > 0 else feed_util.describe_short
    xs = map(db.get_feed, ids) if ids else db.get_feeds()
    for x in xs:
        print(describe(x).encode(ENC))

def print_entries(db, ids, v):
    describe = feed_util.describe_long if v > 0 else feed_util.describe_short
    xs = map(db.get_entry, ids) if ids else db.get_entries()
    for x in xs:
        print(describe(x).encode(ENC))

def add_feed(db, params, v):
    """Add feed tuple."""
    category, priority, url = params
    if v:
        print('Adding %s' % url)
    db.add_feed(url, category, int(priority))

def remove_feed(db, i, v):
    if v:
        feed = db.get_feed(i)
        print('Removing %s (%s)' % (feed['title'], feed['url']))
    db.remove_feed(i)


args = parse_args()
db = feed_db.FeedDb(args.file)

for s in args.add or []:
    params = map(lambda x: x.strip().strip('"'), s.split(','))
    add_feed(db, params, args.verbose)
for f in args.addcsv or []:
    with open(f, 'rb') as csvfile:
        for row in csv.reader(csvfile):
            add_feed(db, row, args.verbose)
for i in args.remove or []:
    remove_feed(db, i, args.verbose)

if args.refresh:
    if args.verbose: print('Refreshing...')
    db.refresh_all(feed_util.parse_url)
    if args.verbose: print('Done.')

if args.feeds is not None:
    print_feeds(db, args.feeds, args.verbose)
if args.entries is not None:
    print_entries(db, args.entries, args.verbose)

if args.categories:
    for x in db.get_categories():
        print(x.encode(ENC) + str(db.n_entries(0, x)))

if args.get:
    print(feed_util.describe_long(db.get_next(0, args.category)[0]).encode(ENC))
if args.pop:
    print(feed_util.describe_long(db.pop()).encode(ENC))

if args.verbose:
    print(db_info(db))

db.close()

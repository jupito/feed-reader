#!/usr/bin/env python2

"""Manage podcasts."""

from __future__ import division, print_function
import argparse

import feed_db

DB_FILENAME = '_podcast.db'

def db_info(db):
    d = dict(nf=db.n_feeds(), ne=db.n_entries(), nu=db.n_unread_entries())
    return 'Total {nf} feeds, {ne} entries ({nu} unread).'.format(**d)

def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dl', nargs='+', metavar='n',
            help='download unlistened files')
    p.add_argument('--purge', action='store_true',
            help='purge listened files')
    p.add_argument('--get', action='store_true',
            help='show next unread')
    p.add_argument('--pop', action='store_true',
            help='show next unread and mark it read')
    args = p.parse_args()
    return args


args = parse_args()
db = feed_db.FeedDb(DB_FILENAME)

print(db_info(db))
db.close()

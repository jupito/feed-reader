#!/usr/bin/env python2.7
# -*- coding: iso-8859-15 -*-

from __future__ import division, print_function
import sys
import argparse

import feed_db
import feed_util

DB_FILENAME = '_podcast.db'

def print_db_info(db):
    print("Total %i feeds, %i entries (%i unread)." % (
            db.n_feeds(), db.n_entries(), db.n_unread_entries()))

def parse_args():
    p = argparse.ArgumentParser(description = 'Manage podcasts.')
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

print_db_info(db)
db.close()

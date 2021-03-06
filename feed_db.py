"""Database API."""

from __future__ import absolute_import, division, print_function
import sqlite3

import util

CREATE_DB = """
    CREATE TABLE IF NOT EXISTS Feeds(
        id INTEGER PRIMARY KEY,
        url TEXT UNIQUE NOT NULL,
        etag TEXT,
        modified TEXT,
        refreshed INTEGER,
        updated INTEGER,
        title TEXT,
        description TEXT,
        link TEXT,
        category TEXT NOT NULL DEFAULT 'misc',
        priority INTEGER NOT NULL DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1,
        CHECK(is_active = 0 OR is_active = 1)
    );
    CREATE TABLE IF NOT EXISTS Entries(
        id INTEGER PRIMARY KEY,
        guid TEXT UNIQUE NOT NULL,
        refreshed INTEGER,
        updated INTEGER,
        title TEXT,
        description TEXT,
        link TEXT,
        enc_url TEXT,
        enc_length INTEGER,
        enc_type TEXT,
        progress REAL DEFAULT 0,
        is_important INTEGER DEFAULT 0,
        feed_id INTEGER NOT NULL,
        CHECK(is_important = 0 OR is_important = 1),
        CHECK(progress BETWEEN 0 AND 1),
        FOREIGN KEY(feed_id) REFERENCES Feeds(id)
    );
    """
DELETE_DB = """
    DROP TABLE IF EXISTS Entries;
    DROP TABLE IF EXISTS Feeds;
    """
ALTER_DB = """
    ALTER TABLE Feeds ADD COLUMN etag TEXT;
    ALTER TABLE Feeds ADD COLUMN modified TEXT;
    """


class FeedDb(object):
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename, timeout=5)
        self.conn.execute('PRAGMA foreign_keys=ON')
        # self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.row_factory = sqlite3.Row
        self.create_db()
        self.cur = self.conn.cursor()

    def close(self):
        self.conn.commit()
        total_changes = self.conn.total_changes
        self.conn.close()
        return total_changes

    def create_db(self):
        self.conn.executescript(CREATE_DB)
        # self.conn.executescript(ALTER_DB)

    def delete_db(self):
        self.conn.executescript(DELETE_DB)

    def insert_feed(self, url, category, priority):
        """Insert feed url."""
        d = dict(url=url, cat=category, pri=priority)
        self.cur.execute("""
            INSERT OR IGNORE
            INTO Feeds(url, category, priority) VALUES(:url, :cat, :pri)
            """, d)
        # Now update properties in case the url was already there.
        self.cur.execute("""
            UPDATE Feeds
            SET category=:cat, priority=:pri
            WHERE url=:url
            """, d)

    def insert_entry(self, guid, feed_id):
        """Insert entry guid."""
        d = dict(guid=guid, feed_id=feed_id)
        self.cur.execute("""
            INSERT OR IGNORE
            INTO Entries(guid, feed_id) VALUES(:guid, :feed_id)
            """, d)

    def update_feed(self, feed):
        """Update feed."""
        self.cur.execute("""
            UPDATE Feeds
            SET etag=:etag, modified=:modified,
                refreshed=:refreshed, updated=:updated,
                title=:title, description=:description, link=:link
            WHERE url=:url
            """, feed)

    def update_entry(self, entry):
        """Update entry."""
        self.cur.execute("""
            UPDATE Entries
            SET refreshed=:refreshed, updated=:updated,
                title=:title, description=:description, link=:link,
            enc_url=:enc_url, enc_length=:enc_length, enc_type=:enc_type
            WHERE guid=:guid
            """, entry)

    def refresh_feed(self, feed_id, feed, entries):
        """Refresh given feed."""
        self.update_feed(feed)
        for entry in entries:
            self.insert_entry(entry['guid'], feed_id)
            self.update_entry(entry)

    def n_feeds(self, cat=None):
        """Return the number of feeds in the database."""
        d = dict(notcat=not cat, cat=cat or '%')
        self.cur.execute("""
            SELECT COUNT(*) FROM Feeds
            WHERE (:notcat OR Feeds.category LIKE :cat)
            """, d)
        return util.sole(self.cur.fetchone())

    def n_entries(self, minprg=0, maxprg=0, cat=None, feed=None):
        """Return the number of entries in the database."""
        d = dict(minprg=minprg, maxprg=maxprg,
                 notcat=not cat, cat=cat or '%',
                 notfeed=not feed, feed=feed)
        self.cur.execute("""
            SELECT COUNT(*)
            FROM Entries INNER JOIN Feeds
            ON Entries.feed_id = Feeds.id
            WHERE (progress BETWEEN :minprg AND :maxprg)
                AND (:notcat OR Feeds.category LIKE :cat)
                AND (:notfeed OR feed_id = :feed)
            """, d)
        return util.sole(self.cur.fetchone())

    def get_feed(self, feed_id):
        """Get given feed."""
        d = dict(i=feed_id)
        self.cur.execute('SELECT * FROM Feeds WHERE id=:i', d)
        return self.cur.fetchone()

    def get_feeds(self, cat=None):
        """Get feeds."""
        d = dict(notcat=not cat, cat=cat or '%')
        self.cur.execute("""
            SELECT *
            FROM Feeds
            WHERE (:notcat OR Feeds.category LIKE :cat)
            ORDER BY id
            """, d)
        return self.cur.fetchall()

    def get_entry(self, entry_id):
        """Get given entry."""
        d = dict(i=entry_id)
        self.cur.execute('SELECT * FROM Entries WHERE id=:i', d)
        return self.cur.fetchone()

    def get_entries(self):
        """Get all entries."""
        self.cur.execute('SELECT * FROM Entries ORDER BY id')
        return self.cur.fetchall()

    def get_categories(self):
        self.cur.execute('SELECT DISTINCT category FROM Feeds')
        rows = self.cur.fetchall()
        return sorted(util.sole(r) for r in rows)

    def add_feed(self, url, category, priority):
        """Add feed."""
        self.insert_feed(url, category, priority)

    def remove_feed(self, feed_id):
        """Remove given feed and all its entries."""
        d = dict(i=feed_id)
        self.cur.execute('DELETE FROM Entries WHERE feed_id=:i', d)
        self.cur.execute('DELETE FROM Feeds WHERE id=:i', d)

    def get_next(self, minprg=0, maxprg=0, cat=None, feed=None, limit=1,
                 priority=True):
        """Get next entry or entries."""
        if priority:
            order = 'priority, updated'
        else:
            order = 'updated'
        if limit == 0:
            limit = -1
        d = dict(minprg=minprg, maxprg=maxprg,
                 notcat=not cat, cat=cat or '%',
                 notfeed=not feed, feed=feed,
                 limit=limit)
        query = """
            SELECT Entries.*
            FROM Entries INNER JOIN Feeds
            ON Entries.feed_id = Feeds.id
            WHERE (progress BETWEEN :minprg AND :maxprg)
                AND (:notcat OR Feeds.category LIKE :cat)
                AND (:notfeed OR feed_id = :feed)
            ORDER BY {order}
            LIMIT :limit
            """.format(order=order)
        self.cur.execute(query, d)
        return self.cur.fetchall()

    def set_progress(self, entry_id, progress):
        """Set progress of given entry."""
        d = dict(p=progress, i=entry_id)
        self.cur.execute('UPDATE Entries SET progress=:p WHERE id=:i', d)

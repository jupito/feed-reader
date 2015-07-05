from __future__ import division, print_function
import sqlite3
import logging

logger = logging.getLogger(__name__)

CREATE_DB = """
        CREATE TABLE IF NOT EXISTS Feeds(
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
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

class FeedDb(object):
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename, timeout=5)
        self.conn.execute('PRAGMA foreign_keys=ON')
        #self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.row_factory = sqlite3.Row
        self.create_db()
        self.cur = self.conn.cursor()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def create_db(self):
        self.conn.executescript(CREATE_DB)

    def delete_db(self):
        self.conn.executescript(DELETE_DB)

    def insert_feed(self, url, category, priority):
        """Insert feed url."""
        self.cur.execute("""
                INSERT OR IGNORE
                INTO Feeds(url, category, priority) VALUES(?, ?, ?)
                """, (url, category, priority))
        # Now update properties in case the url was already there.
        self.cur.execute("""
                UPDATE Feeds
                SET category=?, priority=?
                WHERE url=?
                """, (category, priority, url))

    def insert_entry(self, guid, feed_id):
        """Insert entry guid."""
        self.cur.execute("""
                INSERT OR IGNORE
                INTO Entries(guid, feed_id) VALUES(?, ?)
                """, (guid, feed_id))

    def update_feed(self, x):
        """Update feed."""
        self.cur.execute("""
                UPDATE Feeds
                SET refreshed=?, updated=?, title=?, description=?, link=?
                WHERE url=?
                """,
                (x['refreshed'], x['updated'],
                x['title'], x['description'], x['link'],
                x['url']))

    def update_entry(self, x):
        """Update entry."""
        self.cur.execute("""
                UPDATE Entries
                SET refreshed=?, updated=?, title=?, description=?, link=?,
                enc_url=?, enc_length=?, enc_type=?
                WHERE guid=?
                """,
                (x['refreshed'], x['updated'],
                x['title'], x['description'], x['link'],
                x['enc_url'], x['enc_length'], x['enc_type'],
                x['guid']))

    def refresh_feed(self, feed_id, parse_url):
        """Refresh given feed."""
        d = dict(i=feed_id)
        self.cur.execute('SELECT url FROM Feeds WHERE id=:i', d)
        row = self.cur.fetchone()
        if row is None:
            raise Exception('Could not find feed {i}'.format(**d))
        url = row[0]
        try:
            feed, entries = parse_url(url)
        except Exception, e:
            d.update(u=url, e=e.message)
            logger.error('Error parsing {i}: {u}: {e}'.format(**d))
            return 0 # Continue with other feeds.
        self.update_feed(feed)
        for entry in entries:
            self.insert_entry(entry['guid'], feed_id)
            self.update_entry(entry)
        return len(entries)

    def refresh_all(self, parse_url):
        """Refresh and update all feeds and their entries."""
        feed_ids = self.get_feed_ids()
        d = dict(nf=len(feed_ids), ne=0)
        logger.info('Refresh starting for {nf} feeds.'.format(**d))
        for i in feed_ids:
            d['ne'] += self.refresh_feed(i, parse_url)
        logger.info('Refresh done for {nf} feeds, {ne} entries.'.format(**d))

    def get_feed_ids(self):
        """Get all feed ids."""
        self.cur.execute('SELECT id FROM Feeds')
        rows = self.cur.fetchall()
        ids = [row[0] for row in rows]
        return ids

    def n_feeds(self, cat=None):
        """Return the number of feeds in the database."""
        self.cur.execute("""
                SELECT COUNT(*) FROM Feeds
                WHERE (? OR Feeds.category LIKE ?)
                """, (not cat, cat or '%'))
        return self.cur.fetchone()[0]

    def n_entries(self, minprg=0, maxprg=0, cat=None, feed=None):
        """Return the number of entries in the database."""
        self.cur.execute("""
                SELECT COUNT(*)
                FROM Entries INNER JOIN Feeds
                ON Entries.feed_id = Feeds.id
                WHERE (progress between ? and ?)
                        AND (? OR Feeds.category LIKE ?)
                        AND (? OR feed_id = ?)
                """,
                (minprg, maxprg,
                not cat, cat or '%',
                not feed, feed))
        return self.cur.fetchone()[0]

    def get_feed(self, feed_id):
        """Get given feed."""
        d = dict(i=feed_id)
        self.cur.execute('SELECT * FROM Feeds WHERE id=:i', d)
        return self.cur.fetchone()

    def get_feeds(self, cat=None):
        """Get feeds."""
        self.cur.execute("""
                SELECT *
                FROM Feeds
                WHERE (? OR Feeds.category LIKE ?)
                ORDER BY id
                """, (not cat, cat or '%'))
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
        return sorted([row[0] for row in rows])

    def add_feed(self, url, category, priority):
        """Add feed."""
        self.insert_feed(url, category, priority)

    def remove_feed(self, feed_id):
        """Remove given feed and all its entries."""
        d = dict(i=feed_id)
        self.cur.execute('DELETE FROM Entries WHERE feed_id=:i', d)
        self.cur.execute('DELETE FROM Feeds WHERE id=:i', d)

    def get_next(self, minprg=0, maxprg=0, cat=None, feed=None, limit=1):
        """Get next entry or entries."""
        if limit == 0:
            limit = -1
        self.cur.execute("""
                SELECT Entries.*
                FROM Entries INNER JOIN Feeds
                ON Entries.feed_id = Feeds.id
                WHERE (progress between ? and ?)
                        AND (? OR Feeds.category LIKE ?)
                        AND (? OR feed_id = ?)
                ORDER BY priority, updated
                LIMIT ?
                """,
                (minprg, maxprg,
                not cat, cat or '%',
                not feed, feed,
                limit))
        return self.cur.fetchall()

    def set_progress(self, entry_id, progress):
        """Set progress of given entry."""
        d = dict(p=progress, i=entry_id)
        self.cur.execute("""
                UPDATE Entries
                SET progress=:p
                WHERE id=:i
                """, d)

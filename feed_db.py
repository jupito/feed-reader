from __future__ import division, print_function
import sqlite3

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

    def refresh_feed(self, i, parse_url):
        """Refresh given feed."""
        self.cur.execute('SELECT url FROM Feeds WHERE id=?', (i,))
        row = self.cur.fetchone()
        for url in row:
            try:
                feed, entries = parse_url(url)
            except Exception, err:
                print(err)
                print(url)
                continue
            self.update_feed(feed)
            for entry in entries:
                self.insert_entry(entry['guid'], i)
                self.update_entry(entry)

    def refresh_all(self, parse_url):
        """Refresh and update all feeds and their entries."""
        for i in self.get_feed_ids():
            self.refresh_feed(i, parse_url)

    def get_feed_ids(self):
        """Get all feed ids."""
        self.cur.execute('SELECT id FROM Feeds')
        rows = self.cur.fetchall()
        return [row[0] for row in rows]

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

    def get_feed(self, i):
        """Get given feed."""
        self.cur.execute('SELECT * FROM Feeds WHERE id=?', (i,))
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

    def get_entry(self, i):
        """Get given entry."""
        self.cur.execute('SELECT * FROM Entries WHERE id=?', (i,))
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

    def remove_feed(self, i):
        """Remove given feed and all its entries."""
        self.cur.execute('DELETE FROM Entries WHERE feed_id=?', (i,))
        self.cur.execute('DELETE FROM Feeds WHERE id=?', (i,))

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

    def set_progress(self, id, progress):
        """Set progress of given entry."""
        self.cur.execute("""
                UPDATE Entries
                SET progress=?
                WHERE id=?
                """, (progress, id))

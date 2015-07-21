"""Database API."""

from __future__ import division, print_function
import logging
import sqlite3

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

    def update_feed(self, x):
        """Update feed."""
        #self.cur.execute("""
        #    UPDATE Feeds
        #    SET refreshed=?, updated=?, title=?, description=?, link=?
        #    WHERE url=?
        #    """,
        #    (x['refreshed'], x['updated'],
        #    x['title'], x['description'], x['link'],
        #    x['url']))
        self.cur.execute("""
            UPDATE Feeds
            SET refreshed=:refreshed, updated=:updated,
                title=:title, description=:description, link=:link
            WHERE url=:url
            """, x)

    def update_entry(self, x):
        """Update entry."""
        #self.cur.execute("""
        #    UPDATE Entries
        #    SET refreshed=?, updated=?, title=?, description=?, link=?,
        #    enc_url=?, enc_length=?, enc_type=?
        #    WHERE guid=?
        #    """,
        #    (x['refreshed'], x['updated'],
        #    x['title'], x['description'], x['link'],
        #    x['enc_url'], x['enc_length'], x['enc_type'],
        #    x['guid']))
        self.cur.execute("""
            UPDATE Entries
            SET refreshed=:refreshed, updated=:updated,
                title=:title, description=:description, link=:link,
            enc_url=:enc_url, enc_length=:enc_length, enc_type=:enc_type
            WHERE guid=:guid
            """, x)

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
        except (IOError, ValueError) as e:
            d.update(u=url, e=e.message)
            logger.error('Error parsing {i} from {u}: {e}'.format(**d))
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
        d = dict(notcat=not cat, cat=cat or '%')
        self.cur.execute("""
            SELECT COUNT(*) FROM Feeds
            WHERE (:notcat OR Feeds.category LIKE :cat)
            """, d)
        return self.cur.fetchone()[0]

    def n_entries(self, minprg=0, maxprg=0, cat=None, feed=None):
        """Return the number of entries in the database."""
        d = dict(minprg=minprg, maxprg=maxprg,
                 notcat=not cat, cat=cat or '%',
                 notfeed=not feed, feed=feed)
        self.cur.execute("""
            SELECT COUNT(*)
            FROM Entries INNER JOIN Feeds
            ON Entries.feed_id = Feeds.id
            WHERE (progress between :minprg and :maxprg)
                    AND (:notcat OR Feeds.category LIKE :cat)
                    AND (:notfeed OR feed_id = :feed)
            """, d)
        return self.cur.fetchone()[0]

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
        return sorted([row[0] for row in rows])

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
            WHERE (progress between :minprg and :maxprg)
                    AND (:notcat OR Feeds.category LIKE :cat)
                    AND (:notfeed OR feed_id = :feed)
            ORDER BY {order}
            LIMIT :limit
            """.format(order=order)
        self.cur.execute(query, d)
        return self.cur.fetchall()

    def set_progress(self, entry_id, progress):
        """Set progress of given entry."""
        s = 'UPDATE Entries SET progress=:p WHERE id=:i'
        d = dict(p=progress, i=entry_id)
        self.cur.execute(s, d)

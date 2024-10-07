import sqlite3
import pickle

class CacheDatabase:
    def __init__(self, db_path="cache/cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the cache table in the database if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(''' 
            CREATE TABLE IF NOT EXISTS cache ( 
                id INTEGER PRIMARY KEY, 
                key TEXT UNIQUE, 
                result BLOB 
            ) 
        ''')
        conn.commit()
        conn.close()

    def save_cache(self, key, result):
        """Save a new cache entry or update an existing one."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Serialize using pickle to preserve types, including dictionaries
        serialized_result = pickle.dumps(result)

        c.execute('''
            INSERT OR REPLACE INTO cache (key, result) VALUES (?, ?)
        ''', (key, serialized_result))
        conn.commit()
        conn.close()

    def load_cache(self, key):
        """Load a cache entry based on the key."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT result FROM cache WHERE key = ?
        ''', (key,))
        row = c.fetchone()
        conn.close()

        if row:
            # Deserialize with pickle
            result = pickle.loads(row[0])
            return result
        return None

    def load_all_cache(self):
        """Load all cache entries."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT key, result FROM cache')
        rows = c.fetchall()
        conn.close()

        all_cache = {}
        for row in rows:
            key = row[0]
            result = pickle.loads(row[1])
            all_cache[key] = result
            
        return all_cache

    def delete_cache(self, keys):
        """Delete specific cache entries by keys."""
        if not keys:  # Check if the keys list is empty
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Prepare the SQL statement for deleting by keys
        c.execute('DELETE FROM cache WHERE key IN ({seq})'.format(seq=','.join(['?'] * len(keys))), keys)
        
        conn.commit()  # Ensure changes are committed
        conn.close()


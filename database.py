import sqlite3
from datetime import datetime

class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect('chat.db')
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                receiver_id INTEGER,
                FOREIGN KEY (sender_id) REFERENCES users (id),
                FOREIGN KEY (receiver_id) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()

    def register_user(self, username, password):
        try:
            self.cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                              (username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username, password):
        self.cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?',
                          (username, password))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_all_users(self):
        self.cursor.execute('SELECT id, username FROM users')
        return self.cursor.fetchall()

    def save_message(self, sender_id, content, receiver_id=None):
        self.cursor.execute('''
            INSERT INTO messages (sender_id, content, receiver_id, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (sender_id, content, receiver_id, datetime.now()))
        self.conn.commit()

    def get_recent_messages(self, limit=50):
        self.cursor.execute('''
            SELECT u.username, m.content, m.timestamp
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.receiver_id IS NULL
            ORDER BY m.timestamp DESC
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()

    def get_user_dm_history(self, user_id):
        """Get recent DM history for a user"""
        self.cursor.execute('''
            SELECT u.username, m.content, m.timestamp, m.sender_id, m.receiver_id
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? OR m.receiver_id = ?)
            AND m.receiver_id IS NOT NULL
            ORDER BY m.timestamp DESC
            LIMIT 50
        ''', (user_id, user_id))
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close() 
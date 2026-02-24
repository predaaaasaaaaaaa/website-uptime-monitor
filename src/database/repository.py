# src/database/repository.py
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import contextmanager

import config
from .models import User, Website, History

logger = logging.getLogger(__name__)


class DatabaseRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(config.DATABASE_PATH)
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Websites table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS websites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    name TEXT,
                    enabled INTEGER DEFAULT 1,
                    last_status TEXT,
                    last_checked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES users(chat_id),
                    UNIQUE(chat_id, url)
                )
            ''')
            
            # History table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    website_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    response_time REAL,
                    error_message TEXT,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (website_id) REFERENCES websites(id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_websites_chat_id ON websites(chat_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_website_id ON history(website_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_checked_at ON history(checked_at)')
            
            logger.info("Database initialized successfully")
    
    # User operations
    def add_user(self, chat_id: int) -> User:
        """Add or get user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO users (chat_id) VALUES (?)',
                (chat_id,)
            )
        return self.get_user(chat_id)
    
    def get_user(self, chat_id: int) -> Optional[User]:
        """Get user by chat_id"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,))
            row = cursor.fetchone()
            if row:
                return User(chat_id=row['chat_id'], created_at=row['created_at'])
        return None
    
    # Website operations
    def add_website(self, chat_id: int, url: str, name: str = None) -> Website:
        """Add website for user"""
        self.add_user(chat_id)  # Ensure user exists
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO websites (chat_id, url, name) VALUES (?, ?, ?)',
                (chat_id, url, name or url)
            )
            website_id = cursor.lastrowid
        
        return self.get_website(website_id)
    
    def get_website(self, website_id: int) -> Optional[Website]:
        """Get website by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM websites WHERE id = ?', (website_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_website(row)
        return None
    
    def get_user_websites(self, chat_id: int) -> List[Website]:
        """Get all websites for a user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM websites WHERE chat_id = ? ORDER BY created_at DESC',
                (chat_id,)
            )
            return [self._row_to_website(row) for row in cursor.fetchall()]
    
    def get_all_websites(self) -> List[Website]:
        """Get all enabled websites"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM websites WHERE enabled = 1')
            return [self._row_to_website(row) for row in cursor.fetchall()]
    
    def get_website_by_url(self, chat_id: int, url: str) -> Optional[Website]:
        """Get website by URL for user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM websites WHERE chat_id = ? AND url = ?',
                (chat_id, url)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_website(row)
        return None
    
    def remove_website(self, chat_id: int, url: str) -> bool:
        """Remove website"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM websites WHERE chat_id = ? AND url = ?',
                (chat_id, url)
            )
            return cursor.rowcount > 0
    
    def update_website_status(self, website_id: int, status: str):
        """Update website status"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE websites SET last_status = ?, last_checked = ? WHERE id = ?',
                (status, datetime.now(), website_id)
            )
    
    def _row_to_website(self, row) -> Website:
        """Convert row to Website object"""
        return Website(
            id=row['id'],
            chat_id=row['chat_id'],
            url=row['url'],
            name=row['name'],
            enabled=bool(row['enabled']),
            last_status=row['last_status'],
            last_checked=row['last_checked'],
            created_at=row['created_at']
        )
    
    # History operations
    def add_history(self, website_id: int, status: str, 
                    response_time: float = None, error_message: str = None) -> History:
        """Add check history"""
        checked_at = datetime.now()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO history (website_id, status, response_time, error_message, checked_at) 
                   VALUES (?, ?, ?, ?, ?)''',
                (website_id, status, response_time, error_message, checked_at)
            )
            history_id = cursor.lastrowid
        
        return History(
            id=history_id,
            website_id=website_id,
            status=status,
            response_time=response_time,
            error_message=error_message,
            checked_at=checked_at
        )
    
    def get_website_history(self, website_id: int, limit: int = 100) -> List[History]:
        """Get history for website"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM history WHERE website_id = ? 
                   ORDER BY checked_at DESC LIMIT ?''',
                (website_id, limit)
            )
            return [self._row_to_history(row) for row in cursor.fetchall()]
    
    def get_website_last_status(self, website_id: int) -> Optional[str]:
        """Get last status of website"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT status FROM history WHERE website_id = ? ORDER BY checked_at DESC LIMIT 1',
                (website_id,)
            )
            row = cursor.fetchone()
            return row['status'] if row else None
    
    def _row_to_history(self, row) -> History:
        """Convert row to History object"""
        return History(
            id=row['id'],
            website_id=row['website_id'],
            status=row['status'],
            response_time=row['response_time'],
            error_message=row['error_message'],
            checked_at=row['checked_at']
        )

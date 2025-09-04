#!/usr/bin/env python3
"""
Database manager for Nebula CLI using SQLite
Handles authentication, configuration, and data storage
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for the Nebula CLI"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager with optional custom path"""
        if db_path is None:
            # Default to ~/.nebula/nebula_cli.db
            nebula_dir = Path.home() / '.nebula'
            nebula_dir.mkdir(exist_ok=True)
            db_path = str(nebula_dir / 'nebula_cli.db')
        
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create authentication table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS authentication (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT UNIQUE NOT NULL,
                        project_id TEXT,
                        auth_provider TEXT NOT NULL,
                        access_token TEXT,
                        refresh_token TEXT,
                        token_expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Create configuration table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS configuration (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        user_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES authentication (user_id)
                    )
                ''')
                
                # Create audit log table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        action TEXT NOT NULL,
                        details TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                self.logger.info(f"Database initialized at {self.db_path}")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Query execution error: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            self.logger.error(f"Update execution error: {e}")
            raise
    
    # Authentication methods
    def store_auth_data(self, user_id: str, project_id: str, auth_provider: str, 
                       access_token: str, refresh_token: str = None, 
                       token_expires_at: datetime = None) -> bool:
        """Store authentication data"""
        try:
            query = '''
                INSERT OR REPLACE INTO authentication 
                (user_id, project_id, auth_provider, access_token, refresh_token, 
                 token_expires_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
            '''
            params = (user_id, project_id, auth_provider, access_token, 
                     refresh_token, token_expires_at)
            
            self.execute_update(query, params)
            self.logger.info(f"Authentication data stored for user: {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store auth data: {e}")
            return False
    
    def get_auth_data(self, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get authentication data for user or most recent active user"""
        try:
            if user_id:
                query = '''
                    SELECT * FROM authentication 
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY updated_at DESC LIMIT 1
                '''
                params = (user_id,)
            else:
                query = '''
                    SELECT * FROM authentication 
                    WHERE is_active = 1
                    ORDER BY updated_at DESC LIMIT 1
                '''
                params = ()
            
            results = self.execute_query(query, params)
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"Failed to get auth data: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        auth_data = self.get_auth_data()
        if not auth_data:
            return False
        
        # Check if token is expired
        if auth_data.get('token_expires_at'):
            try:
                expires_at = datetime.fromisoformat(auth_data['token_expires_at'])
                if datetime.now() >= expires_at:
                    self.logger.info("Authentication token expired")
                    return False
            except ValueError:
                self.logger.warning("Invalid token expiration format")
        
        return True
    
    def logout(self, user_id: str = None) -> bool:
        """Logout user by deactivating their authentication"""
        try:
            if user_id:
                query = '''
                    UPDATE authentication 
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                '''
                params = (user_id,)
            else:
                query = '''
                    UPDATE authentication 
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE is_active = 1
                '''
                params = ()
            
            affected_rows = self.execute_update(query, params)
            if affected_rows > 0:
                self.logger.info(f"User logged out: {user_id or 'all users'}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to logout: {e}")
            return False
    
    # Configuration methods
    def set_config(self, key: str, value: Any, description: str = None) -> bool:
        """Set configuration value"""
        try:
            # Convert value to JSON string if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            query = '''
                INSERT OR REPLACE INTO configuration 
                (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            '''
            params = (key, value, description)
            
            self.execute_update(query, params)
            self.logger.info(f"Configuration set: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set config: {e}")
            return False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            query = 'SELECT value FROM configuration WHERE key = ?'
            results = self.execute_query(query, (key,))
            
            if not results:
                return default
            
            value = results[0]['value']
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            self.logger.error(f"Failed to get config: {e}")
            return default
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values"""
        try:
            query = 'SELECT key, value FROM configuration'
            results = self.execute_query(query)
            
            config = {}
            for row in results:
                key = row['key']
                value = row['value']
                
                # Try to parse as JSON, fallback to string
                try:
                    config[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    config[key] = value
            
            return config
        except Exception as e:
            self.logger.error(f"Failed to get all config: {e}")
            return {}
    
    # Session methods
    def create_session(self, user_id: str) -> str:
        """Create a new user session"""
        try:
            import uuid
            session_id = str(uuid.uuid4())
            
            query = '''
                INSERT INTO user_sessions (session_id, user_id)
                VALUES (?, ?)
            '''
            self.execute_update(query, (session_id, user_id))
            
            self.logger.info(f"Session created for user: {user_id}")
            return session_id
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return None
    
    def update_session(self, session_id: str) -> bool:
        """Update session last accessed time"""
        try:
            query = '''
                UPDATE user_sessions 
                SET last_accessed = CURRENT_TIMESTAMP
                WHERE session_id = ? AND is_active = 1
            '''
            affected_rows = self.execute_update(query, (session_id,))
            return affected_rows > 0
        except Exception as e:
            self.logger.error(f"Failed to update session: {e}")
            return False
    
    def end_session(self, session_id: str) -> bool:
        """End a user session"""
        try:
            query = '''
                UPDATE user_sessions 
                SET is_active = 0
                WHERE session_id = ?
            '''
            affected_rows = self.execute_update(query, (session_id,))
            return affected_rows > 0
        except Exception as e:
            self.logger.error(f"Failed to end session: {e}")
            return False
    
    # Audit logging
    def log_action(self, user_id: str, action: str, details: str = None, 
                   ip_address: str = None, user_agent: str = None) -> bool:
        """Log user action for audit trail"""
        try:
            query = '''
                INSERT INTO audit_log (user_id, action, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            '''
            params = (user_id, action, details, ip_address, user_agent)
            self.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Failed to log action: {e}")
            return False
    
    def get_audit_log(self, user_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        try:
            if user_id:
                query = '''
                    SELECT * FROM audit_log 
                    WHERE user_id = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                '''
                params = (user_id, limit)
            else:
                query = '''
                    SELECT * FROM audit_log 
                    ORDER BY created_at DESC 
                    LIMIT ?
                '''
                params = (limit,)
            
            return self.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"Failed to get audit log: {e}")
            return []
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up old inactive sessions"""
        try:
            query = '''
                UPDATE user_sessions 
                SET is_active = 0
                WHERE last_accessed < datetime('now', '-{} days')
                AND is_active = 1
            '''.format(days)
            
            affected_rows = self.execute_update(query)
            self.logger.info(f"Cleaned up {affected_rows} old sessions")
            return affected_rows
        except Exception as e:
            self.logger.error(f"Failed to cleanup sessions: {e}")
            return 0

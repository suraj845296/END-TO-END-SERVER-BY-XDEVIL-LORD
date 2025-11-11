import sqlite3
import hashlib
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="e2ee_facebook.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                approval_status TEXT DEFAULT 'pending',
                approval_key TEXT,
                real_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # User configurations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id TEXT,
                name_prefix TEXT,
                delay INTEGER DEFAULT 10,
                cookies TEXT,
                messages_file_content TEXT,
                automation_running BOOLEAN DEFAULT FALSE,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Automation logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def create_user(self, username, password):
        """Create new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, "Username already exists"
            
            # Hash password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, password_hash) 
                VALUES (?, ?)
            ''', (username, password_hash))
            
            user_id = cursor.lastrowid
            
            # Create default configuration
            cursor.execute('''
                INSERT INTO user_configs (user_id, delay) 
                VALUES (?, ?)
            ''', (user_id, 10))
            
            conn.commit()
            conn.close()
            
            return True, "User created successfully", user_id
            
        except Exception as e:
            return False, f"Error creating user: {str(e)}"

    def verify_user(self, username, password):
        """Verify user credentials"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                SELECT id FROM users 
                WHERE username = ? AND password_hash = ? AND is_active = TRUE
            ''', (username, password_hash))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            print(f"Error verifying user: {e}")
            return None

    def get_approval_status(self, user_id):
        """Get user approval status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT approval_status FROM users WHERE id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 'pending'
            
        except Exception as e:
            print(f"Error getting approval status: {e}")
            return 'pending'

    def set_approval_key(self, user_id, approval_key):
        """Set approval key for user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET approval_key = ? WHERE id = ?
            ''', (approval_key, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error setting approval key: {e}")
            return False

    def get_approval_key(self, user_id):
        """Get approval key for user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT approval_key FROM users WHERE id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            print(f"Error getting approval key: {e}")
            return None

    def update_approval_status(self, user_id, status):
        """Update user approval status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET approval_status = ? WHERE id = ?
            ''', (status, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error updating approval status: {e}")
            return False

    def update_user_real_name(self, user_id, real_name):
        """Update user real name"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET real_name = ? WHERE id = ?
            ''', (real_name, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error updating real name: {e}")
            return False

    def get_user_config(self, user_id):
        """Get user configuration"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT chat_id, name_prefix, delay, cookies, messages_file_content 
                FROM user_configs WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'chat_id': result[0] or '',
                    'name_prefix': result[1] or '',
                    'delay': result[2] or 10,
                    'cookies': result[3] or '',
                    'messages_file_content': result[4] or ''
                }
            else:
                # Return default config if not found
                return {
                    'chat_id': '',
                    'name_prefix': '',
                    'delay': 10,
                    'cookies': '',
                    'messages_file_content': ''
                }
                
        except Exception as e:
            print(f"Error getting user config: {e}")
            return {
                'chat_id': '',
                'name_prefix': '',
                'delay': 10,
                'cookies': '',
                'messages_file_content': ''
            }

    def update_user_config(self, user_id, chat_id, name_prefix, delay, cookies, messages_file_content):
        """Update user configuration"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if config exists
            cursor.execute('SELECT id FROM user_configs WHERE user_id = ?', (user_id,))
            if cursor.fetchone():
                # Update existing config
                cursor.execute('''
                    UPDATE user_configs 
                    SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, 
                        messages_file_content = ?, last_updated = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (chat_id, name_prefix, delay, cookies, messages_file_content, user_id))
            else:
                # Insert new config
                cursor.execute('''
                    INSERT INTO user_configs 
                    (user_id, chat_id, name_prefix, delay, cookies, messages_file_content) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, chat_id, name_prefix, delay, cookies, messages_file_content))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error updating user config: {e}")
            return False

    def set_automation_running(self, user_id, running):
        """Set automation running status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_configs SET automation_running = ? WHERE user_id = ?
            ''', (running, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error setting automation running: {e}")
            return False

    def get_automation_running(self, user_id):
        """Get automation running status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT automation_running FROM user_configs WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else False
            
        except Exception as e:
            print(f"Error getting automation running: {e}")
            return False

    def get_username(self, user_id):
        """Get username by user ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else "Unknown"
            
        except Exception as e:
            print(f"Error getting username: {e}")
            return "Unknown"

    def get_pending_approvals(self):
        """Get all pending approval users"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, approval_key, real_name 
                FROM users 
                WHERE approval_status = 'pending' AND is_active = TRUE
                ORDER BY created_at DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"Error getting pending approvals: {e}")
            return []

    def get_all_users(self):
        """Get all users"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, approval_status, real_name, approval_key 
                FROM users 
                WHERE is_active = TRUE
                ORDER BY created_at DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    def add_automation_log(self, user_id, log_message):
        """Add automation log"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO automation_logs (user_id, log_message) 
                VALUES (?, ?)
            ''', (user_id, log_message))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error adding automation log: {e}")
            return False

    def get_automation_logs(self, user_id, limit=50):
        """Get automation logs for user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT log_message, created_at 
                FROM automation_logs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"Error getting automation logs: {e}")
            return []

# Create global database instance
db = Database()

import sqlite3
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pathlib import Path
from config import Config

class Database:
    """Database handler untuk bot"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self):
        """Buat koneksi database"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_database(self):
        """Inisialisasi tabel database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Tabel Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_downloads INTEGER DEFAULT 0,
                daily_downloads INTEGER DEFAULT 0,
                last_download_date DATE,
                is_banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                is_premium INTEGER DEFAULT 0,
                language TEXT DEFAULT 'id'
            )
        ''')

        # Tabel Admins
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                added_by INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role TEXT DEFAULT 'admin'
            )
        ''')

        # Tabel Download History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT,
                platform TEXT,
                title TEXT,
                file_size INTEGER,
                download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                rating INTEGER
            )
        ''')

        # Tabel Bot Settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabel Broadcast History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                message TEXT,
                total_users INTEGER,
                success_count INTEGER,
                failed_count INTEGER,
                broadcast_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabel Banned Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                banned_by INTEGER,
                reason TEXT,
                ban_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    # ═══════════════════════════════════════════════════════════
    # USER MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def add_user(self, user_id: int, username: str = None,
                 first_name: str = None, last_name: str = None) -> bool:
        """Tambah atau update user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, join_date, last_active)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_active = CURRENT_TIMESTAMP
        ''', (user_id, username, first_name, last_name))

        conn.commit()
        conn.close()
        return True

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Ambil data user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            columns = ['user_id', 'username', 'first_name', 'last_name', 'join_date',
                      'last_active', 'total_downloads', 'daily_downloads',
                      'last_download_date', 'is_banned', 'ban_reason', 'is_premium', 'language']
            return dict(zip(columns, row))
        return None

    def get_all_users(self) -> List[Dict]:
        """Ambil semua user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id, username, first_name, total_downloads, is_banned FROM users ORDER BY total_downloads DESC')
        rows = cursor.fetchall()
        conn.close()

        users = []
        for row in rows:
            users.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'total_downloads': row[3],
                'is_banned': row[4]
            })
        return users

    def get_user_count(self) -> int:
        """Hitung total user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_active_users_today(self) -> int:
        """Hitung user aktif hari ini"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM users
            WHERE DATE(last_active) = DATE('now')
        ''')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def update_download_count(self, user_id: int) -> bool:
        """Update jumlah download user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Cek apakah perlu reset daily downloads
        cursor.execute('''
            UPDATE users SET
                daily_downloads = CASE
                    WHEN DATE(last_download_date) != DATE('now') THEN 1
                    ELSE daily_downloads + 1
                END,
                total_downloads = total_downloads + 1,
                last_download_date = DATE('now'),
                last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))

        conn.commit()
        conn.close()
        return True

    def check_daily_limit(self, user_id: int) -> tuple:
        """Cek apakah user sudah mencapai limit harian"""
        user = self.get_user(user_id)
        if not user:
            return (True, Config.DAILY_LIMIT)  # User baru, belum ada limit

        # Reset jika hari berbeda
        if user['last_download_date'] != str(date.today()):
            return (True, Config.DAILY_LIMIT)

        remaining = Config.DAILY_LIMIT - user['daily_downloads']
        return (remaining > 0, remaining)

    # ═══════════════════════════════════════════════════════════
    # BAN MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def ban_user(self, user_id: int, banned_by: int, reason: str = "No reason") -> bool:
        """Ban user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Update status ban di tabel users
        cursor.execute('''
            UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?
        ''', (reason, user_id))

        # Tambah ke tabel banned_users
        cursor.execute('''
            INSERT OR REPLACE INTO banned_users (user_id, banned_by, reason, ban_date)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, banned_by, reason))

        conn.commit()
        conn.close()
        return True

    def unban_user(self, user_id: int) -> bool:
        """Unban user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))

        conn.commit()
        conn.close()
        return True

    def is_banned(self, user_id: int) -> bool:
        """Cek apakah user dibanned"""
        user = self.get_user(user_id)
        return user and user['is_banned'] == 1

    def get_banned_users(self) -> List[Dict]:
        """Ambil daftar user yang dibanned"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT b.user_id, u.username, u.first_name, b.reason, b.ban_date, b.banned_by
            FROM banned_users b
            LEFT JOIN users u ON b.user_id = u.user_id
            ORDER BY b.ban_date DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        return [{'user_id': r[0], 'username': r[1], 'first_name': r[2],
                 'reason': r[3], 'ban_date': r[4], 'banned_by': r[5]} for r in rows]

    # ═══════════════════════════════════════════════════════════
    # ADMIN MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def add_admin(self, user_id: int, username: str, added_by: int, role: str = "admin") -> bool:
        """Tambah admin baru"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO admins (user_id, username, added_by, added_date, role)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        ''', (user_id, username, added_by, role))

        conn.commit()
        conn.close()
        return True

    def remove_admin(self, user_id: int) -> bool:
        """Hapus admin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True

    def get_admins(self) -> List[Dict]:
        """Ambil daftar admin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins ORDER BY added_date')
        rows = cursor.fetchall()
        conn.close()

        return [{'user_id': r[0], 'username': r[1], 'added_by': r[2],
                 'added_date': r[3], 'role': r[4]} for r in rows]

    def is_admin_in_db(self, user_id: int) -> bool:
        """Cek apakah user adalah admin di database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    # ═══════════════════════════════════════════════════════════
    # DOWNLOAD HISTORY
    # ═══════════════════════════════════════════════════════════

    def add_download(self, user_id: int, url: str, platform: str,
                     title: str, file_size: int, status: str = "success",
                     error_message: str = None) -> Optional[int]:
        """Simpan history download dan return ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO downloads (user_id, url, platform, title, file_size, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, url, platform, title, file_size, status, error_message))

            download_id = cursor.lastrowid
            conn.commit()
            return download_id
        except Exception as e:
            print(f"Error adding download: {e}")
            return None
        finally:
            conn.close()

    def get_download_stats(self) -> Dict:
        """Ambil statistik download"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Total downloads
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE status = "success"')
        total = cursor.fetchone()[0]

        # Downloads hari ini
        cursor.execute('''
            SELECT COUNT(*) FROM downloads
            WHERE DATE(download_date) = DATE('now') AND status = "success"
        ''')
        today = cursor.fetchone()[0]

        # Downloads per platform
        cursor.execute('''
            SELECT platform, COUNT(*) as count FROM downloads
            WHERE status = "success"
            GROUP BY platform ORDER BY count DESC LIMIT 10
        ''')
        platforms = cursor.fetchall()

        # Top users
        cursor.execute('''
            SELECT user_id, COUNT(*) as count FROM downloads
            WHERE status = "success"
            GROUP BY user_id ORDER BY count DESC LIMIT 5
        ''')
        top_users = cursor.fetchall()

        conn.close()

        return {
            'total': total,
            'today': today,
            'platforms': [{'name': p[0], 'count': p[1]} for p in platforms],
            'top_users': [{'user_id': u[0], 'count': u[1]} for u in top_users]
        }

    def get_recent_downloads(self, limit: int = 10) -> List[Dict]:
        """Ambil download terbaru"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT d.*, u.username, u.first_name
            FROM downloads d
            LEFT JOIN users u ON d.user_id = u.user_id
            ORDER BY d.download_date DESC LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [{'id': r[0], 'user_id': r[1], 'url': r[2], 'platform': r[3],
                 'title': r[4], 'file_size': r[5], 'download_date': r[6],
                 'status': r[7], 'username': r[9], 'first_name': r[10]} for r in rows]

    def update_download_rating(self, download_id: int, rating: int) -> bool:
        """Update rating untuk download tertentu"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('UPDATE downloads SET rating = ? WHERE id = ?', (rating, download_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating rating: {e}")
            return False
        finally:
            conn.close()

    # ═══════════════════════════════════════════════════════════
    # SETTINGS MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Ambil setting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            try:
                return json.loads(row[0])
            except:
                return row[0]
        return default

    def set_setting(self, key: str, value: Any) -> bool:
        """Set setting"""
        conn = self.get_connection()
        cursor = conn.cursor()

        value_str = json.dumps(value) if not isinstance(value, str) else value

        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value_str))

        conn.commit()
        conn.close()
        return True

    # ═══════════════════════════════════════════════════════════
    # BROADCAST
    # ═══════════════════════════════════════════════════════════

    def save_broadcast(self, admin_id: int, message: str,
                       total: int, success: int, failed: int) -> bool:
        """Simpan history broadcast"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO broadcasts (admin_id, message, total_users, success_count, failed_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (admin_id, message[:500], total, success, failed))

        conn.commit()
        conn.close()
        return True

    def get_all_user_ids(self) -> List[int]:
        """Ambil semua user ID untuk broadcast"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_banned = 0')
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]


# Instance global
db = Database()
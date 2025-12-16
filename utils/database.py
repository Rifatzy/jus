import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import os


# Database path - define here to avoid circular import
DATABASE_PATH = "bot_database.db"


@dataclass
class User:
    user_id: int
    username: str
    first_name: str
    join_date: str
    total_downloads: int
    is_banned: bool
    is_premium: bool = False
    language: str = "id"


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _init_db(self):
        """Initialize database - called separately"""
        if self._initialized:
            return

        self.db_path = DATABASE_PATH
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                last_name TEXT DEFAULT '',
                join_date TEXT,
                last_active TEXT,
                total_downloads INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                is_premium INTEGER DEFAULT 0,
                premium_until TEXT,
                language TEXT DEFAULT 'id',
                quality_mode TEXT DEFAULT 'ask',
                notifications INTEGER DEFAULT 1,
                ban_reason TEXT,
                admin_notes TEXT
            )
        ''')

        # Downloads table
        c.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                platform TEXT,
                url TEXT,
                media_type TEXT,
                quality TEXT DEFAULT 'best',
                title TEXT DEFAULT '',
                author TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                duration INTEGER DEFAULT 0,
                timestamp TEXT,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Feedback table
        c.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                timestamp TEXT,
                replied INTEGER DEFAULT 0,
                reply_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Broadcasts table
        c.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                message TEXT,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                timestamp TEXT
            )
        ''')

        # Activity log table
        c.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')

        # Create indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_dl_user ON downloads(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_dl_time ON downloads(timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_dl_platform ON downloads(platform)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium)')

        conn.commit()
        conn.close()

        self._initialized = True

    def _conn(self):
        if not self._initialized:
            self._init_db()
        return sqlite3.connect(self.db_path)

    # ========== USER METHODS ==========

    def add_user(self, user_id: int, username: str = "", first_name: str = "", last_name: str = ""):
        conn = self._conn()
        c = conn.cursor()
        now = datetime.now().isoformat()

        c.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, join_date, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_active = excluded.last_active
        ''', (user_id, username, first_name, last_name, now, now))

        conn.commit()
        conn.close()

    def get_user(self, user_id: int) -> Optional[User]:
        conn = self._conn()
        c = conn.cursor()
        c.execute('''
            SELECT user_id, username, first_name, join_date,
                   total_downloads, is_banned, is_premium, language
            FROM users WHERE user_id = ?
        ''', (user_id,))
        row = c.fetchone()
        conn.close()

        if row:
            return User(row[0], row[1], row[2], row[3], row[4], bool(row[5]), bool(row[6]), row[7] or 'id')
        return None

    def is_banned(self, user_id: int) -> bool:
        conn = self._conn()
        c = conn.cursor()
        c.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        return bool(row[0]) if row else False

    def is_premium(self, user_id: int) -> bool:
        conn = self._conn()
        c = conn.cursor()
        c.execute('SELECT is_premium, premium_until FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()

        if not row or not row[0]:
            return False

        if row[1]:
            try:
                until = datetime.fromisoformat(row[1])
                if until < datetime.now():
                    return False
            except:
                pass

        return True

    def ban_user(self, user_id: int, reason: str = ""):
        conn = self._conn()
        c = conn.cursor()
        c.execute('UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?', (reason, user_id))
        conn.commit()
        conn.close()
        self.log_activity(user_id, "banned", reason)

    def unban_user(self, user_id: int):
        conn = self._conn()
        c = conn.cursor()
        c.execute('UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        self.log_activity(user_id, "unbanned", "")

    def set_premium(self, user_id: int, days: int = 30):
        conn = self._conn()
        c = conn.cursor()
        until = (datetime.now() + timedelta(days=days)).isoformat()
        c.execute('UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?', (until, user_id))
        conn.commit()
        conn.close()
        self.log_activity(user_id, "premium_set", f"{days} days")

    def remove_premium(self, user_id: int):
        conn = self._conn()
        c = conn.cursor()
        c.execute('UPDATE users SET is_premium = 0, premium_until = NULL WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        self.log_activity(user_id, "premium_removed", "")

    def get_all_user_ids(self) -> List[int]:
        conn = self._conn()
        c = conn.cursor()
        c.execute('SELECT user_id FROM users WHERE is_banned = 0')
        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def get_users_paginated(self, page: int = 1, per_page: int = 10) -> Tuple[List[User], int]:
        conn = self._conn()
        c = conn.cursor()

        c.execute('SELECT COUNT(*) FROM users')
        total = c.fetchone()[0]

        offset = (page - 1) * per_page
        c.execute('''
            SELECT user_id, username, first_name, join_date,
                   total_downloads, is_banned, is_premium, language
            FROM users ORDER BY total_downloads DESC LIMIT ? OFFSET ?
        ''', (per_page, offset))

        users = [User(r[0], r[1], r[2], r[3], r[4], bool(r[5]), bool(r[6]), r[7] or 'id') for r in c.fetchall()]
        conn.close()

        return users, total

    def search_users(self, query: str) -> List[User]:
        conn = self._conn()
        c = conn.cursor()

        try:
            user_id = int(query)
            c.execute('''
                SELECT user_id, username, first_name, join_date,
                       total_downloads, is_banned, is_premium, language
                FROM users WHERE user_id = ?
            ''', (user_id,))
        except:
            c.execute('''
                SELECT user_id, username, first_name, join_date,
                       total_downloads, is_banned, is_premium, language
                FROM users
                WHERE username LIKE ? OR first_name LIKE ?
                LIMIT 20
            ''', (f'%{query}%', f'%{query}%'))

        users = [User(r[0], r[1], r[2], r[3], r[4], bool(r[5]), bool(r[6]), r[7] or 'id') for r in c.fetchall()]
        conn.close()

        return users

    def set_user_language(self, user_id: int, lang: str):
        conn = self._conn()
        c = conn.cursor()
        c.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
        conn.commit()
        conn.close()

    def get_user_language(self, user_id: int) -> str:
        conn = self._conn()
        c = conn.cursor()
        c.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row and row[0] else 'id'

    def get_quality_mode(self, user_id: int) -> str:
        conn = self._conn()
        c = conn.cursor()
        c.execute('SELECT quality_mode FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 'ask'

    def set_quality_mode(self, user_id: int, mode: str):
        conn = self._conn()
        c = conn.cursor()
        c.execute('UPDATE users SET quality_mode = ? WHERE user_id = ?', (mode, user_id))
        conn.commit()
        conn.close()

    def get_notifications(self, user_id: int) -> bool:
        conn = self._conn()
        c = conn.cursor()
        c.execute('SELECT notifications FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        return bool(row[0]) if row else True

    def set_notifications(self, user_id: int, enabled: bool):
        conn = self._conn()
        c = conn.cursor()
        c.execute('UPDATE users SET notifications = ? WHERE user_id = ?', (1 if enabled else 0, user_id))
        conn.commit()
        conn.close()

    def add_admin_note(self, user_id: int, note: str):
        conn = self._conn()
        c = conn.cursor()
        c.execute('UPDATE users SET admin_notes = ? WHERE user_id = ?', (note, user_id))
        conn.commit()
        conn.close()

    def get_admin_note(self, user_id: int) -> str:
        conn = self._conn()
        c = conn.cursor()
        c.execute('SELECT admin_notes FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row and row[0] else ""

    # ========== DOWNLOAD METHODS ==========

    def add_download(self, user_id: int, platform: str, url: str, media_type: str,
                     quality: str = "best", title: str = "", author: str = "",
                     file_size: int = 0, duration: int = 0, success: bool = True,
                     error_message: str = ""):
        conn = self._conn()
        c = conn.cursor()
        now = datetime.now().isoformat()

        c.execute('''
            INSERT INTO downloads
            (user_id, platform, url, media_type, quality, title, author, file_size, duration, timestamp, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, platform, url, media_type, quality, title, author, file_size, duration, now, 1 if success else 0, error_message))

        if success:
            c.execute('UPDATE users SET total_downloads = total_downloads + 1, last_active = ? WHERE user_id = ?', (now, user_id))

        conn.commit()
        conn.close()

    def get_user_history(self, user_id: int, limit: int = 5, offset: int = 0) -> List[dict]:
        conn = self._conn()
        c = conn.cursor()

        c.execute('''
            SELECT platform, url, media_type, quality, title, author, file_size, timestamp
            FROM downloads WHERE user_id = ? AND success = 1
            ORDER BY timestamp DESC LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))

        history = []
        for r in c.fetchall():
            history.append({
                'platform': r[0], 'url': r[1], 'media_type': r[2], 'quality': r[3],
                'title': r[4] or 'Untitled', 'author': r[5] or 'Unknown',
                'file_size': r[6], 'timestamp': r[7]
            })

        conn.close()
        return history

    def get_user_history_count(self, user_id: int) -> int:
        conn = self._conn()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM downloads WHERE user_id = ? AND success = 1', (user_id,))
        count = c.fetchone()[0]
        conn.close()
        return count

    def clear_user_history(self, user_id: int):
        conn = self._conn()
        c = conn.cursor()
        c.execute('DELETE FROM downloads WHERE user_id = ?', (user_id,))
        c.execute('UPDATE users SET total_downloads = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    # ========== STATS METHODS ==========

    def get_user_stats(self, user_id: int) -> dict:
        conn = self._conn()
        c = conn.cursor()

        c.execute('SELECT join_date, total_downloads, is_premium FROM users WHERE user_id = ?', (user_id,))
        user_row = c.fetchone()

        c.execute('''
            SELECT
                SUM(CASE WHEN platform = 'tiktok' THEN 1 ELSE 0 END),
                SUM(CASE WHEN platform = 'instagram' THEN 1 ELSE 0 END),
                SUM(CASE WHEN platform = 'twitter' THEN 1 ELSE 0 END),
                SUM(CASE WHEN media_type = 'video' THEN 1 ELSE 0 END),
                SUM(CASE WHEN media_type = 'audio' THEN 1 ELSE 0 END),
                SUM(CASE WHEN media_type = 'image' THEN 1 ELSE 0 END),
                SUM(file_size)
            FROM downloads WHERE user_id = ? AND success = 1
        ''', (user_id,))
        dl_row = c.fetchone()

        today = datetime.now().date().isoformat()
        c.execute("SELECT COUNT(*) FROM downloads WHERE user_id = ? AND success = 1 AND DATE(timestamp) = ?", (user_id, today))
        today_count = c.fetchone()[0]

        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        c.execute("SELECT COUNT(*) FROM downloads WHERE user_id = ? AND success = 1 AND timestamp >= ?", (user_id, week_ago))
        week_count = c.fetchone()[0]

        c.execute('''
            SELECT platform FROM downloads
            WHERE user_id = ? AND success = 1
            GROUP BY platform ORDER BY COUNT(*) DESC LIMIT 1
        ''', (user_id,))
        fav_row = c.fetchone()

        conn.close()

        return {
            'join_date': user_row[0] if user_row else None,
            'total': user_row[1] if user_row else 0,
            'is_premium': bool(user_row[2]) if user_row else False,
            'tiktok': dl_row[0] or 0 if dl_row else 0,
            'instagram': dl_row[1] or 0 if dl_row else 0,
            'twitter': dl_row[2] or 0 if dl_row else 0,
            'videos': dl_row[3] or 0 if dl_row else 0,
            'audios': dl_row[4] or 0 if dl_row else 0,
            'images': dl_row[5] or 0 if dl_row else 0,
            'total_size': dl_row[6] or 0 if dl_row else 0,
            'today': today_count,
            'this_week': week_count,
            'favorite': fav_row[0] if fav_row else None,
        }

    def get_global_stats(self) -> dict:
        conn = self._conn()
        c = conn.cursor()

        c.execute('SELECT COUNT(*) FROM users')
        total_users = c.fetchone()[0]

        c.execute('SELECT COUNT(*) FROM users WHERE is_banned = 1')
        banned = c.fetchone()[0]

        c.execute('SELECT COUNT(*) FROM users WHERE is_premium = 1')
        premium = c.fetchone()[0]

        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        c.execute('SELECT COUNT(*) FROM users WHERE last_active >= ?', (week_ago,))
        active = c.fetchone()[0]

        c.execute('SELECT COUNT(*), SUM(file_size) FROM downloads WHERE success = 1')
        dl_row = c.fetchone()
        total_downloads = dl_row[0] or 0
        total_size = dl_row[1] or 0

        today = datetime.now().date().isoformat()
        c.execute("SELECT COUNT(*) FROM downloads WHERE success = 1 AND DATE(timestamp) = ?", (today,))
        today_dl = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM users WHERE DATE(join_date) = ?", (today,))
        new_users = c.fetchone()[0]

        c.execute('SELECT platform, COUNT(*) FROM downloads WHERE success = 1 GROUP BY platform')
        platforms = dict(c.fetchall())

        c.execute('''
            SELECT user_id, username, first_name, total_downloads
            FROM users ORDER BY total_downloads DESC LIMIT 10
        ''')
        top_users = [{'id': r[0], 'username': r[1], 'name': r[2] or r[1] or str(r[0]), 'downloads': r[3]} for r in c.fetchall()]

        conn.close()

        return {
            'total_users': total_users,
            'active_users': active,
            'banned': banned,
            'premium': premium,
            'new_today': new_users,
            'total_downloads': total_downloads,
            'total_size': total_size,
            'today_downloads': today_dl,
            'platforms': platforms,
            'top_users': top_users,
        }

    # ========== FEEDBACK METHODS ==========

    def add_feedback(self, user_id: int, message: str):
        conn = self._conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO feedback (user_id, message, timestamp)
            VALUES (?, ?, ?)
        ''', (user_id, message, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_feedbacks(self, limit: int = 20, unreplied_only: bool = False) -> List[dict]:
        conn = self._conn()
        c = conn.cursor()

        if unreplied_only:
            c.execute('''
                SELECT f.id, f.user_id, u.username, u.first_name, f.message, f.timestamp
                FROM feedback f
                LEFT JOIN users u ON f.user_id = u.user_id
                WHERE f.replied = 0
                ORDER BY f.timestamp DESC LIMIT ?
            ''', (limit,))
        else:
            c.execute('''
                SELECT f.id, f.user_id, u.username, u.first_name, f.message, f.timestamp
                FROM feedback f
                LEFT JOIN users u ON f.user_id = u.user_id
                ORDER BY f.timestamp DESC LIMIT ?
            ''', (limit,))

        feedbacks = []
        for r in c.fetchall():
            feedbacks.append({
                'id': r[0], 'user_id': r[1], 'username': r[2] or '',
                'name': r[3] or '', 'message': r[4], 'timestamp': r[5]
            })

        conn.close()
        return feedbacks

    def mark_feedback_replied(self, feedback_id: int, reply: str = ""):
        conn = self._conn()
        c = conn.cursor()
        c.execute('UPDATE feedback SET replied = 1, reply_message = ? WHERE id = ?', (reply, feedback_id))
        conn.commit()
        conn.close()

    # ========== BROADCAST METHODS ==========

    def add_broadcast(self, admin_id: int, message: str, sent: int, failed: int):
        conn = self._conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO broadcasts (admin_id, message, sent_count, failed_count, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (admin_id, message, sent, failed, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_broadcasts(self, limit: int = 10) -> List[dict]:
        conn = self._conn()
        c = conn.cursor()
        c.execute('''
            SELECT id, admin_id, message, sent_count, failed_count, timestamp
            FROM broadcasts ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))

        broadcasts = []
        for r in c.fetchall():
            broadcasts.append({
                'id': r[0], 'admin_id': r[1], 'message': r[2][:100],
                'sent': r[3], 'failed': r[4], 'timestamp': r[5]
            })

        conn.close()
        return broadcasts

    # ========== ACTIVITY LOG ==========

    def log_activity(self, user_id: int, action: str, details: str = ""):
        conn = self._conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO activity_log (user_id, action, details, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, details, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_user_activity_log(self, user_id: int, limit: int = 20) -> List[dict]:
        conn = self._conn()
        c = conn.cursor()
        c.execute('''
            SELECT action, details, timestamp
            FROM activity_log WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (user_id, limit))

        logs = [{'action': r[0], 'details': r[1], 'timestamp': r[2]} for r in c.fetchall()]
        conn.close()
        return logs


# Create instance but don't initialize yet
db = Database()
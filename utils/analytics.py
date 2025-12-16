import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict


class Analytics:
    """Analytics dan reporting"""

    def __init__(self, database):
        self.db = database

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily download statistics"""
        conn = self.db._conn()
        c = conn.cursor()

        stats = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date().isoformat()

            c.execute('''
                SELECT COUNT(*), COUNT(DISTINCT user_id)
                FROM downloads WHERE DATE(timestamp) = ?
            ''', (date,))
            row = c.fetchone()

            stats.append({
                'date': date,
                'downloads': row[0] or 0,
                'users': row[1] or 0
            })

        conn.close()
        return stats

    def get_hourly_stats(self) -> List[Dict]:
        """Get hourly stats for today"""
        conn = self.db._conn()
        c = conn.cursor()

        today = datetime.now().date().isoformat()

        c.execute('''
            SELECT strftime('%H', timestamp) as hour, COUNT(*)
            FROM downloads
            WHERE DATE(timestamp) = ?
            GROUP BY hour
            ORDER BY hour
        ''', (today,))

        rows = c.fetchall()
        conn.close()

        hour_map = {r[0]: r[1] for r in rows}
        stats = []
        for h in range(24):
            hour_str = f"{h:02d}"
            stats.append({
                'hour': hour_str,
                'count': hour_map.get(hour_str, 0)
            })

        return stats

    def get_platform_breakdown(self, days: int = 30) -> Dict:
        """Get platform breakdown"""
        conn = self.db._conn()
        c = conn.cursor()

        date_from = (datetime.now() - timedelta(days=days)).isoformat()

        c.execute('''
            SELECT platform, COUNT(*) as count
            FROM downloads
            WHERE timestamp >= ?
            GROUP BY platform
            ORDER BY count DESC
        ''', (date_from,))

        result = dict(c.fetchall())
        conn.close()

        return result

    def get_top_users(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Get top users by downloads"""
        conn = self.db._conn()
        c = conn.cursor()

        date_from = (datetime.now() - timedelta(days=days)).isoformat()

        c.execute('''
            SELECT d.user_id, u.username, u.first_name, COUNT(*) as downloads
            FROM downloads d
            LEFT JOIN users u ON d.user_id = u.user_id
            WHERE d.timestamp >= ?
            GROUP BY d.user_id
            ORDER BY downloads DESC
            LIMIT ?
        ''', (date_from, limit))

        users = []
        for row in c.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1] or '',
                'name': row[2] or f'User {row[0]}',
                'downloads': row[3]
            })

        conn.close()
        return users

    def export_users_csv(self) -> io.BytesIO:
        """Export all users to CSV"""
        conn = self.db._conn()
        c = conn.cursor()

        c.execute('''
            SELECT user_id, username, first_name, join_date,
                   last_active, total_downloads, is_banned, is_premium
            FROM users
            ORDER BY total_downloads DESC
        ''')

        rows = c.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'User ID', 'Username', 'Name', 'Join Date',
            'Last Active', 'Total Downloads', 'Banned', 'Premium'
        ])

        for row in rows:
            writer.writerow([
                row[0], row[1] or '', row[2] or '', row[3] or '',
                row[4] or '', row[5], 'Yes' if row[6] else 'No',
                'Yes' if row[7] else 'No'
            ])

        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)

        return bytes_output

    def export_downloads_csv(self, days: int = 30) -> io.BytesIO:
        """Export downloads to CSV"""
        conn = self.db._conn()
        c = conn.cursor()

        date_from = (datetime.now() - timedelta(days=days)).isoformat()

        c.execute('''
            SELECT d.id, d.user_id, u.username, d.platform,
                   d.media_type, d.quality, d.title, d.timestamp
            FROM downloads d
            LEFT JOIN users u ON d.user_id = u.user_id
            WHERE d.timestamp >= ?
            ORDER BY d.timestamp DESC
        ''', (date_from,))

        rows = c.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'ID', 'User ID', 'Username', 'Platform',
            'Media Type', 'Quality', 'Title', 'Timestamp'
        ])

        for row in rows:
            writer.writerow(row)

        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)

        return bytes_output

    def generate_report(self) -> str:
        """Generate text report"""
        daily = self.get_daily_stats(7)
        platforms = self.get_platform_breakdown(30)
        top_users = self.get_top_users(5, 30)

        report = "📊 *BOT ANALYTICS REPORT*\n"
        report += "━" * 30 + "\n\n"

        report += "📅 *Last 7 Days:*\n"
        for stat in daily[:7]:
            report += f"  {stat['date']}: {stat['downloads']} downloads, {stat['users']} users\n"

        report += "\n📱 *Platform (30 days):*\n"
        for platform, count in platforms.items():
            report += f"  {platform}: {count}\n"

        report += "\n🏆 *Top Users (30 days):*\n"
        for i, user in enumerate(top_users, 1):
            report += f"  {i}. {user['name']}: {user['downloads']}\n"

        report += "\n" + "━" * 30
        report += f"\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        return report
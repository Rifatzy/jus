import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LevelInfo:
    level: int
    name: str
    badge: str
    xp: int
    next_xp: int
    progress: float


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    badge: str
    xp: int
    unlocked: bool
    unlocked_at: Optional[str] = None


@dataclass
class DailyReward:
    day: int
    coins: int
    xp: int
    bonus: str
    claimed: bool


class Gamification:
    """Gamification system"""

    def __init__(self, db):
        self.db = db
        self._init_tables()

        # Load config
        try:
            from config import Config
            self.levels = Config.LEVELS
            self.achievements_config = Config.ACHIEVEMENTS
            self.xp_per_download = Config.XP_PER_DOWNLOAD
            self.xp_per_referral = Config.XP_PER_REFERRAL
            self.daily_bonus_coins = Config.DAILY_BONUS_COINS
            self.referral_bonus_coins = Config.REFERRAL_BONUS_COINS
        except:
            self.levels = {
                1: {"name": "Newbie", "xp": 0, "badge": "🌱"},
                2: {"name": "Beginner", "xp": 100, "badge": "🌿"},
                3: {"name": "Regular", "xp": 300, "badge": "🌳"},
                4: {"name": "Active", "xp": 600, "badge": "⭐"},
                5: {"name": "Pro", "xp": 1000, "badge": "🌟"},
            }
            self.achievements_config = {}
            self.xp_per_download = 10
            self.xp_per_referral = 100
            self.daily_bonus_coins = 5
            self.referral_bonus_coins = 50

    def _init_tables(self):
        """Initialize gamification tables"""
        conn = self.db._conn()
        c = conn.cursor()

        # User gamification data
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_game (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                streak_days INTEGER DEFAULT 0,
                last_daily TEXT,
                last_active_date TEXT,
                total_referrals INTEGER DEFAULT 0,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                spin_today INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Achievements
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_id TEXT,
                unlocked_at TEXT,
                UNIQUE(user_id, achievement_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Daily rewards history
        c.execute('''
            CREATE TABLE IF NOT EXISTS daily_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day_number INTEGER,
                coins INTEGER,
                xp INTEGER,
                claimed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Leaderboard cache
        c.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard_cache (
                id INTEGER PRIMARY KEY,
                type TEXT,
                data TEXT,
                updated_at TEXT
            )
        ''')

        conn.commit()
        conn.close()

    # ========== XP & LEVEL ==========

    def _ensure_user_game(self, user_id: int):
        """Ensure user has game data"""
        conn = self.db._conn()
        c = conn.cursor()

        c.execute('SELECT user_id FROM user_game WHERE user_id = ?', (user_id,))
        if not c.fetchone():
            ref_code = self._generate_referral_code(user_id)
            c.execute('''
                INSERT INTO user_game (user_id, referral_code)
                VALUES (?, ?)
            ''', (user_id, ref_code))
            conn.commit()

        conn.close()

    def _generate_referral_code(self, user_id: int) -> str:
        """Generate unique referral code"""
        import hashlib
        base = f"{user_id}{datetime.now().timestamp()}"
        hash_code = hashlib.md5(base.encode()).hexdigest()[:8].upper()
        return f"REF{hash_code}"

    def add_xp(self, user_id: int, xp: int, reason: str = "") -> Tuple[int, bool]:
        """Add XP and check for level up. Returns (new_xp, leveled_up)"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()

        c.execute('SELECT xp, level FROM user_game WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        old_xp = row[0]
        old_level = row[1]

        new_xp = old_xp + xp
        new_level = self._calculate_level(new_xp)
        leveled_up = new_level > old_level

        c.execute('''
            UPDATE user_game SET xp = ?, level = ? WHERE user_id = ?
        ''', (new_xp, new_level, user_id))

        conn.commit()
        conn.close()

        return new_xp, leveled_up

    def _calculate_level(self, xp: int) -> int:
        """Calculate level from XP"""
        level = 1
        for lvl, data in sorted(self.levels.items(), reverse=True):
            if xp >= data["xp"]:
                level = lvl
                break
        return level

    def get_level_info(self, user_id: int) -> LevelInfo:
        """Get user's level information"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()

        c.execute('SELECT xp, level FROM user_game WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        xp = row[0]
        level = row[1]

        conn.close()

        level_data = self.levels.get(level, {"name": "Unknown", "badge": "❓", "xp": 0})
        next_level = level + 1
        next_data = self.levels.get(next_level, None)

        if next_data:
            next_xp = next_data["xp"]
            current_level_xp = level_data["xp"]
            progress = (xp - current_level_xp) / (next_xp - current_level_xp) * 100
        else:
            next_xp = level_data["xp"]
            progress = 100

        return LevelInfo(
            level=level,
            name=level_data["name"],
            badge=level_data["badge"],
            xp=xp,
            next_xp=next_xp,
            progress=min(100, progress)
        )

    # ========== COINS ==========

    def add_coins(self, user_id: int, coins: int) -> int:
        """Add coins to user. Returns new balance"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()

        c.execute('''
            UPDATE user_game SET coins = coins + ? WHERE user_id = ?
        ''', (coins, user_id))

        c.execute('SELECT coins FROM user_game WHERE user_id = ?', (user_id,))
        new_coins = c.fetchone()[0]

        conn.commit()
        conn.close()

        return new_coins

    def use_coins(self, user_id: int, coins: int) -> Tuple[bool, int]:
        """Use coins. Returns (success, new_balance)"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()

        c.execute('SELECT coins FROM user_game WHERE user_id = ?', (user_id,))
        current = c.fetchone()[0]

        if current < coins:
            conn.close()
            return False, current

        new_coins = current - coins
        c.execute('UPDATE user_game SET coins = ? WHERE user_id = ?', (new_coins, user_id))

        conn.commit()
        conn.close()

        return True, new_coins

    def get_coins(self, user_id: int) -> int:
        """Get user's coin balance"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()
        c.execute('SELECT coins FROM user_game WHERE user_id = ?', (user_id,))
        coins = c.fetchone()[0]
        conn.close()
        return coins

    # ========== DAILY REWARDS ==========

    def claim_daily(self, user_id: int) -> Tuple[bool, DailyReward]:
        """Claim daily reward. Returns (success, reward)"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()

        today = datetime.now().date().isoformat()

        c.execute('SELECT last_daily, streak_days FROM user_game WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        last_daily = row[0]
        streak = row[1]

        # Check if already claimed today
        if last_daily == today:
            conn.close()
            return False, DailyReward(streak, 0, 0, "", True)

        # Calculate streak
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
        if last_daily == yesterday:
            streak += 1
        else:
            streak = 1

        # Calculate rewards based on streak
        day_in_week = ((streak - 1) % 7) + 1
        base_coins = self.daily_bonus_coins
        base_xp = 5

        # Bonus for streak milestones
        bonus = ""
        if day_in_week == 7:
            coins = base_coins * 3
            xp = base_xp * 3
            bonus = "🎉 Weekly Bonus!"
        elif streak >= 30:
            coins = base_coins * 2
            xp = base_xp * 2
            bonus = "🔥 30 Day Streak!"
        else:
            coins = base_coins + (day_in_week - 1)
            xp = base_xp + (day_in_week - 1) * 2

        # Update user
        c.execute('''
            UPDATE user_game
            SET last_daily = ?, streak_days = ?, coins = coins + ?, xp = xp + ?
            WHERE user_id = ?
        ''', (today, streak, coins, xp, user_id))

        # Record reward
        c.execute('''
            INSERT INTO daily_rewards (user_id, day_number, coins, xp, claimed_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, day_in_week, coins, xp, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return True, DailyReward(day_in_week, coins, xp, bonus, False)

    def get_streak(self, user_id: int) -> int:
        """Get user's current streak"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()
        c.execute('SELECT streak_days, last_daily FROM user_game WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        streak = row[0]
        last_daily = row[1]

        # Check if streak is still valid
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
        today = datetime.now().date().isoformat()

        if last_daily not in [yesterday, today]:
            streak = 0

        conn.close()
        return streak

    # ========== REFERRAL ==========

    def get_referral_code(self, user_id: int) -> str:
        """Get user's referral code"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()
        c.execute('SELECT referral_code FROM user_game WHERE user_id = ?', (user_id,))
        code = c.fetchone()[0]
        conn.close()
        return code

    def apply_referral(self, user_id: int, referral_code: str) -> Tuple[bool, str]:
        """Apply referral code. Returns (success, message)"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()

        # Check if already referred
        c.execute('SELECT referred_by FROM user_game WHERE user_id = ?', (user_id,))
        if c.fetchone()[0]:
            conn.close()
            return False, "Kamu sudah pernah menggunakan referral code"

        # Find referrer
        c.execute('SELECT user_id FROM user_game WHERE referral_code = ?', (referral_code.upper(),))
        result = c.fetchone()

        if not result:
            conn.close()
            return False, "Referral code tidak valid"

        referrer_id = result[0]

        if referrer_id == user_id:
            conn.close()
            return False, "Tidak bisa menggunakan kode sendiri"

        # Apply referral
        c.execute('''
            UPDATE user_game
            SET referred_by = ?, coins = coins + ?
            WHERE user_id = ?
        ''', (referrer_id, self.referral_bonus_coins, user_id))

        # Reward referrer
        c.execute('''
            UPDATE user_game
            SET total_referrals = total_referrals + 1,
                coins = coins + ?,
                xp = xp + ?
            WHERE user_id = ?
        ''', (self.referral_bonus_coins, self.xp_per_referral, referrer_id))

        conn.commit()
        conn.close()

        return True, f"Berhasil! Kamu dapat {self.referral_bonus_coins} coins 🎉"

    def get_referral_count(self, user_id: int) -> int:
        """Get number of referrals"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()
        c.execute('SELECT total_referrals FROM user_game WHERE user_id = ?', (user_id,))
        count = c.fetchone()[0]
        conn.close()
        return count

    # ========== ACHIEVEMENTS ==========

    def check_achievements(self, user_id: int) -> List[Achievement]:
        """Check and unlock new achievements. Returns newly unlocked"""
        self._ensure_user_game(user_id)

        unlocked = []

        # Get user stats
        stats = self.db.get_user_stats(user_id)
        total_downloads = stats.get('total', 0)
        streak = self.get_streak(user_id)
        referrals = self.get_referral_count(user_id)
        is_premium = self.db.is_premium(user_id)
        platforms_used = sum(1 for p in ['tiktok', 'instagram', 'twitter'] if stats.get(p, 0) > 0)

        # Check each achievement
        achievements_to_check = {
            "first_download": total_downloads >= 1,
            "download_10": total_downloads >= 10,
            "download_50": total_downloads >= 50,
            "download_100": total_downloads >= 100,
            "download_500": total_downloads >= 500,
            "streak_7": streak >= 7,
            "streak_30": streak >= 30,
            "referral_1": referrals >= 1,
            "referral_5": referrals >= 5,
            "referral_10": referrals >= 10,
            "premium_member": is_premium,
            "all_platforms": platforms_used >= 3,
        }

        for ach_id, condition in achievements_to_check.items():
            if condition and ach_id in self.achievements_config:
                if self._unlock_achievement(user_id, ach_id):
                    config = self.achievements_config[ach_id]
                    unlocked.append(Achievement(
                        id=ach_id,
                        name=config["name"],
                        description=config["desc"],
                        badge=config["badge"],
                        xp=config["xp"],
                        unlocked=True,
                        unlocked_at=datetime.now().isoformat()
                    ))

        return unlocked

    def _unlock_achievement(self, user_id: int, achievement_id: str) -> bool:
        """Try to unlock achievement. Returns True if newly unlocked"""
        conn = self.db._conn()
        c = conn.cursor()

        # Check if already unlocked
        c.execute('''
            SELECT id FROM user_achievements
            WHERE user_id = ? AND achievement_id = ?
        ''', (user_id, achievement_id))

        if c.fetchone():
            conn.close()
            return False

        # Unlock
        c.execute('''
            INSERT INTO user_achievements (user_id, achievement_id, unlocked_at)
            VALUES (?, ?, ?)
        ''', (user_id, achievement_id, datetime.now().isoformat()))

        # Add XP
        config = self.achievements_config.get(achievement_id, {})
        xp = config.get("xp", 0)
        if xp:
            c.execute('UPDATE user_game SET xp = xp + ? WHERE user_id = ?', (xp, user_id))

        conn.commit()
        conn.close()
        return True

    def get_achievements(self, user_id: int) -> List[Achievement]:
        """Get all achievements with unlock status"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()

        c.execute('''
            SELECT achievement_id, unlocked_at FROM user_achievements WHERE user_id = ?
        ''', (user_id,))

        unlocked_map = {row[0]: row[1] for row in c.fetchall()}
        conn.close()

        achievements = []
        for ach_id, config in self.achievements_config.items():
            achievements.append(Achievement(
                id=ach_id,
                name=config["name"],
                description=config["desc"],
                badge=config["badge"],
                xp=config["xp"],
                unlocked=ach_id in unlocked_map,
                unlocked_at=unlocked_map.get(ach_id)
            ))

        return achievements

    # ========== SPIN WHEEL ==========

    def spin_wheel(self, user_id: int) -> Tuple[bool, str, int]:
        """Spin the wheel. Returns (success, prize_name, prize_value)"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()

        today = datetime.now().date().isoformat()

        c.execute('SELECT spin_today, last_daily FROM user_game WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        spins = row[0]
        last_date = row[1]

        # Reset spins if new day
        if last_date != today:
            spins = 0

        # Check if can spin (1 free spin per day, more for premium)
        max_spins = 3 if self.db.is_premium(user_id) else 1
        if spins >= max_spins:
            conn.close()
            return False, "No spins left", 0

        # Spin!
        prizes = [
            ("🎉 5 Coins", "coins", 5, 30),
            ("🎊 10 Coins", "coins", 10, 25),
            ("⭐ 20 Coins", "coins", 20, 15),
            ("💫 50 Coins", "coins", 50, 5),
            ("🌟 10 XP", "xp", 10, 15),
            ("✨ 25 XP", "xp", 25, 8),
            ("😢 Nothing", "none", 0, 2),
        ]

        # Weighted random
        total_weight = sum(p[3] for p in prizes)
        rand = random.randint(1, total_weight)

        current = 0
        prize = prizes[0]
        for p in prizes:
            current += p[3]
            if rand <= current:
                prize = p
                break

        prize_name, prize_type, prize_value, _ = prize

        # Apply prize
        if prize_type == "coins":
            c.execute('UPDATE user_game SET coins = coins + ? WHERE user_id = ?', (prize_value, user_id))
        elif prize_type == "xp":
            c.execute('UPDATE user_game SET xp = xp + ? WHERE user_id = ?', (prize_value, user_id))

        # Update spin count
        c.execute('UPDATE user_game SET spin_today = ? WHERE user_id = ?', (spins + 1, user_id))

        conn.commit()
        conn.close()

        return True, prize_name, prize_value

    # ========== LEADERBOARD ==========

    def get_leaderboard(self, type: str = "xp", limit: int = 10) -> List[Dict]:
        """Get leaderboard. Types: xp, coins, downloads, streak"""
        conn = self.db._conn()
        c = conn.cursor()

        if type == "xp":
            c.execute('''
                SELECT ug.user_id, u.first_name, u.username, ug.xp, ug.level
                FROM user_game ug
                LEFT JOIN users u ON ug.user_id = u.user_id
                ORDER BY ug.xp DESC
                LIMIT ?
            ''', (limit,))
        elif type == "coins":
            c.execute('''
                SELECT ug.user_id, u.first_name, u.username, ug.coins, ug.level
                FROM user_game ug
                LEFT JOIN users u ON ug.user_id = u.user_id
                ORDER BY ug.coins DESC
                LIMIT ?
            ''', (limit,))
        elif type == "downloads":
            c.execute('''
                SELECT u.user_id, u.first_name, u.username, u.total_downloads, ug.level
                FROM users u
                LEFT JOIN user_game ug ON u.user_id = ug.user_id
                ORDER BY u.total_downloads DESC
                LIMIT ?
            ''', (limit,))
        elif type == "streak":
            c.execute('''
                SELECT ug.user_id, u.first_name, u.username, ug.streak_days, ug.level
                FROM user_game ug
                LEFT JOIN users u ON ug.user_id = u.user_id
                ORDER BY ug.streak_days DESC
                LIMIT ?
            ''', (limit,))
        else:
            conn.close()
            return []

        leaderboard = []
        for i, row in enumerate(c.fetchall(), 1):
            level_data = self.levels.get(row[4] or 1, {"badge": "🌱"})
            leaderboard.append({
                "rank": i,
                "user_id": row[0],
                "name": row[1] or row[2] or f"User {row[0]}",
                "value": row[3] or 0,
                "badge": level_data["badge"]
            })

        conn.close()
        return leaderboard

    def get_user_rank(self, user_id: int, type: str = "xp") -> int:
        """Get user's rank in leaderboard"""
        leaderboard = self.get_leaderboard(type, limit=1000)

        for entry in leaderboard:
            if entry["user_id"] == user_id:
                return entry["rank"]

        return 0

    # ========== GAME STATS ==========

    def get_game_stats(self, user_id: int) -> Dict:
        """Get all game stats for user"""
        self._ensure_user_game(user_id)

        conn = self.db._conn()
        c = conn.cursor()

        c.execute('''
            SELECT xp, coins, level, streak_days, total_referrals, referral_code
            FROM user_game WHERE user_id = ?
        ''', (user_id,))

        row = c.fetchone()
        conn.close()

        level_info = self.get_level_info(user_id)
        achievements = self.get_achievements(user_id)
        unlocked_count = sum(1 for a in achievements if a.unlocked)

        return {
            "xp": row[0],
            "coins": row[1],
            "level": row[2],
            "level_name": level_info.name,
            "level_badge": level_info.badge,
            "level_progress": level_info.progress,
            "next_xp": level_info.next_xp,
            "streak": row[3],
            "referrals": row[4],
            "referral_code": row[5],
            "achievements_unlocked": unlocked_count,
            "achievements_total": len(achievements),
            "xp_rank": self.get_user_rank(user_id, "xp"),
        }
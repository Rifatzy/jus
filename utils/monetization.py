import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import aiohttp


@dataclass
class PaymentPlan:
    id: str
    name: str
    price: int
    duration_days: int
    features: List[str]
    popular: bool = False


@dataclass
class PaymentOrder:
    order_id: str
    user_id: int
    plan_id: str
    amount: int
    status: str  # pending, paid, expired, cancelled
    payment_url: str
    created_at: str
    paid_at: Optional[str] = None


@dataclass
class Transaction:
    id: int
    user_id: int
    type: str  # purchase, coin_buy, premium, refund
    amount: int
    description: str
    status: str
    created_at: str


class Monetization:
    """Monetization and payment system"""

    def __init__(self, db):
        self.db = db
        self._init_tables()

        # Load config
        try:
            from config import Config
            self.server_key = Config.MIDTRANS_SERVER_KEY
            self.client_key = Config.MIDTRANS_CLIENT_KEY
            self.payment_enabled = Config.PAYMENT_ENABLED
            self.price_monthly = Config.PREMIUM_PRICE_MONTHLY
            self.price_yearly = Config.PREMIUM_PRICE_YEARLY
        except:
            self.server_key = ""
            self.client_key = ""
            self.payment_enabled = False
            self.price_monthly = 50000
            self.price_yearly = 500000

        # Define plans
        self.plans = {
            "premium_monthly": PaymentPlan(
                id="premium_monthly",
                name="Premium Monthly",
                price=self.price_monthly,
                duration_days=30,
                features=[
                    "200 downloads/day",
                    "100MB max file size",
                    "Priority download",
                    "No ads",
                    "Premium badge"
                ],
                popular=True
            ),
            "premium_yearly": PaymentPlan(
                id="premium_yearly",
                name="Premium Yearly",
                price=self.price_yearly,
                duration_days=365,
                features=[
                    "200 downloads/day",
                    "100MB max file size",
                    "Priority download",
                    "No ads",
                    "Premium badge",
                    "Save 17%!"
                ]
            ),
            "coins_100": PaymentPlan(
                id="coins_100",
                name="100 Coins",
                price=10000,
                duration_days=0,
                features=["100 coins", "Never expires"]
            ),
            "coins_500": PaymentPlan(
                id="coins_500",
                name="500 Coins + 50 Bonus",
                price=45000,
                duration_days=0,
                features=["550 coins total", "10% bonus", "Never expires"],
                popular=True
            ),
            "coins_1000": PaymentPlan(
                id="coins_1000",
                name="1000 Coins + 200 Bonus",
                price=80000,
                duration_days=0,
                features=["1200 coins total", "20% bonus", "Never expires"]
            ),
        }

        # Promo codes
        self.promo_codes = {}

    def _init_tables(self):
        """Initialize payment tables"""
        conn = self.db._conn()
        c = conn.cursor()

        # Orders table
        c.execute('''
            CREATE TABLE IF NOT EXISTS payment_orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                plan_id TEXT,
                amount INTEGER,
                currency TEXT DEFAULT 'IDR',
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                payment_url TEXT,
                promo_code TEXT,
                discount INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                paid_at TEXT,
                expires_at TEXT,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Transactions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id TEXT,
                type TEXT,
                amount INTEGER,
                balance_before INTEGER,
                balance_after INTEGER,
                description TEXT,
                status TEXT DEFAULT 'success',
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Promo codes table
        c.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                discount_percent INTEGER DEFAULT 0,
                discount_amount INTEGER DEFAULT 0,
                max_uses INTEGER DEFAULT 0,
                used_count INTEGER DEFAULT 0,
                valid_from TEXT,
                valid_until TEXT,
                min_amount INTEGER DEFAULT 0,
                applicable_plans TEXT,
                created_by INTEGER,
                created_at TEXT,
                active INTEGER DEFAULT 1
            )
        ''')

        # Promo code usage
        c.execute('''
            CREATE TABLE IF NOT EXISTS promo_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                user_id INTEGER,
                order_id TEXT,
                used_at TEXT,
                UNIQUE(code, user_id)
            )
        ''')

        conn.commit()
        conn.close()

    # ========== PLANS ==========

    def get_plans(self, plan_type: str = "all") -> List[PaymentPlan]:
        """Get available plans"""
        if plan_type == "premium":
            return [p for p in self.plans.values() if p.id.startswith("premium")]
        elif plan_type == "coins":
            return [p for p in self.plans.values() if p.id.startswith("coins")]
        else:
            return list(self.plans.values())

    def get_plan(self, plan_id: str) -> Optional[PaymentPlan]:
        """Get specific plan"""
        return self.plans.get(plan_id)

    # ========== ORDERS ==========

    def create_order(self, user_id: int, plan_id: str, promo_code: str = "") -> Tuple[bool, str, Optional[PaymentOrder]]:
        """Create payment order. Returns (success, message, order)"""
        plan = self.get_plan(plan_id)
        if not plan:
            return False, "Plan not found", None

        # Calculate amount with promo
        amount = plan.price
        discount = 0

        if promo_code:
            valid, promo_msg, discount = self._validate_promo(promo_code, user_id, amount, plan_id)
            if not valid:
                return False, promo_msg, None
            amount -= discount

        # Generate order ID
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}"

        # Create payment URL (mock for demo, integrate real payment gateway)
        payment_url = self._create_payment_url(order_id, amount, plan.name)

        conn = self.db._conn()
        c = conn.cursor()

        now = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(hours=24)).isoformat()

        c.execute('''
            INSERT INTO payment_orders
            (order_id, user_id, plan_id, amount, status, payment_url, promo_code, discount, created_at, expires_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)
        ''', (order_id, user_id, plan_id, amount, payment_url, promo_code, discount, now, expires))

        conn.commit()
        conn.close()

        order = PaymentOrder(
            order_id=order_id,
            user_id=user_id,
            plan_id=plan_id,
            amount=amount,
            status="pending",
            payment_url=payment_url,
            created_at=now
        )

        return True, "Order created", order

    def _create_payment_url(self, order_id: str, amount: int, item_name: str) -> str:
        """Create payment URL (integrate with payment gateway)"""
        # For demo, return mock URL
        # In production, integrate with Midtrans, Stripe, etc.
        return f"https://payment.example.com/pay/{order_id}"

    def confirm_payment(self, order_id: str) -> Tuple[bool, str]:
        """Confirm payment and activate plan"""
        conn = self.db._conn()
        c = conn.cursor()

        c.execute('''
            SELECT user_id, plan_id, amount, status, promo_code
            FROM payment_orders WHERE order_id = ?
        ''', (order_id,))

        row = c.fetchone()
        if not row:
            conn.close()
            return False, "Order not found"

        user_id, plan_id, amount, status, promo_code = row

        if status == "paid":
            conn.close()
            return False, "Order already paid"

        # Update order status
        now = datetime.now().isoformat()
        c.execute('''
            UPDATE payment_orders SET status = 'paid', paid_at = ?, updated_at = ?
            WHERE order_id = ?
        ''', (now, now, order_id))

        # Activate plan
        plan = self.get_plan(plan_id)
        if plan:
            if plan_id.startswith("premium"):
                self.db.set_premium(user_id, plan.duration_days)
            elif plan_id.startswith("coins"):
                coins = self._get_coins_from_plan(plan_id)
                self._add_coins_to_user(user_id, coins)

        # Record transaction
        c.execute('''
            INSERT INTO transactions
            (user_id, order_id, type, amount, description, status, created_at)
            VALUES (?, ?, 'purchase', ?, ?, 'success', ?)
        ''', (user_id, order_id, amount, f"Purchase: {plan.name if plan else plan_id}", now))

        # Update promo usage
        if promo_code:
            c.execute('''
                INSERT OR IGNORE INTO promo_usage (code, user_id, order_id, used_at)
                VALUES (?, ?, ?, ?)
            ''', (promo_code, user_id, order_id, now))
            c.execute('UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?', (promo_code,))

        conn.commit()
        conn.close()

        return True, "Payment confirmed"

    def _get_coins_from_plan(self, plan_id: str) -> int:
        """Get coins amount from plan"""
        coins_map = {
            "coins_100": 100,
            "coins_500": 550,
            "coins_1000": 1200,
        }
        return coins_map.get(plan_id, 0)

    def _add_coins_to_user(self, user_id: int, coins: int):
        """Add coins to user"""
        conn = self.db._conn()
        c = conn.cursor()
        c.execute('''
            UPDATE user_game SET coins = coins + ? WHERE user_id = ?
        ''', (coins, user_id))
        conn.commit()
        conn.close()

    def get_order(self, order_id: str) -> Optional[PaymentOrder]:
        """Get order by ID"""
        conn = self.db._conn()
        c = conn.cursor()

        c.execute('''
            SELECT order_id, user_id, plan_id, amount, status, payment_url, created_at, paid_at
            FROM payment_orders WHERE order_id = ?
        ''', (order_id,))

        row = c.fetchone()
        conn.close()

        if row:
            return PaymentOrder(
                order_id=row[0],
                user_id=row[1],
                plan_id=row[2],
                amount=row[3],
                status=row[4],
                payment_url=row[5],
                created_at=row[6],
                paid_at=row[7]
            )
        return None

    def get_user_orders(self, user_id: int, limit: int = 10) -> List[PaymentOrder]:
        """Get user's order history"""
        conn = self.db._conn()
        c = conn.cursor()

        c.execute('''
            SELECT order_id, user_id, plan_id, amount, status, payment_url, created_at, paid_at
            FROM payment_orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))

        orders = []
        for row in c.fetchall():
            orders.append(PaymentOrder(
                order_id=row[0],
                user_id=row[1],
                plan_id=row[2],
                amount=row[3],
                status=row[4],
                payment_url=row[5],
                created_at=row[6],
                paid_at=row[7]
            ))

        conn.close()
        return orders

    # ========== PROMO CODES ==========

    def create_promo_code(
        self,
        code: str,
        discount_percent: int = 0,
        discount_amount: int = 0,
        max_uses: int = 0,
        valid_days: int = 30,
        min_amount: int = 0,
        applicable_plans: str = "",
        created_by: int = 0
    ) -> Tuple[bool, str]:
        """Create promo code"""
        conn = self.db._conn()
        c = conn.cursor()

        code = code.upper()

        # Check if exists
        c.execute('SELECT code FROM promo_codes WHERE code = ?', (code,))
        if c.fetchone():
            conn.close()
            return False, "Promo code already exists"

        now = datetime.now()
        valid_until = (now + timedelta(days=valid_days)).isoformat()

        c.execute('''
            INSERT INTO promo_codes
            (code, discount_percent, discount_amount, max_uses, valid_from, valid_until,
             min_amount, applicable_plans, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, discount_percent, discount_amount, max_uses, now.isoformat(),
              valid_until, min_amount, applicable_plans, created_by, now.isoformat()))

        conn.commit()
        conn.close()

        return True, f"Promo code {code} created"

    def _validate_promo(self, code: str, user_id: int, amount: int, plan_id: str) -> Tuple[bool, str, int]:
        """Validate promo code. Returns (valid, message, discount)"""
        conn = self.db._conn()
        c = conn.cursor()

        code = code.upper()

        c.execute('''
            SELECT discount_percent, discount_amount, max_uses, used_count,
                   valid_from, valid_until, min_amount, applicable_plans, active
            FROM promo_codes WHERE code = ?
        ''', (code,))

        row = c.fetchone()
        if not row:
            conn.close()
            return False, "Invalid promo code", 0

        (discount_pct, discount_amt, max_uses, used_count,
         valid_from, valid_until, min_amount, applicable_plans, active) = row

        if not active:
            conn.close()
            return False, "Promo code is inactive", 0

        # Check validity period
        now = datetime.now().isoformat()
        if now < valid_from or now > valid_until:
            conn.close()
            return False, "Promo code has expired", 0

        # Check max uses
        if max_uses > 0 and used_count >= max_uses:
            conn.close()
            return False, "Promo code has reached max uses", 0

        # Check if user already used
        c.execute('SELECT id FROM promo_usage WHERE code = ? AND user_id = ?', (code, user_id))
        if c.fetchone():
            conn.close()
            return False, "You already used this promo code", 0

        # Check minimum amount
        if amount < min_amount:
            conn.close()
            return False, f"Minimum purchase is Rp {min_amount:,}", 0

        # Check applicable plans
        if applicable_plans and plan_id not in applicable_plans:
            conn.close()
            return False, "Promo code not applicable for this plan", 0

        # Calculate discount
        if discount_pct > 0:
            discount = int(amount * discount_pct / 100)
        else:
            discount = discount_amt

        conn.close()
        return True, "Promo code applied", discount

    def check_promo(self, code: str, user_id: int, amount: int, plan_id: str) -> Tuple[bool, str, int]:
        """Public method to check promo code"""
        return self._validate_promo(code, user_id, amount, plan_id)

    # ========== TRANSACTIONS ==========

    def get_transactions(self, user_id: int, limit: int = 20) -> List[Transaction]:
        """Get user's transaction history"""
        conn = self.db._conn()
        c = conn.cursor()

        c.execute('''
            SELECT id, user_id, type, amount, description, status, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))

        transactions = []
        for row in c.fetchall():
            transactions.append(Transaction(
                id=row[0],
                user_id=row[1],
                type=row[2],
                amount=row[3],
                description=row[4],
                status=row[5],
                created_at=row[6]
            ))

        conn.close()
        return transactions

    # ========== COINS SHOP ==========

    def buy_with_coins(self, user_id: int, item_id: str) -> Tuple[bool, str]:
        """Buy items with coins"""
        # Define shop items
        shop_items = {
            "extra_download_10": {"name": "+10 Downloads Today", "price": 20, "type": "download_limit"},
            "extra_download_50": {"name": "+50 Downloads Today", "price": 80, "type": "download_limit"},
            "premium_1day": {"name": "Premium 1 Day", "price": 50, "type": "premium", "days": 1},
            "premium_3day": {"name": "Premium 3 Days", "price": 120, "type": "premium", "days": 3},
            "premium_7day": {"name": "Premium 7 Days", "price": 250, "type": "premium", "days": 7},
            "spin_ticket": {"name": "Extra Spin", "price": 30, "type": "spin"},
        }

        item = shop_items.get(item_id)
        if not item:
            return False, "Item not found"

        # Check coins
        conn = self.db._conn()
        c = conn.cursor()

        c.execute('SELECT coins FROM user_game WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return False, "User not found"

        coins = row[0]
        price = item["price"]

        if coins < price:
            conn.close()
            return False, f"Not enough coins. Need {price}, have {coins}"

        # Deduct coins
        c.execute('UPDATE user_game SET coins = coins - ? WHERE user_id = ?', (price, user_id))

        # Apply item
        if item["type"] == "premium":
            self.db.set_premium(user_id, item["days"])
        elif item["type"] == "spin":
            c.execute('UPDATE user_game SET spin_today = spin_today - 1 WHERE user_id = ?', (user_id,))
        # download_limit would need custom implementation

        # Record transaction
        c.execute('''
            INSERT INTO transactions
            (user_id, type, amount, description, status, created_at)
            VALUES (?, 'coin_purchase', ?, ?, 'success', ?)
        ''', (user_id, -price, f"Bought: {item['name']}", datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return True, f"Successfully purchased {item['name']}!"

    def get_shop_items(self) -> List[Dict]:
        """Get available shop items"""
        return [
            {"id": "extra_download_10", "name": "+10 Downloads Today", "price": 20, "icon": "📥"},
            {"id": "extra_download_50", "name": "+50 Downloads Today", "price": 80, "icon": "📦"},
            {"id": "premium_1day", "name": "Premium 1 Day", "price": 50, "icon": "⭐"},
            {"id": "premium_3day", "name": "Premium 3 Days", "price": 120, "icon": "🌟"},
            {"id": "premium_7day", "name": "Premium 7 Days", "price": 250, "icon": "💫"},
            {"id": "spin_ticket", "name": "Extra Spin", "price": 30, "icon": "🎰"},
        ]

    # ========== REVENUE STATS (Admin) ==========

    def get_revenue_stats(self, days: int = 30) -> Dict:
        """Get revenue statistics"""
        conn = self.db._conn()
        c = conn.cursor()

        date_from = (datetime.now() - timedelta(days=days)).isoformat()

        # Total revenue
        c.execute('''
            SELECT SUM(amount) FROM payment_orders
            WHERE status = 'paid' AND paid_at >= ?
        ''', (date_from,))
        total = c.fetchone()[0] or 0

        # Revenue by plan
        c.execute('''
            SELECT plan_id, COUNT(*), SUM(amount)
            FROM payment_orders
            WHERE status = 'paid' AND paid_at >= ?
            GROUP BY plan_id
        ''', (date_from,))
        by_plan = {row[0]: {"count": row[1], "amount": row[2]} for row in c.fetchall()}

        # Daily revenue
        c.execute('''
            SELECT DATE(paid_at), SUM(amount)
            FROM payment_orders
            WHERE status = 'paid' AND paid_at >= ?
            GROUP BY DATE(paid_at)
            ORDER BY DATE(paid_at) DESC
        ''', (date_from,))
        daily = [{"date": row[0], "amount": row[1]} for row in c.fetchall()]

        # Total orders
        c.execute('SELECT COUNT(*) FROM payment_orders WHERE status = "paid" AND paid_at >= ?', (date_from,))
        total_orders = c.fetchone()[0]

        conn.close()

        return {
            "total_revenue": total,
            "total_orders": total_orders,
            "by_plan": by_plan,
            "daily": daily[:7],  # Last 7 days
            "period_days": days
        }
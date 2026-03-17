# ============================================================
#  ICA PMS — Database Manager
#  SQLite with 15+ indexes, full schema
# ============================================================

import sqlite3
import hashlib
import os
import datetime
import sys

def get_db_path():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "ica_pms.db")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class DatabaseManager:
    def __init__(self):
        self.db_path = get_db_path()
        self.conn = None
        self.connect()
        self.create_schema()
        self.seed_admin()

    # ── Connection ───────────────────────────────────────────
    def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA cache_size=-64000")   # 64 MB cache
        self.conn.execute("PRAGMA temp_store=MEMORY")
        self.conn.execute("PRAGMA mmap_size=268435456") # 256 MB memory map
        self.conn.execute("PRAGMA synchronous=NORMAL")  # faster writes, safe with WAL

    def get_conn(self):
        try:
            self.conn.execute("SELECT 1")
        except Exception:
            self.connect()
        return self.conn

    # ── Schema ───────────────────────────────────────────────
    def create_schema(self):
        c = self.get_conn()
        c.executescript("""
        -- Users
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            full_name   TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'Store Keeper',
            email       TEXT,
            phone       TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            last_login  TEXT
        );

        -- Categories
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Suppliers
        CREATE TABLE IF NOT EXISTS suppliers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            contact     TEXT,
            phone       TEXT,
            email       TEXT,
            address     TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Products
        CREATE TABLE IF NOT EXISTS products (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sku             TEXT UNIQUE NOT NULL,
            barcode         TEXT,
            name            TEXT NOT NULL,
            description     TEXT,
            category_id     INTEGER REFERENCES categories(id),
            supplier_id     INTEGER REFERENCES suppliers(id),
            cost_price      REAL NOT NULL DEFAULT 0,
            selling_price   REAL NOT NULL DEFAULT 0,
            quantity        INTEGER NOT NULL DEFAULT 0,
            min_stock       INTEGER NOT NULL DEFAULT 10,
            unit            TEXT DEFAULT 'pcs',
            image_path      TEXT,
            batch_no        TEXT,
            expiry_date     TEXT,
            is_active       INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Stock Transactions
        CREATE TABLE IF NOT EXISTS stock_transactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id      INTEGER NOT NULL REFERENCES products(id),
            transaction_type TEXT NOT NULL,   -- 'IN','OUT','RETURN','ADJUSTMENT'
            quantity        INTEGER NOT NULL,
            previous_qty    INTEGER NOT NULL DEFAULT 0,
            new_qty         INTEGER NOT NULL DEFAULT 0,
            unit_price      REAL DEFAULT 0,
            total_value     REAL DEFAULT 0,
            reference_no    TEXT,
            notes           TEXT,
            user_id         INTEGER REFERENCES users(id),
            buyer_id        INTEGER REFERENCES buyers(id),
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Sales
        CREATE TABLE IF NOT EXISTS sales (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no      TEXT UNIQUE NOT NULL,
            customer_name   TEXT,
            customer_phone  TEXT,
            customer_address TEXT,
            total_amount    REAL NOT NULL DEFAULT 0,
            discount        REAL DEFAULT 0,
            gst_rate        REAL DEFAULT 0,
            gst_amount      REAL DEFAULT 0,
            net_amount      REAL NOT NULL DEFAULT 0,
            payment_method  TEXT DEFAULT 'Cash',
            user_id         INTEGER REFERENCES users(id),
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Sale Items
        CREATE TABLE IF NOT EXISTS sale_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id         INTEGER NOT NULL REFERENCES sales(id),
            product_id      INTEGER NOT NULL REFERENCES products(id),
            quantity        INTEGER NOT NULL,
            unit_price      REAL NOT NULL,
            total_price     REAL NOT NULL
        );

        -- Audit Log
        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            username    TEXT,
            action      TEXT NOT NULL,
            module      TEXT,
            details     TEXT,
            ip_address  TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Login History
        CREATE TABLE IF NOT EXISTS login_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            username    TEXT,
            status      TEXT,   -- 'SUCCESS', 'FAILED'
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Buyers / Customers
        CREATE TABLE IF NOT EXISTS buyers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            contact     TEXT,
            phone       TEXT,
            email       TEXT,
            address     TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_buyers_name ON buyers(name);

        -- App Settings
        CREATE TABLE IF NOT EXISTS settings (
            key     TEXT PRIMARY KEY,
            value   TEXT
        );

        -- ── Indexes (15+) ──────────────────────────────────
        CREATE INDEX IF NOT EXISTS idx_products_sku       ON products(sku);
        CREATE INDEX IF NOT EXISTS idx_products_barcode   ON products(barcode);
        CREATE INDEX IF NOT EXISTS idx_products_name      ON products(name);
        CREATE INDEX IF NOT EXISTS idx_products_category  ON products(category_id);
        CREATE INDEX IF NOT EXISTS idx_products_supplier  ON products(supplier_id);
        CREATE INDEX IF NOT EXISTS idx_products_quantity  ON products(quantity);
        CREATE INDEX IF NOT EXISTS idx_products_active    ON products(is_active);
        CREATE INDEX IF NOT EXISTS idx_stock_product      ON stock_transactions(product_id);
        CREATE INDEX IF NOT EXISTS idx_stock_type         ON stock_transactions(transaction_type);
        CREATE INDEX IF NOT EXISTS idx_stock_date         ON stock_transactions(created_at);
        CREATE INDEX IF NOT EXISTS idx_stock_user         ON stock_transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sales_date         ON sales(created_at);
        CREATE INDEX IF NOT EXISTS idx_sales_invoice      ON sales(invoice_no);
        CREATE INDEX IF NOT EXISTS idx_sale_items_sale    ON sale_items(sale_id);
        CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id);
        CREATE INDEX IF NOT EXISTS idx_audit_user         ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_module       ON audit_log(module);
        CREATE INDEX IF NOT EXISTS idx_audit_date         ON audit_log(created_at);
        CREATE INDEX IF NOT EXISTS idx_login_user         ON login_history(user_id);
        """)
        c.commit()

    # ── Seed default admin ────────────────────────────────────
    def seed_admin(self):
        c = self.get_conn()
        existing = c.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not existing:
            c.execute("""
                INSERT INTO users (username, password, full_name, role, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, ('admin', hash_password('admin123'), 'System Administrator', 'Admin'))
            c.commit()
        # Default settings
        defaults = [
            ('business_name', 'ICA – Integrating Consulting & Automation'),
            ('support_phone', '9967969850'),
            ('currency', '₹'),
            ('low_stock_threshold', '10'),
            ('install_date', datetime.date.today().isoformat()),
        ]
        for k, v in defaults:
            c.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (k, v))
        c.commit()

    # ─────────────────────────────────────────────────────────
    #  AUTH
    # ─────────────────────────────────────────────────────────
    def authenticate(self, username, password):
        c = self.get_conn()
        user = c.execute(
            "SELECT * FROM users WHERE username=? AND is_active=1", (username,)
        ).fetchone()
        if user and user['password'] == hash_password(password):
            c.execute("UPDATE users SET last_login=datetime('now','localtime') WHERE id=?", (user['id'],))
            c.execute("INSERT INTO login_history (user_id, username, status) VALUES (?,?,?)",
                      (user['id'], username, 'SUCCESS'))
            c.commit()
            return dict(user)
        else:
            c.execute("INSERT INTO login_history (user_id, username, status) VALUES (?,?,?)",
                      (None, username, 'FAILED'))
            c.commit()
            return None

    def reset_password(self, user_id, new_password):
        c = self.get_conn()
        c.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_password), user_id))
        c.commit()

    # ─────────────────────────────────────────────────────────
    #  USERS
    # ─────────────────────────────────────────────────────────
    def get_all_users(self):
        return [dict(r) for r in self.get_conn().execute(
            "SELECT * FROM users ORDER BY full_name").fetchall()]

    def get_user(self, user_id):
        r = self.get_conn().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(r) if r else None

    def create_user(self, username, password, full_name, role, email='', phone=''):
        c = self.get_conn()
        c.execute("""
            INSERT INTO users (username, password, full_name, role, email, phone)
            VALUES (?,?,?,?,?,?)
        """, (username, hash_password(password), full_name, role, email, phone))
        c.commit()

    def update_user(self, user_id, full_name, role, email, phone, is_active):
        c = self.get_conn()
        c.execute("""
            UPDATE users SET full_name=?, role=?, email=?, phone=?, is_active=?
            WHERE id=?
        """, (full_name, role, email, phone, is_active, user_id))
        c.commit()

    def delete_user(self, user_id):
        c = self.get_conn()
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        c.commit()

    def get_login_history(self, limit=200):
        return [dict(r) for r in self.get_conn().execute("""
            SELECT lh.*, u.full_name FROM login_history lh
            LEFT JOIN users u ON lh.user_id = u.id
            ORDER BY lh.created_at DESC LIMIT ?
        """, (limit,)).fetchall()]

    # ─────────────────────────────────────────────────────────
    #  CATEGORIES
    # ─────────────────────────────────────────────────────────
    def get_categories(self):
        return [dict(r) for r in self.get_conn().execute(
            "SELECT * FROM categories ORDER BY name").fetchall()]

    def add_category(self, name, desc=''):
        c = self.get_conn()
        c.execute("INSERT INTO categories (name, description) VALUES (?,?)", (name, desc))
        c.commit()

    def delete_category(self, cat_id):
        c = self.get_conn()
        c.execute("DELETE FROM categories WHERE id=?", (cat_id,))
        c.commit()

    # ─────────────────────────────────────────────────────────
    #  SUPPLIERS
    # ─────────────────────────────────────────────────────────
    def get_suppliers(self):
        return [dict(r) for r in self.get_conn().execute(
            "SELECT * FROM suppliers WHERE is_active=1 ORDER BY name").fetchall()]

    def add_supplier(self, name, contact='', phone='', email='', address=''):
        c = self.get_conn()
        c.execute("""
            INSERT INTO suppliers (name, contact, phone, email, address)
            VALUES (?,?,?,?,?)
        """, (name, contact, phone, email, address))
        c.commit()

    def update_supplier(self, sup_id, name, contact, phone, email, address):
        c = self.get_conn()
        c.execute("""
            UPDATE suppliers SET name=?, contact=?, phone=?, email=?, address=?
            WHERE id=?
        """, (name, contact, phone, email, address, sup_id))
        c.commit()

    def delete_supplier(self, sup_id):
        c = self.get_conn()
        c.execute("UPDATE suppliers SET is_active=0 WHERE id=?", (sup_id,))
        c.commit()

    # ─────────────────────────────────────────────────────────
    #  BUYERS / CUSTOMERS
    # ─────────────────────────────────────────────────────────
    def get_buyers(self):
        return [dict(r) for r in self.get_conn().execute(
            "SELECT * FROM buyers WHERE is_active=1 ORDER BY name").fetchall()]

    def add_buyer(self, name, contact='', phone='', email='', address=''):
        c = self.get_conn()
        c.execute("""
            INSERT INTO buyers (name, contact, phone, email, address)
            VALUES (?,?,?,?,?)
        """, (name, contact, phone, email, address))
        c.commit()

    def update_buyer(self, buyer_id, name, contact, phone, email, address):
        c = self.get_conn()
        c.execute("""
            UPDATE buyers SET name=?, contact=?, phone=?, email=?, address=?
            WHERE id=?
        """, (name, contact, phone, email, address, buyer_id))
        c.commit()

    def delete_buyer(self, buyer_id):
        c = self.get_conn()
        c.execute("UPDATE buyers SET is_active=0 WHERE id=?", (buyer_id,))
        c.commit()

    # ─────────────────────────────────────────────────────────
    #  PRODUCTS
    # ─────────────────────────────────────────────────────────
    def get_products(self, search='', category_id=None, low_stock_only=False,
                     limit=500, offset=0):
        query = """
            SELECT p.*, c.name as category_name, s.name as supplier_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.is_active=1
        """
        params = []
        if search:
            query += " AND (p.name LIKE ? OR p.sku LIKE ? OR p.barcode LIKE ?)"
            params += [f'%{search}%', f'%{search}%', f'%{search}%']
        if category_id:
            query += " AND p.category_id=?"
            params.append(category_id)
        if low_stock_only:
            query += " AND p.quantity <= p.min_stock"
        query += " ORDER BY p.name"
        query += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        return [dict(r) for r in self.get_conn().execute(query, params).fetchall()]

    def count_products(self, search='', category_id=None, low_stock_only=False):
        query = """
            SELECT COUNT(*) FROM products p WHERE p.is_active=1
        """
        params = []
        if search:
            query += " AND (p.name LIKE ? OR p.sku LIKE ? OR p.barcode LIKE ?)"
            params += [f'%{search}%', f'%{search}%', f'%{search}%']
        if category_id:
            query += " AND p.category_id=?"
            params.append(category_id)
        if low_stock_only:
            query += " AND p.quantity <= p.min_stock"
        return self.get_conn().execute(query, params).fetchone()[0]

    def get_product(self, product_id):
        r = self.get_conn().execute("""
            SELECT p.*, c.name as category_name, s.name as supplier_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id=?
        """, (product_id,)).fetchone()
        return dict(r) if r else None

    def get_product_by_sku(self, sku):
        r = self.get_conn().execute("SELECT * FROM products WHERE sku=? AND is_active=1", (sku,)).fetchone()
        return dict(r) if r else None

    def add_product(self, data: dict):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO products (sku, barcode, name, description, category_id, supplier_id,
                cost_price, selling_price, quantity, min_stock, unit, batch_no, expiry_date)
            VALUES (:sku, :barcode, :name, :description, :category_id, :supplier_id,
                :cost_price, :selling_price, :quantity, :min_stock, :unit, :batch_no, :expiry_date)
        """, data)
        conn.commit()
        return cur.lastrowid

    def update_product(self, product_id, data: dict):
        data['id'] = product_id
        data['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c = self.get_conn()
        c.execute("""
            UPDATE products SET sku=:sku, barcode=:barcode, name=:name, description=:description,
                category_id=:category_id, supplier_id=:supplier_id, cost_price=:cost_price,
                selling_price=:selling_price, min_stock=:min_stock, unit=:unit,
                batch_no=:batch_no, expiry_date=:expiry_date, updated_at=:updated_at
            WHERE id=:id
        """, data)
        c.commit()

    def delete_product(self, product_id):
        c = self.get_conn()
        c.execute("UPDATE products SET is_active=0 WHERE id=?", (product_id,))
        c.commit()

    def get_product_count(self):
        return self.get_conn().execute("SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0]

    def get_low_stock_count(self):
        return self.get_conn().execute(
            "SELECT COUNT(*) FROM products WHERE is_active=1 AND quantity <= min_stock").fetchone()[0]

    # ─────────────────────────────────────────────────────────
    #  STOCK TRANSACTIONS
    # ─────────────────────────────────────────────────────────
    def stock_in(self, product_id, quantity, unit_price, reference_no, notes, user_id):
        c = self.get_conn()
        prod = c.execute("SELECT quantity FROM products WHERE id=?", (product_id,)).fetchone()
        prev_qty = prod['quantity']
        new_qty = prev_qty + quantity
        c.execute("UPDATE products SET quantity=?, updated_at=datetime('now','localtime') WHERE id=?",
                  (new_qty, product_id))
        c.execute("""
            INSERT INTO stock_transactions
                (product_id, transaction_type, quantity, previous_qty, new_qty,
                 unit_price, total_value, reference_no, notes, user_id)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (product_id, 'IN', quantity, prev_qty, new_qty,
              unit_price, quantity * unit_price, reference_no, notes, user_id))
        c.commit()

    def stock_out(self, product_id, quantity, unit_price, reference_no, notes, user_id, buyer_id=None):
        c = self.get_conn()
        prod = c.execute("SELECT quantity FROM products WHERE id=?", (product_id,)).fetchone()
        prev_qty = prod['quantity']
        new_qty = max(0, prev_qty - quantity)
        c.execute("UPDATE products SET quantity=?, updated_at=datetime('now','localtime') WHERE id=?",
                  (new_qty, product_id))
        c.execute("""
            INSERT INTO stock_transactions
                (product_id, transaction_type, quantity, previous_qty, new_qty,
                 unit_price, total_value, reference_no, notes, user_id, buyer_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (product_id, 'OUT', quantity, prev_qty, new_qty,
              unit_price, quantity * unit_price, reference_no, notes, user_id, buyer_id))
        c.commit()

    def stock_adjust(self, product_id, new_quantity, notes, user_id):
        c = self.get_conn()
        prod = c.execute("SELECT quantity FROM products WHERE id=?", (product_id,)).fetchone()
        prev_qty = prod['quantity']
        c.execute("UPDATE products SET quantity=?, updated_at=datetime('now','localtime') WHERE id=?",
                  (new_quantity, product_id))
        c.execute("""
            INSERT INTO stock_transactions
                (product_id, transaction_type, quantity, previous_qty, new_qty, notes, user_id)
            VALUES (?,?,?,?,?,?,?)
        """, (product_id, 'ADJUSTMENT', new_quantity - prev_qty, prev_qty, new_quantity, notes, user_id))
        c.commit()

    def get_stock_transactions(self, product_id=None, tx_type=None, date_from=None, date_to=None, limit=500):
        query = """
            SELECT st.*, p.name as product_name, p.sku, u.full_name as user_name,
                   b.name as buyer_name
            FROM stock_transactions st
            LEFT JOIN products p ON st.product_id = p.id
            LEFT JOIN users u ON st.user_id = u.id
            LEFT JOIN buyers b ON st.buyer_id = b.id
            WHERE 1=1
        """
        params = []
        if product_id:
            query += " AND st.product_id=?"; params.append(product_id)
        if tx_type:
            query += " AND st.transaction_type=?"; params.append(tx_type)
        if date_from:
            query += " AND DATE(st.created_at)>=?"; params.append(date_from)
        if date_to:
            query += " AND DATE(st.created_at)<=?"; params.append(date_to)
        query += f" ORDER BY st.created_at DESC LIMIT {limit}"
        return [dict(r) for r in self.get_conn().execute(query, params).fetchall()]

    # ─────────────────────────────────────────────────────────
    #  SALES
    # ─────────────────────────────────────────────────────────
    def _migrate_sales_gst(self):
        """Add GST columns to existing databases."""
        conn = self.get_conn()
        cols = [r[1] for r in conn.execute("PRAGMA table_info(sales)").fetchall()]
        for col, default in [('gst_rate','0'), ('gst_amount','0'),
                              ('customer_phone','""'), ('customer_address','""')]:
            if col not in cols:
                try:
                    conn.execute(f"ALTER TABLE sales ADD COLUMN {col} REAL DEFAULT {default}")
                    conn.commit()
                except Exception:
                    pass

    def create_sale(self, customer_name, items, discount, payment_method, notes,
                    user_id, gst_rate=0, customer_phone='', customer_address=''):
        self._migrate_sales_gst()
        conn = self.get_conn()
        cur  = conn.cursor()
        invoice_no  = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        subtotal    = sum(i['qty'] * i['unit_price'] for i in items)
        after_disc  = subtotal - discount
        gst_amount  = round(after_disc * gst_rate / 100, 2)
        net         = round(after_disc + gst_amount, 2)
        cur.execute("""
            INSERT INTO sales (invoice_no, customer_name, customer_phone, customer_address,
                total_amount, discount, gst_rate, gst_amount, net_amount,
                payment_method, user_id, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (invoice_no, customer_name, customer_phone, customer_address,
              subtotal, discount, gst_rate, gst_amount, net,
              payment_method, user_id, notes))
        sale_id = cur.lastrowid
        for item in items:
            conn.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
                VALUES (?,?,?,?,?)
            """, (sale_id, item['product_id'], item['qty'],
                  item['unit_price'], item['qty'] * item['unit_price']))
            self.stock_out(item['product_id'], item['qty'], item['unit_price'],
                           invoice_no, f"Sale {invoice_no}", user_id, None)
        conn.commit()
        return invoice_no

    def get_sales(self, date_from=None, date_to=None, limit=500):
        query = """
            SELECT s.*, u.full_name as user_name
            FROM sales s LEFT JOIN users u ON s.user_id = u.id
            WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND DATE(s.created_at)>=?"; params.append(date_from)
        if date_to:
            query += " AND DATE(s.created_at)<=?"; params.append(date_to)
        query += " ORDER BY s.created_at DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.get_conn().execute(query, params).fetchall()]

    def get_sale_items(self, sale_id):
        return [dict(r) for r in self.get_conn().execute("""
            SELECT si.*, p.name as product_name, p.sku
            FROM sale_items si LEFT JOIN products p ON si.product_id = p.id
            WHERE si.sale_id=?
        """, (sale_id,)).fetchall()]

    # ─────────────────────────────────────────────────────────
    #  DASHBOARD STATS
    # ─────────────────────────────────────────────────────────
    def get_dashboard_stats(self):
        c = self.get_conn()
        stats = {}
        stats['total_products'] = c.execute(
            "SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0]
        stats['total_categories'] = c.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        stats['total_suppliers'] = c.execute(
            "SELECT COUNT(*) FROM suppliers WHERE is_active=1").fetchone()[0]
        stats['low_stock'] = c.execute(
            "SELECT COUNT(*) FROM products WHERE is_active=1 AND quantity<=min_stock").fetchone()[0]
        stats['out_of_stock'] = c.execute(
            "SELECT COUNT(*) FROM products WHERE is_active=1 AND quantity=0").fetchone()[0]
        stats['total_stock_value'] = c.execute(
            "SELECT COALESCE(SUM(quantity*cost_price),0) FROM products WHERE is_active=1").fetchone()[0]

        today = datetime.date.today().isoformat()
        week_start = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        month_start = datetime.date.today().replace(day=1).isoformat()

        stats['sales_today'] = c.execute(
            "SELECT COALESCE(SUM(net_amount),0) FROM sales WHERE DATE(created_at)=?", (today,)).fetchone()[0]
        stats['sales_week'] = c.execute(
            "SELECT COALESCE(SUM(net_amount),0) FROM sales WHERE DATE(created_at)>=?", (week_start,)).fetchone()[0]
        stats['sales_month'] = c.execute(
            "SELECT COALESCE(SUM(net_amount),0) FROM sales WHERE DATE(created_at)>=?", (month_start,)).fetchone()[0]
        stats['total_users'] = c.execute("SELECT COUNT(*) FROM users WHERE is_active=1").fetchone()[0]
        return stats

    def get_monthly_sales(self):
        return [dict(r) for r in self.get_conn().execute("""
            SELECT strftime('%Y-%m', created_at) as month,
                   COALESCE(SUM(net_amount),0) as total,
                   COUNT(*) as count
            FROM sales
            WHERE created_at >= date('now','-12 months')
            GROUP BY month ORDER BY month
        """).fetchall()]

    def get_category_stock(self):
        return [dict(r) for r in self.get_conn().execute("""
            SELECT c.name, COALESCE(SUM(p.quantity),0) as total_qty,
                   COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON p.category_id = c.id AND p.is_active=1
            GROUP BY c.id, c.name ORDER BY total_qty DESC
        """).fetchall()]

    def get_fast_moving(self, limit=10):
        return [dict(r) for r in self.get_conn().execute("""
            SELECT p.name, p.sku, COALESCE(SUM(si.quantity),0) as sold_qty
            FROM products p
            LEFT JOIN sale_items si ON si.product_id = p.id
            LEFT JOIN sales s ON si.sale_id = s.id
            WHERE s.created_at >= date('now','-30 days') OR s.created_at IS NULL
            GROUP BY p.id ORDER BY sold_qty DESC LIMIT ?
        """, (limit,)).fetchall()]

    def get_stock_value_trend(self):
        return [dict(r) for r in self.get_conn().execute("""
            SELECT DATE(created_at) as date,
                   SUM(CASE WHEN transaction_type='IN' THEN total_value ELSE -total_value END) as net_value
            FROM stock_transactions
            WHERE created_at >= date('now','-30 days')
            GROUP BY DATE(created_at) ORDER BY date
        """).fetchall()]

    # ─────────────────────────────────────────────────────────
    #  AUDIT LOG
    # ─────────────────────────────────────────────────────────
    def log_action(self, user_id, username, action, module='', details=''):
        self.get_conn().execute("""
            INSERT INTO audit_log (user_id, username, action, module, details)
            VALUES (?,?,?,?,?)
        """, (user_id, username, action, module, details))
        self.get_conn().commit()

    def get_audit_log(self, limit=500):
        return [dict(r) for r in self.get_conn().execute("""
            SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()]

    # ─────────────────────────────────────────────────────────
    #  SETTINGS
    # ─────────────────────────────────────────────────────────
    def get_setting(self, key, default=''):
        r = self.get_conn().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r['value'] if r else default

    def set_setting(self, key, value):
        c = self.get_conn()
        c.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
        c.commit()

    # ─────────────────────────────────────────────────────────
    #  BACKUP / RESTORE
    # ─────────────────────────────────────────────────────────
    def backup_database(self, backup_path):
        import shutil
        shutil.copy2(self.db_path, backup_path)

    def restore_database(self, backup_path):
        import shutil
        self.conn.close()
        shutil.copy2(backup_path, self.db_path)
        self.connect()

    # ─────────────────────────────────────────────────────────
    #  REPORTS DATA
    # ─────────────────────────────────────────────────────────
    def get_inventory_report(self):
        return [dict(r) for r in self.get_conn().execute("""
            SELECT p.sku, p.name, c.name as category, s.name as supplier,
                   p.quantity, p.min_stock, p.cost_price, p.selling_price,
                   (p.quantity * p.cost_price) as stock_value,
                   CASE WHEN p.quantity=0 THEN 'Out of Stock'
                        WHEN p.quantity<=p.min_stock THEN 'Low Stock'
                        ELSE 'In Stock' END as status
            FROM products p
            LEFT JOIN categories c ON p.category_id=c.id
            LEFT JOIN suppliers s ON p.supplier_id=s.id
            WHERE p.is_active=1 ORDER BY p.name
        """).fetchall()]

    def get_supplier_report(self):
        return [dict(r) for r in self.get_conn().execute("""
            SELECT s.name as supplier, COUNT(p.id) as product_count,
                   COALESCE(SUM(p.quantity),0) as total_qty,
                   COALESCE(SUM(p.quantity*p.cost_price),0) as stock_value
            FROM suppliers s
            LEFT JOIN products p ON p.supplier_id=s.id AND p.is_active=1
            WHERE s.is_active=1 GROUP BY s.id ORDER BY stock_value DESC
        """).fetchall()]

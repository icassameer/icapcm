#!/usr/bin/env python3
import os
import sqlite3
import random
import string
from datetime import datetime, timedelta

DB_PATH = "ica_pms.db"

CATEGORY_COUNT = 100
SUPPLIER_COUNT = 500
PRODUCT_COUNT = 10000
CUSTOMER_COUNT = 3000
USER_COUNT = 20
STOCK_TX_COUNT = 50000
SALES_COUNT = 5000
MAX_ITEMS_PER_SALE = 5

random.seed(42)


def rand_text(prefix="", length=6):
    chars = string.ascii_uppercase + string.digits
    return f"{prefix}{''.join(random.choices(chars, k=length))}"


def rand_phone():
    return "9" + "".join(random.choices(string.digits, k=9))


def rand_email(name):
    safe = "".join(c.lower() for c in name if c.isalnum())
    return f"{safe}@example.com"


def rand_date(start_days_ago=365, end_days_ahead=365):
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() + timedelta(days=end_days_ahead)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")


def rand_datetime(start_days_ago=365):
    start = datetime.now() - timedelta(days=start_days_ago)
    return (start + timedelta(
        days=random.randint(0, start_days_ago),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )).strftime("%Y-%m-%d %H:%M:%S")


def table_exists(cur, table_name):
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)",
        (table_name,)
    )
    return cur.fetchone() is not None


def get_tables(cur):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [r[0] for r in cur.fetchall()]


def get_columns(cur, table_name):
    cur.execute(f"PRAGMA table_info({table_name})")
    rows = cur.fetchall()
    return [r[1] for r in rows]  # 2nd field is column name


def find_table(cur, candidates):
    tables = get_tables(cur)
    lower_map = {t.lower(): t for t in tables}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None


def pick_column(columns, candidates):
    cols_lower = {c.lower(): c for c in columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None


def filter_data_for_table(cur, table_name, data):
    cols = get_columns(cur, table_name)
    valid = {}
    for k, v in data.items():
        if k in cols:
            valid[k] = v
    return valid


def insert_row(cur, table_name, data):
    data = filter_data_for_table(cur, table_name, data)
    if not data:
        return None
    keys = list(data.keys())
    placeholders = ",".join(["?"] * len(keys))
    sql = f"INSERT INTO {table_name} ({','.join(keys)}) VALUES ({placeholders})"
    cur.execute(sql, [data[k] for k in keys])
    return cur.lastrowid


def maybe_value(columns, names, value):
    col = pick_column(columns, names)
    return col, value


def build_row(columns, mapping):
    row = {}
    for candidate_names, value in mapping:
        col = pick_column(columns, candidate_names)
        if col is not None:
            row[col] = value
    return row


def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    tables = get_tables(cur)
    print("Detected tables:", tables)

    category_table = find_table(cur, ["categories", "category"])
    supplier_table = find_table(cur, ["suppliers", "supplier"])
    product_table = find_table(cur, ["products", "product", "items"])
    customer_table = find_table(cur, ["buyers", "customers", "customer", "clients"])
    sales_table = find_table(cur, ["sales", "sale", "invoices"])
    sale_items_table = find_table(cur, ["sale_items", "sales_items", "invoice_items"])
    stock_tx_table = find_table(cur, ["stock_transactions", "inventory_transactions", "inventory_logs", "stock_movements"])
    user_table = find_table(cur, ["users", "user"])
    login_history_table = find_table(cur, ["login_history", "user_login_history"])
    audit_table = find_table(cur, ["audit_log", "activity_log", "logs"])

    print("Using:")
    print("  category_table =", category_table)
    print("  supplier_table =", supplier_table)
    print("  product_table =", product_table)
    print("  customer_table =", customer_table)
    print("  sales_table =", sales_table)
    print("  sale_items_table =", sale_items_table)
    print("  stock_tx_table =", stock_tx_table)
    print("  user_table =", user_table)
    print("  login_history_table =", login_history_table)
    print("  audit_table =", audit_table)

    category_ids = []
    supplier_ids = []
    product_ids = []
    customer_ids = []
    user_ids = []

    # -------------------------
    # Categories
    # -------------------------
    if category_table:
        cols = get_columns(cur, category_table)
        print(f"Inserting {CATEGORY_COUNT} categories...")
        for i in range(CATEGORY_COUNT):
            name = f"Category {i+1}"
            row = build_row(cols, [
                (["name", "category_name", "title"], name),
                (["description", "notes"], f"Auto-generated category {i+1}"),
                (["created_at", "created_on"], rand_datetime(180)),
                (["updated_at", "updated_on"], rand_datetime(30)),
                (["is_active", "status", "active"], 1),
            ])
            try:
                row_id = insert_row(cur, category_table, row)
                if row_id:
                    category_ids.append(row_id)
            except sqlite3.IntegrityError:
                pass
        conn.commit()

    # -------------------------
    # Suppliers
    # -------------------------
    if supplier_table:
        cols = get_columns(cur, supplier_table)
        print(f"Inserting {SUPPLIER_COUNT} suppliers...")
        for i in range(SUPPLIER_COUNT):
            name = f"Supplier {i+1}"
            city = random.choice(["Mumbai", "Pune", "Delhi", "Chennai", "Bengaluru", "Kolkata", "Hyderabad"])
            row = build_row(cols, [
                (["name", "supplier_name", "company_name"], name),
                (["contact_person", "person_name"], f"Contact {i+1}"),
                (["phone", "mobile", "mobile_number"], rand_phone()),
                (["email"], rand_email(name)),
                (["city"], city),
                (["address"], f"{random.randint(1,999)}, Market Road, {city}"),
                (["gst_number", "gstin"], f"27ABCDE{i:05d}F1Z5"[:15]),
                (["created_at", "created_on"], rand_datetime(180)),
                (["updated_at", "updated_on"], rand_datetime(30)),
                (["is_active", "status", "active"], 1),
            ])
            try:
                row_id = insert_row(cur, supplier_table, row)
                if row_id:
                    supplier_ids.append(row_id)
            except sqlite3.IntegrityError:
                pass
        conn.commit()

    # -------------------------
    # Customers / Buyers
    # -------------------------
    if customer_table:
        cols = get_columns(cur, customer_table)
        print(f"Inserting {CUSTOMER_COUNT} customers...")
        for i in range(CUSTOMER_COUNT):
            name = f"Customer {i+1}"
            city = random.choice(["Mumbai", "Pune", "Delhi", "Chennai", "Bengaluru", "Kolkata", "Hyderabad"])
            row = build_row(cols, [
                (["name", "customer_name", "buyer_name", "full_name"], name),
                (["phone", "mobile", "mobile_number"], rand_phone()),
                (["email"], rand_email(name)),
                (["city"], city),
                (["address"], f"{random.randint(1,999)}, Residency Area, {city}"),
                (["created_at", "created_on"], rand_datetime(180)),
                (["updated_at", "updated_on"], rand_datetime(30)),
            ])
            try:
                row_id = insert_row(cur, customer_table, row)
                if row_id:
                    customer_ids.append(row_id)
            except sqlite3.IntegrityError:
                pass
        conn.commit()

    # -------------------------
    # Users
    # -------------------------
    if user_table:
        cols = get_columns(cur, user_table)
        print(f"Inserting {USER_COUNT} users...")
        for i in range(USER_COUNT):
            username = f"user{i+1}"
            role = "Store Keeper" if i % 3 else "Admin"
            row = build_row(cols, [
                (["username", "user_name", "login"], username),
                (["name", "full_name"], f"Test User {i+1}"),
                (["password", "password_hash", "passwd"], "test123"),
                (["role", "user_role"], role),
                (["phone", "mobile"], rand_phone()),
                (["email"], rand_email(username)),
                (["created_at", "created_on"], rand_datetime(180)),
                (["updated_at", "updated_on"], rand_datetime(30)),
                (["is_active", "status", "active"], 1),
            ])
            try:
                row_id = insert_row(cur, user_table, row)
                if row_id:
                    user_ids.append(row_id)
            except sqlite3.IntegrityError:
                pass
        conn.commit()

    # -------------------------
    # Products
    # -------------------------
    if product_table:
        cols = get_columns(cur, product_table)
        print(f"Inserting {PRODUCT_COUNT} products...")
        for i in range(PRODUCT_COUNT):
            category_id = random.choice(category_ids) if category_ids else None
            supplier_id = random.choice(supplier_ids) if supplier_ids else None
            cost_price = round(random.uniform(10, 1000), 2)
            sell_price = round(cost_price * random.uniform(1.08, 1.6), 2)
            stock_qty = random.randint(0, 500)
            min_stock = random.randint(5, 30)
            product_name = f"Product {i+1} {rand_text('', 4)}"
            sku = f"SKU-{i+1:05d}"
            row = build_row(cols, [
                (["name", "product_name", "title"], product_name),
                (["sku", "product_code", "code"], sku),
                (["barcode"], f"{random.randint(100000000000, 999999999999)}"),
                (["category_id"], category_id),
                (["supplier_id"], supplier_id),
                (["cost_price", "purchase_price", "buy_price", "cost"], cost_price),
                (["selling_price", "sale_price", "mrp", "price"], sell_price),
                (["stock", "quantity", "qty", "current_stock"], stock_qty),
                (["min_stock", "minimum_stock", "reorder_level"], min_stock),
                (["unit"], random.choice(["pcs", "box", "kg", "ltr"])),
                (["expiry_date", "exp_date"], rand_date(0, 720)),
                (["description", "notes"], f"Auto-generated product {i+1}"),
                (["created_at", "created_on"], rand_datetime(180)),
                (["updated_at", "updated_on"], rand_datetime(30)),
                (["is_active", "status", "active"], 1),
            ])
            try:
                row_id = insert_row(cur, product_table, row)
                if row_id:
                    product_ids.append(row_id)
            except sqlite3.IntegrityError:
                pass
            if (i + 1) % 1000 == 0:
                conn.commit()
                print(f"  inserted {i+1} products")
        conn.commit()

    # -------------------------
    # Stock transactions
    # -------------------------
    if stock_tx_table and product_ids:
        cols = get_columns(cur, stock_tx_table)
        print(f"Inserting {STOCK_TX_COUNT} stock transactions...")
        tx_types = ["IN", "OUT", "ADJUSTMENT"]
        for i in range(STOCK_TX_COUNT):
            product_id = random.choice(product_ids)
            user_id = random.choice(user_ids) if user_ids else None
            qty = random.randint(1, 50)
            tx_type = random.choices(tx_types, weights=[50, 35, 15])[0]
            row = build_row(cols, [
                (["product_id", "item_id"], product_id),
                (["user_id"], user_id),
                (["transaction_type", "type", "movement_type", "action"], tx_type),
                (["quantity", "qty"], qty),
                (["reference_no", "ref_no", "reference"], rand_text("REF-", 8)),
                (["remarks", "note", "notes", "description"], f"Auto-generated stock transaction {i+1}"),
                (["created_at", "created_on", "transaction_date", "date"], rand_datetime(365)),
            ])
            try:
                insert_row(cur, stock_tx_table, row)
            except sqlite3.IntegrityError:
                pass
            if (i + 1) % 5000 == 0:
                conn.commit()
                print(f"  inserted {i+1} stock transactions")
        conn.commit()

    # -------------------------
    # Sales and sale items
    # -------------------------
    sale_ids = []
    if sales_table and product_ids:
        sales_cols = get_columns(cur, sales_table)
        print(f"Inserting {SALES_COUNT} sales...")
        for i in range(SALES_COUNT):
            customer_id = random.choice(customer_ids) if customer_ids else None
            user_id = random.choice(user_ids) if user_ids else None
            invoice_no = f"INV-{100000 + i}"
            subtotal = round(random.uniform(500, 15000), 2)
            discount = round(random.uniform(0, subtotal * 0.1), 2)
            gst = round((subtotal - discount) * 0.18, 2)
            total = round(subtotal - discount + gst, 2)
            row = build_row(sales_cols, [
                (["invoice_no", "invoice_number", "bill_no"], invoice_no),
                (["customer_id", "buyer_id", "client_id"], customer_id),
                (["user_id", "created_by"], user_id),
                (["customer_name", "buyer_name"], f"Walk-in Customer {i+1}" if not customer_id else None),
                (["subtotal", "sub_total"], subtotal),
                (["discount"], discount),
                (["gst", "tax", "tax_amount"], gst),
                (["total", "grand_total", "net_total", "amount"], total),
                (["payment_method", "payment_mode"], random.choice(["Cash", "Card", "UPI", "Bank Transfer"])),
                (["status"], "Completed"),
                (["sale_date", "date", "created_at", "created_on"], rand_datetime(365)),
            ])
            row = {k: v for k, v in row.items() if v is not None}
            try:
                sale_id = insert_row(cur, sales_table, row)
                if sale_id:
                    sale_ids.append((sale_id, total))
            except sqlite3.IntegrityError:
                pass
            if (i + 1) % 1000 == 0:
                conn.commit()
                print(f"  inserted {i+1} sales")
        conn.commit()

    if sale_items_table and sale_ids and product_ids:
        cols = get_columns(cur, sale_items_table)
        print("Inserting sale items...")
        for i, (sale_id, total) in enumerate(sale_ids, start=1):
            item_count = random.randint(1, MAX_ITEMS_PER_SALE)
            chosen_products = random.sample(product_ids, min(item_count, len(product_ids)))
            remaining = total

            for idx, product_id in enumerate(chosen_products, start=1):
                qty = random.randint(1, 4)
                unit_price = round(random.uniform(50, 1500), 2)
                line_total = round(qty * unit_price, 2)
                if idx == len(chosen_products):
                    line_total = max(1.0, round(remaining, 2))
                    qty = max(1, qty)
                    unit_price = round(line_total / qty, 2)
                remaining -= line_total

                row = build_row(cols, [
                    (["sale_id", "invoice_id"], sale_id),
                    (["product_id", "item_id"], product_id),
                    (["quantity", "qty"], qty),
                    (["unit_price", "price", "rate", "selling_price"], unit_price),
                    (["total", "line_total", "amount"], line_total),
                    (["created_at", "created_on"], rand_datetime(365)),
                ])
                try:
                    insert_row(cur, sale_items_table, row)
                except sqlite3.IntegrityError:
                    pass

            if i % 1000 == 0:
                conn.commit()
                print(f"  inserted items for {i} sales")
        conn.commit()

    # -------------------------
    # Login history
    # -------------------------
    if login_history_table and user_ids:
        cols = get_columns(cur, login_history_table)
        print("Inserting login history...")
        for i in range(min(2000, len(user_ids) * 100)):
            user_id = random.choice(user_ids)
            row = build_row(cols, [
                (["user_id"], user_id),
                (["login_time", "created_at", "date"], rand_datetime(365)),
                (["ip_address", "ip"], f"192.168.1.{random.randint(2, 254)}"),
                (["status"], "Success"),
            ])
            try:
                insert_row(cur, login_history_table, row)
            except sqlite3.IntegrityError:
                pass
        conn.commit()

    # -------------------------
    # Audit log
    # -------------------------
    if audit_table and user_ids:
        cols = get_columns(cur, audit_table)
        print("Inserting audit logs...")
        actions = ["CREATE_PRODUCT", "UPDATE_PRODUCT", "LOGIN", "CREATE_SALE", "UPDATE_STOCK"]
        for i in range(3000):
            user_id = random.choice(user_ids)
            row = build_row(cols, [
                (["user_id"], user_id),
                (["action"], random.choice(actions)),
                (["description", "details", "note"], f"Auto-generated audit event {i+1}"),
                (["created_at", "created_on", "date"], rand_datetime(365)),
            ])
            try:
                insert_row(cur, audit_table, row)
            except sqlite3.IntegrityError:
                pass
        conn.commit()

    conn.execute("VACUUM")
    conn.close()
    print("Done. Large test data generated successfully.")


if __name__ == "__main__":
    main()
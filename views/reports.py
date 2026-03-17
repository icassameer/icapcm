# ============================================================
#  ICA PMS — Reports View
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os, sys, datetime, csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import (DataTable, make_btn, make_green_btn, card_frame,
                            show_toast, format_currency, format_date,
                            export_to_excel, export_to_pdf, today_str, month_start_str)


REPORTS = [
    ('📊 Inventory Status',     'inventory'),
    ('📈 Stock Movement',       'stock_movement'),
    ('💰 Sales Report',         'sales'),
    ('⚠ Low Stock Report',     'low_stock'),
    ('🏭 Supplier Report',      'supplier'),
    ('👤 User Activity',        'audit'),
    ('🔑 Login History',        'login'),
]


class ReportsView(ctk.CTkFrame):
    def __init__(self, parent, db, user, **kwargs):
        super().__init__(parent, fg_color=config.BG, **kwargs)
        self.db = db
        self.user = user
        self.is_admin = user['role'] == config.ROLE_ADMIN
        self.current_report = 'inventory'
        self.current_data = []
        self.current_cols = []
        self._build()
        self.load_report('inventory')

    def _build(self):
        # Main layout: left sidebar + right content
        main = ctk.CTkFrame(self, fg_color='transparent')
        main.pack(fill='both', expand=True)

        # ── Left Sidebar ─────────────────────────────────────
        sidebar = ctk.CTkFrame(main, fg_color=config.SIDEBAR_BG, width=200, corner_radius=0)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text='Reports',
                      font=('Segoe UI', 14, 'bold'), text_color='white').pack(
            anchor='w', padx=16, pady=(20, 12))

        self.nav_btns = {}
        for label, key in REPORTS:
            btn = ctk.CTkButton(sidebar, text=label, anchor='w', height=40,
                                 fg_color='transparent', hover_color=config.HOVER_NAV,
                                 text_color='#B0BAD4', font=('Segoe UI', 12),
                                 command=lambda k=key: self.load_report(k))
            btn.pack(fill='x', padx=8, pady=2)
            self.nav_btns[key] = btn

        # ── Right Panel ──────────────────────────────────────
        right = ctk.CTkFrame(main, fg_color=config.BG)
        right.pack(side='left', fill='both', expand=True)

        # Header
        hdr = ctk.CTkFrame(right, fg_color='white', height=64)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)

        self.report_title = ctk.CTkLabel(hdr, text='Reports',
                                          font=('Segoe UI', 18, 'bold'), text_color=config.PRIMARY)
        self.report_title.pack(side='left', padx=20, pady=16)

        # Export buttons
        export_frame = ctk.CTkFrame(hdr, fg_color='transparent')
        export_frame.pack(side='right', padx=16, pady=12)

        make_btn(export_frame, '📄 PDF', self.export_pdf,
                  color='#EF4444', hover='#DC2626', width=80, height=36).pack(side='right', padx=4)
        make_btn(export_frame, '📊 Excel', self.export_excel,
                  color='#10B981', hover='#059669', width=90, height=36).pack(side='right', padx=4)
        make_btn(export_frame, '📋 CSV', self.export_csv,
                  color='#6B7280', hover='#4B5563', width=80, height=36).pack(side='right', padx=4)
        make_btn(export_frame, '🖨 Print', self.print_report,
                  color='#7C3AED', hover='#6D28D9', width=80, height=36).pack(side='right', padx=4)

        # ── Filters ──────────────────────────────────────────
        self.filter_frame = ctk.CTkFrame(right, fg_color='white', height=54)
        self.filter_frame.pack(fill='x', pady=(0, 2))
        self.filter_frame.pack_propagate(False)
        self._build_date_filters(self.filter_frame)

        # ── Stats bar ────────────────────────────────────────
        self.stats_bar = ctk.CTkFrame(right, fg_color='white', height=46)
        self.stats_bar.pack(fill='x', pady=(0, 4))
        self.stats_bar.pack_propagate(False)
        self.stats_lbl = ctk.CTkLabel(self.stats_bar, text='',
                                       font=('Segoe UI', 12), text_color=config.TEXT_MID)
        self.stats_lbl.pack(side='left', padx=20, pady=10)

        # ── Table ────────────────────────────────────────────
        self.table_container = ctk.CTkFrame(right, fg_color='white', corner_radius=12)
        self.table_container.pack(fill='both', expand=True, padx=16, pady=(0, 12))
        self.table = None

    def _build_date_filters(self, parent):
        inner = ctk.CTkFrame(parent, fg_color='transparent')
        inner.pack(side='left', padx=16, pady=10)

        ctk.CTkLabel(inner, text='From:', font=('Segoe UI', 12),
                      text_color=config.TEXT_MID).pack(side='left', padx=(0,4))
        self.date_from_var = ctk.StringVar(value=month_start_str())
        ctk.CTkEntry(inner, textvariable=self.date_from_var, width=120,
                      fg_color='white', border_color='#D1D5DB',
                      text_color=config.TEXT_DARK).pack(side='left')

        ctk.CTkLabel(inner, text='To:', font=('Segoe UI', 12),
                      text_color=config.TEXT_MID).pack(side='left', padx=(12,4))
        self.date_to_var = ctk.StringVar(value=today_str())
        ctk.CTkEntry(inner, textvariable=self.date_to_var, width=120,
                      fg_color='white', border_color='#D1D5DB',
                      text_color=config.TEXT_DARK).pack(side='left')

        make_btn(inner, '🔍 Generate', self._on_filter,
                  width=110, height=34).pack(side='left', padx=12)

        # Quick buttons
        for label, days in [('Today', 0), ('Week', 7), ('Month', 30), ('Year', 365)]:
            make_btn(inner, label, lambda d=days: self._quick_date(d),
                      color='#F3F4F6', hover='#E5E7EB',
                      width=60, height=34).pack(side='left', padx=2)

    def _quick_date(self, days):
        today = datetime.date.today()
        if days == 0:
            self.date_from_var.set(today.isoformat())
        else:
            start = today - datetime.timedelta(days=days)
            self.date_from_var.set(start.isoformat())
        self.date_to_var.set(today.isoformat())
        self._on_filter()

    def _on_filter(self):
        self.load_report(self.current_report)

    def load_report(self, key):
        self.current_report = key

        # Highlight nav
        for k, btn in self.nav_btns.items():
            btn.configure(
                fg_color=config.ACCENT if k==key else 'transparent',
                text_color='white' if k==key else '#B0BAD4'
            )

        # Title
        label = next((l for l, k in REPORTS if k==key), key)
        self.report_title.configure(text=label)

        # Clear table
        for w in self.table_container.winfo_children():
            w.destroy()

        date_from = self.date_from_var.get()
        date_to   = self.date_to_var.get()

        # ── Load data by type ─────────────────────────────
        if key == 'inventory':
            self._load_inventory()
        elif key == 'stock_movement':
            self._load_stock_movement(date_from, date_to)
        elif key == 'sales':
            self._load_sales(date_from, date_to)
        elif key == 'low_stock':
            self._load_low_stock()
        elif key == 'supplier':
            self._load_supplier()
        elif key == 'audit':
            self._load_audit()
        elif key == 'login':
            self._load_login_history()

    def _make_table(self, cols, col_widths=None):
        for w in self.table_container.winfo_children():
            w.destroy()
        t = DataTable(self.table_container, cols, col_widths, height=22)
        t.pack(fill='both', expand=True, padx=8, pady=8)
        self.table = t
        return t

    def _load_inventory(self):
        data = self.db.get_inventory_report()
        cols = ('SKU', 'Product Name', 'Category', 'Supplier', 'Qty',
                 'Min Stock', 'Cost Price', 'Sell Price', 'Stock Value', 'Status')
        col_w = {'SKU':90,'Product Name':200,'Category':110,'Supplier':130,
                  'Qty':60,'Min Stock':75,'Cost Price':90,'Sell Price':90,
                  'Stock Value':100,'Status':90}
        t = self._make_table(cols, col_w)
        rows = []
        total_val = 0
        for d in data:
            total_val += d.get('stock_value', 0) or 0
            rows.append((d.get('sku',''), d.get('name',''), d.get('category',''),
                          d.get('supplier',''), d.get('quantity',0), d.get('min_stock',0),
                          format_currency(d.get('cost_price',0)),
                          format_currency(d.get('selling_price',0)),
                          format_currency(d.get('stock_value',0)),
                          d.get('status','')))
        t.load_raw(rows)
        self.stats_lbl.configure(
            text=f"Total Products: {len(data)}  |  Total Stock Value: {format_currency(total_val)}")
        self.current_data = rows
        self.current_cols = list(cols)

    def _load_stock_movement(self, df, dt):
        data = self.db.get_stock_transactions(date_from=df, date_to=dt)
        cols = ('Date','SKU','Product','Type','Qty','Prev Qty','New Qty','Unit Price','Total','Ref No','User')
        col_w = {'Date':130,'SKU':85,'Product':180,'Type':90,'Qty':55,'Prev Qty':70,
                  'New Qty':70,'Unit Price':90,'Total':100,'Ref No':110,'User':100}
        t = self._make_table(cols, col_w)
        rows = [(format_date(d.get('created_at','')),d.get('sku',''),d.get('product_name',''),
                  d.get('transaction_type',''),d.get('quantity',0),d.get('previous_qty',0),
                  d.get('new_qty',0),format_currency(d.get('unit_price',0)),
                  format_currency(d.get('total_value',0)),
                  d.get('reference_no',''),d.get('user_name','')) for d in data]
        t.load_raw(rows)
        self.stats_lbl.configure(text=f"Total Transactions: {len(data)}")
        self.current_data = rows; self.current_cols = list(cols)

    def _load_sales(self, df, dt):
        data = self.db.get_sales(date_from=df, date_to=dt)
        cols = ('Date','Invoice No','Customer','Total','Discount','Net Amount','Payment','User')
        col_w = {'Date':130,'Invoice No':140,'Customer':140,'Total':100,'Discount':80,
                  'Net Amount':110,'Payment':100,'User':110}
        t = self._make_table(cols, col_w)
        rows = []
        total_net = 0
        for d in data:
            total_net += d.get('net_amount',0) or 0
            rows.append((format_date(d.get('created_at','')),d.get('invoice_no',''),
                          d.get('customer_name',''),format_currency(d.get('total_amount',0)),
                          format_currency(d.get('discount',0)),format_currency(d.get('net_amount',0)),
                          d.get('payment_method',''),d.get('user_name','')))
        t.load_raw(rows)
        self.stats_lbl.configure(
            text=f"Total Sales: {len(data)}  |  Net Revenue: {format_currency(total_net)}")
        self.current_data = rows; self.current_cols = list(cols)

    def _load_low_stock(self):
        products = self.db.get_products(low_stock_only=True)
        cols = ('SKU','Product Name','Category','Supplier','Current Qty','Min Stock','Shortage','Cost Price')
        col_w = {'SKU':90,'Product Name':200,'Category':120,'Supplier':140,
                  'Current Qty':90,'Min Stock':80,'Shortage':80,'Cost Price':90}
        t = self._make_table(cols, col_w)
        rows = [(p['sku'],p['name'],p.get('category_name',''),p.get('supplier_name',''),
                  p['quantity'],p['min_stock'],max(0,p['min_stock']-p['quantity']),
                  format_currency(p['cost_price'])) for p in products]
        t.load_raw(rows)
        self.stats_lbl.configure(text=f"Low Stock Products: {len(products)}")
        self.current_data = rows; self.current_cols = list(cols)

    def _load_supplier(self):
        data = self.db.get_supplier_report()
        cols = ('Supplier','Products','Total Qty','Stock Value')
        col_w = {'Supplier':220,'Products':100,'Total Qty':100,'Stock Value':140}
        t = self._make_table(cols, col_w)
        rows = [(d.get('supplier',''),d.get('product_count',0),d.get('total_qty',0),
                  format_currency(d.get('stock_value',0))) for d in data]
        t.load_raw(rows)
        self.stats_lbl.configure(text=f"Total Suppliers: {len(data)}")
        self.current_data = rows; self.current_cols = list(cols)

    def _load_audit(self):
        if not self.is_admin:
            self.stats_lbl.configure(text='⚠ Admin access required for audit logs')
            return
        data = self.db.get_audit_log(500)
        cols = ('Date','User','Action','Module','Details')
        col_w = {'Date':130,'User':120,'Action':140,'Module':100,'Details':300}
        t = self._make_table(cols, col_w)
        rows = [(format_date(d.get('created_at','')),d.get('username',''),
                  d.get('action',''),d.get('module',''),d.get('details','')) for d in data]
        t.load_raw(rows)
        self.stats_lbl.configure(text=f"Audit Records: {len(data)}")
        self.current_data = rows; self.current_cols = list(cols)

    def _load_login_history(self):
        data = self.db.get_login_history(300)
        cols = ('Date','Username','Full Name','Status')
        col_w = {'Date':150,'Username':140,'Full Name':180,'Status':90}
        t = self._make_table(cols, col_w)
        rows = [(format_date(d.get('created_at','')),d.get('username',''),
                  d.get('full_name',''),d.get('status','')) for d in data]
        t.load_raw(rows)
        for i, d in enumerate(data):
            color = '#F0FFF4' if d.get('status')=='SUCCESS' else '#FFF5F5'
            self.table.tree.item(str(i), tags=('row',))
            self.table.tree.tag_configure('row', background='white')
        self.stats_lbl.configure(text=f"Login Records: {len(data)}")
        self.current_data = rows; self.current_cols = list(cols)

    # ── Export ───────────────────────────────────────────────
    def export_excel(self):
        if not self.current_data:
            messagebox.showinfo('No Data', 'Please generate a report first.'); return
        path = filedialog.asksaveasfilename(
            defaultextension='.xlsx', filetypes=[('Excel', '*.xlsx')],
            initialfile=f'ICA_{self.current_report}_{today_str()}.xlsx')
        if path:
            if export_to_excel(self.current_data, self.current_cols, path, self.current_report):
                show_toast(self, f'✓ Exported to Excel')
                os.startfile(path) if os.name=='nt' else None

    def export_csv(self):
        if not self.current_data:
            messagebox.showinfo('No Data', 'Please generate a report first.'); return
        path = filedialog.asksaveasfilename(
            defaultextension='.csv', filetypes=[('CSV', '*.csv')],
            initialfile=f'ICA_{self.current_report}_{today_str()}.csv')
        if path:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.current_cols)
                writer.writerows(self.current_data)
            show_toast(self, '✓ Exported to CSV')

    def export_pdf(self):
        if not self.current_data:
            messagebox.showinfo('No Data', 'Please generate a report first.'); return
        path = filedialog.asksaveasfilename(
            defaultextension='.pdf', filetypes=[('PDF', '*.pdf')],
            initialfile=f'ICA_{self.current_report}_{today_str()}.pdf')
        if path:
            title = next((l for l, k in REPORTS if k==self.current_report), self.current_report)
            if export_to_pdf(title, self.current_cols, self.current_data, path):
                show_toast(self, '✓ PDF exported')
                if os.name == 'nt':
                    os.startfile(path)

    def print_report(self):
        messagebox.showinfo('Print', 'Please export to PDF and print from your PDF viewer.')

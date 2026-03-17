# ============================================================
#  ICA PMS — Dashboard View
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import format_currency, format_date, stat_card, card_frame

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.patches as mpatches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

NAV_COLOR = config.PRIMARY
ACC = config.ACCENT


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, db, user, **kwargs):
        super().__init__(parent, fg_color=config.BG, **kwargs)
        self.db = db
        self.user = user
        self._charts = []
        self._build()

    def _build(self):
        # ── Header ──────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color='white', corner_radius=0, height=60)
        header.pack(fill='x', padx=0, pady=(0, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text='📊  Dashboard Overview',
                      font=('Segoe UI', 18, 'bold'), text_color=config.PRIMARY).pack(
            side='left', padx=20, pady=16)

        refresh_btn = ctk.CTkButton(header, text='↻  Refresh', width=100, height=32,
                                     fg_color=config.ACCENT, hover_color='#00B870',
                                     font=('Segoe UI', 12, 'bold'), command=self.refresh)
        refresh_btn.pack(side='right', padx=20, pady=14)

        ts = ctk.CTkLabel(header, text='', font=('Segoe UI', 11), text_color=config.TEXT_MID)
        ts.pack(side='right', padx=8, pady=14)
        self._ts_label = ts

        # ── Scrollable Content ───────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=config.BG)
        self.scroll.pack(fill='both', expand=True, padx=0, pady=0)

        self.refresh()

    def refresh(self):
        import datetime
        self._ts_label.configure(text=f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

        # Clear
        for w in self.scroll.winfo_children():
            w.destroy()
        for c in self._charts:
            try:
                if HAS_MPL:
                    plt.close(c)
            except Exception:
                pass
        self._charts = []

        stats = self.db.get_dashboard_stats()
        self._build_kpi(stats)
        self._build_alerts(stats)
        if HAS_MPL:
            self._build_charts()
        self._build_recent_transactions()

    def _build_kpi(self, s):
        frame = ctk.CTkFrame(self.scroll, fg_color='transparent')
        frame.pack(fill='x', padx=20, pady=(16, 8))

        ctk.CTkLabel(frame, text='Key Performance Indicators',
                      font=('Segoe UI', 14, 'bold'), text_color=config.PRIMARY).pack(anchor='w', pady=(0, 10))

        cards_row = ctk.CTkFrame(frame, fg_color='transparent')
        cards_row.pack(fill='x')

        kpis = [
            ('Total Products', s['total_products'], 'Active SKUs', config.PRIMARY, '📦'),
            ('Categories', s['total_categories'], 'Product groups', '#7C3AED', '🏷'),
            ('Suppliers', s['total_suppliers'], 'Active vendors', '#0891B2', '🏭'),
            ('Low Stock', s['low_stock'], 'Need attention', '#F59E0B', '⚠'),
            ('Out of Stock', s['out_of_stock'], 'Immediate action', '#EF4444', '🚫'),
            ('Active Users', s['total_users'], 'System users', '#10B981', '👥'),
        ]

        for title, val, sub, color, icon in kpis:
            c = stat_card(cards_row, title, val, sub, color, icon)
            c.pack(side='left', padx=8, pady=4)

        # Sales row
        sales_row = ctk.CTkFrame(frame, fg_color='transparent')
        sales_row.pack(fill='x', pady=(12, 0))

        sales_kpis = [
            ("Today's Sales", format_currency(s['sales_today']), 'Today', '#1B2A6B', '💰'),
            ('Weekly Sales', format_currency(s['sales_week']), 'Last 7 days', '#00A693', '📈'),
            ('Monthly Sales', format_currency(s['sales_month']), 'This month', '#7C3AED', '📅'),
            ('Stock Value', format_currency(s['total_stock_value']), 'At cost price', '#0891B2', '🏪'),
        ]
        for title, val, sub, color, icon in sales_kpis:
            c = stat_card(sales_row, title, val, sub, color, icon)
            c.pack(side='left', padx=8, pady=4)

    def _build_alerts(self, s):
        if s['low_stock'] == 0 and s['out_of_stock'] == 0:
            return
        frame = card_frame(self.scroll)
        frame.pack(fill='x', padx=20, pady=8)

        ctk.CTkLabel(frame, text='⚠  Stock Alerts', font=('Segoe UI', 14, 'bold'),
                      text_color='#F59E0B').pack(anchor='w', padx=16, pady=(12, 4))

        row = ctk.CTkFrame(frame, fg_color='transparent')
        row.pack(fill='x', padx=16, pady=(0, 12))

        if s['out_of_stock'] > 0:
            alert = ctk.CTkFrame(row, fg_color='#FEE2E2', corner_radius=8)
            alert.pack(side='left', padx=(0, 12))
            ctk.CTkLabel(alert, text=f"🚫  {s['out_of_stock']} products OUT OF STOCK",
                          font=('Segoe UI', 12, 'bold'), text_color='#DC2626').pack(padx=16, pady=10)

        if s['low_stock'] > 0:
            alert2 = ctk.CTkFrame(row, fg_color='#FEF3C7', corner_radius=8)
            alert2.pack(side='left')
            ctk.CTkLabel(alert2, text=f"⚠  {s['low_stock']} products BELOW MINIMUM STOCK",
                          font=('Segoe UI', 12, 'bold'), text_color='#92400E').pack(padx=16, pady=10)

    def _build_charts(self):
        charts_section = ctk.CTkFrame(self.scroll, fg_color='transparent')
        charts_section.pack(fill='x', padx=20, pady=8)

        ctk.CTkLabel(charts_section, text='Analytics & Charts',
                      font=('Segoe UI', 14, 'bold'), text_color=config.PRIMARY).pack(anchor='w', pady=(0, 10))

        if not HAS_MPL:
            msg = ctk.CTkFrame(charts_section, fg_color='#FEF3C7', corner_radius=10)
            msg.pack(fill='x', pady=8)
            ctk.CTkLabel(msg,
                          text='⚠  Charts unavailable. Run:  python -m pip install matplotlib numpy',
                          font=('Segoe UI', 12), text_color='#92400E').pack(pady=16)
            return

        row1 = ctk.CTkFrame(charts_section, fg_color='transparent')
        row1.pack(fill='x')

        row2 = ctk.CTkFrame(charts_section, fg_color='transparent')
        row2.pack(fill='x', pady=12)

        self._chart_monthly_sales(row1)
        self._chart_category_stock(row1)
        self._chart_stock_distribution(row1)

        self._chart_fast_moving(row2)
        self._chart_slow_moving(row2)
        self._chart_stock_value_trend(row2)
        self._chart_product_status(row2)

    def _make_chart_frame(self, parent, title):
        outer = card_frame(parent)
        outer.pack(side='left', padx=6, pady=4, fill='y')
        ctk.CTkLabel(outer, text=title, font=('Segoe UI', 12, 'bold'),
                      text_color=config.PRIMARY).pack(anchor='w', padx=12, pady=(10, 0))
        return outer

    def _embed_fig(self, fig, parent_frame):
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(padx=8, pady=8)
        self._charts.append(fig)

    def _chart_monthly_sales(self, parent):
        frame = self._make_chart_frame(parent, '📅 Monthly Sales (12 months)')
        data = self.db.get_monthly_sales()
        months = [r['month'] for r in data] or ['No Data']
        values = [r['total'] for r in data] or [0]

        fig = Figure(figsize=(5, 3), dpi=80, facecolor='white')
        ax = fig.add_subplot(111)
        bars = ax.bar(range(len(months)), values, color=config.ACCENT, width=0.6)
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels([m[-5:] for m in months], rotation=45, fontsize=8)
        ax.set_ylabel('Sales (₹)', fontsize=9)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_facecolor('#F8FAFC')
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2., h,
                         f'₹{h/1000:.0f}k' if h >= 1000 else f'₹{h:.0f}',
                         ha='center', va='bottom', fontsize=7)
        fig.tight_layout()
        self._embed_fig(fig, frame)

    def _chart_category_stock(self, parent):
        frame = self._make_chart_frame(parent, '🏷 Category-wise Stock')
        data = self.db.get_category_stock()
        names = [r['name'][:12] for r in data[:8]] or ['No Categories']
        values = [r['total_qty'] for r in data[:8]] or [0]
        colors = ['#1B2A6B', '#00D084', '#7C3AED', '#0891B2', '#F59E0B',
                  '#EF4444', '#10B981', '#F97316']

        fig = Figure(figsize=(4, 3), dpi=80, facecolor='white')
        ax = fig.add_subplot(111)
        if sum(values) > 0:
            wedges, texts, autotexts = ax.pie(values, labels=None, autopct='%1.0f%%',
                                               colors=colors[:len(values)], startangle=90,
                                               pctdistance=0.8)
            for at in autotexts: at.set_fontsize(8)
            ax.legend(wedges, names, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=7)
        else:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center')
        fig.tight_layout()
        self._embed_fig(fig, frame)

    def _chart_stock_distribution(self, parent):
        frame = self._make_chart_frame(parent, '📦 Stock Status')
        stats = self.db.get_dashboard_stats()
        total = stats['total_products']
        low = stats['low_stock']
        out = stats['out_of_stock']
        ok = max(0, total - low - out)

        fig = Figure(figsize=(3.5, 3), dpi=80, facecolor='white')
        ax = fig.add_subplot(111)
        vals = [ok, low, out]
        lbls = ['In Stock', 'Low Stock', 'Out of Stock']
        clrs = ['#10B981', '#F59E0B', '#EF4444']
        non_zero = [(v, l, c) for v, l, c in zip(vals, lbls, clrs) if v > 0]
        if non_zero:
            ax.pie([v for v,l,c in non_zero],
                   labels=[l for v,l,c in non_zero],
                   colors=[c for v,l,c in non_zero],
                   autopct='%1.0f%%', startangle=90)
        else:
            ax.text(0.5, 0.5, 'No products', ha='center', va='center')
        fig.tight_layout()
        self._embed_fig(fig, frame)

    def _chart_fast_moving(self, parent):
        frame = self._make_chart_frame(parent, '🚀 Fast Moving Products')
        data = self.db.get_fast_moving(8)
        names = [r['name'][:15] for r in data] or ['No Sales']
        values = [r['sold_qty'] for r in data] or [0]

        fig = Figure(figsize=(5, 3), dpi=80, facecolor='white')
        ax = fig.add_subplot(111)
        ax.barh(names[::-1], values[::-1], color=config.PRIMARY, height=0.6)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_xlabel('Units Sold', fontsize=9)
        ax.set_facecolor('#F8FAFC')
        ax.tick_params(axis='y', labelsize=8)
        fig.tight_layout()
        self._embed_fig(fig, frame)

    def _chart_slow_moving(self, parent):
        frame = self._make_chart_frame(parent, '🐢 Slow Moving (High Stock)')
        products = self.db.get_products()
        slow = sorted(products, key=lambda x: x['quantity'], reverse=True)[:8]
        names = [p['name'][:15] for p in slow]
        values = [p['quantity'] for p in slow]

        fig = Figure(figsize=(5, 3), dpi=80, facecolor='white')
        ax = fig.add_subplot(111)
        ax.barh(names[::-1], values[::-1], color='#7C3AED', height=0.6)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_xlabel('Stock Qty', fontsize=9)
        ax.set_facecolor('#F8FAFC')
        ax.tick_params(axis='y', labelsize=8)
        fig.tight_layout()
        self._embed_fig(fig, frame)

    def _chart_stock_value_trend(self, parent):
        frame = self._make_chart_frame(parent, '📈 Stock Value Trend (30d)')
        data = self.db.get_stock_value_trend()
        dates = [r['date'][-5:] for r in data] or ['No data']
        values = [r['net_value'] for r in data] or [0]

        fig = Figure(figsize=(5, 3), dpi=80, facecolor='white')
        ax = fig.add_subplot(111)
        if len(dates) > 1:
            ax.plot(range(len(dates)), values, color=config.ACCENT, linewidth=2, marker='o', markersize=4)
            ax.fill_between(range(len(dates)), values, alpha=0.15, color=config.ACCENT)
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45, fontsize=7)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_facecolor('#F8FAFC')
        fig.tight_layout()
        self._embed_fig(fig, frame)

    def _chart_product_status(self, parent):
        frame = self._make_chart_frame(parent, '🏭 Supplier Performance')
        data = self.db.get_supplier_report()[:6]
        names = [r['supplier'][:12] for r in data] or ['No Suppliers']
        values = [r['stock_value'] for r in data] or [0]

        fig = Figure(figsize=(4, 3), dpi=80, facecolor='white')
        ax = fig.add_subplot(111)
        bars = ax.bar(range(len(names)), values, color=config.ACCENT, width=0.6)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=30, ha='right', fontsize=8)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_ylabel('Stock Value (₹)', fontsize=9)
        ax.set_facecolor('#F8FAFC')
        fig.tight_layout()
        self._embed_fig(fig, frame)

    def _build_recent_transactions(self):
        frame = card_frame(self.scroll)
        frame.pack(fill='x', padx=20, pady=(8, 20))

        ctk.CTkLabel(frame, text='🕒  Recent Stock Transactions',
                      font=('Segoe UI', 14, 'bold'), text_color=config.PRIMARY).pack(
            anchor='w', padx=16, pady=(12, 0))

        txs = self.db.get_stock_transactions(limit=15)

        # Simple table
        cols = ('Date', 'Product', 'Type', 'Qty', 'Prev Qty', 'New Qty', 'User')
        style = ttk.Style()
        style.configure('Dash.Treeview', rowheight=28, font=('Segoe UI', 10))
        style.configure('Dash.Treeview.Heading', font=('Segoe UI', 10, 'bold'),
                         background='#1B2A6B', foreground='white')

        tree = ttk.Treeview(frame, columns=cols, show='headings', height=min(len(txs), 12),
                             style='Dash.Treeview')
        widths = [130, 200, 90, 60, 80, 80, 120]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w)

        type_color = {'IN': '#DCFCE7', 'OUT': '#FEE2E2', 'ADJUSTMENT': '#FEF3C7', 'RETURN': '#DBEAFE'}
        for i, tx in enumerate(txs):
            tag = tx.get('transaction_type', 'IN')
            tree.insert('', 'end', values=(
                format_date(tx.get('created_at', '')),
                tx.get('product_name', '')[:30],
                tx.get('transaction_type', ''),
                tx.get('quantity', 0),
                tx.get('previous_qty', 0),
                tx.get('new_qty', 0),
                tx.get('user_name', ''),
            ), tags=(tag,))

        tree.tag_configure('IN', background='#F0FFF4')
        tree.tag_configure('OUT', background='#FFF5F5')
        tree.tag_configure('ADJUSTMENT', background='#FFFBEB')
        tree.tag_configure('RETURN', background='#EFF6FF')

        tree.pack(fill='x', padx=16, pady=(8, 16))

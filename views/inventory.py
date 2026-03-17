# ============================================================
#  ICA PMS — Inventory Management View (Fixed)
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import (DataTable, SearchBar, make_btn, make_green_btn,
                            make_danger_btn, card_frame, show_toast, format_currency, format_date)

TX_COLS = ('Date', 'SKU', 'Product', 'Type', 'Qty', 'Prev', 'New Qty',
           'Unit Price', 'Total Value', 'Buyer/Ref', 'User', 'Notes')
TX_WIDTHS = {
    'Date': 130, 'SKU': 85, 'Product': 175, 'Type': 85, 'Qty': 55,
    'Prev': 55, 'New Qty': 65, 'Unit Price': 90, 'Total Value': 100,
    'Buyer/Ref': 130, 'User': 100, 'Notes': 180
}


class InventoryView(ctk.CTkFrame):
    def __init__(self, parent, db, user, **kwargs):
        super().__init__(parent, fg_color=config.BG, **kwargs)
        self.db = db
        self.user = user
        self.is_admin = user['role'] == config.ROLE_ADMIN
        self._build()
        self._load_all_tabs()

    def _build(self):
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color='white', height=64)
        toolbar.pack(fill='x', pady=(0, 2))
        toolbar.pack_propagate(False)

        ctk.CTkLabel(toolbar, text='🏪  Inventory Management',
                      font=('Segoe UI', 18, 'bold'), text_color=config.PRIMARY).pack(
            side='left', padx=20, pady=16)

        btn_row = ctk.CTkFrame(toolbar, fg_color='transparent')
        btn_row.pack(side='right', padx=16, pady=10)
        make_green_btn(btn_row, '📥 Stock In',  self.stock_in_dialog,  width=110).pack(side='left', padx=4)
        make_danger_btn(btn_row, '📤 Stock Out', self.stock_out_dialog, width=110).pack(side='left', padx=4)
        make_btn(btn_row, '↩ Return',  self.return_dialog,  color='#F59E0B', hover='#D97706', width=100).pack(side='left', padx=4)
        make_btn(btn_row, '⚙ Adjust',  self.adjust_dialog,  color='#7C3AED', hover='#6D28D9', width=100).pack(side='left', padx=4)

        # Tabs
        self.tabs = ctk.CTkTabview(
            self, fg_color='white',
            segmented_button_fg_color=config.PRIMARY,
            segmented_button_selected_color=config.ACCENT,
            segmented_button_selected_hover_color='#00B870',
            text_color='white'
        )
        self.tabs.pack(fill='both', expand=True, padx=16, pady=8)
        for t in ('All Transactions', 'Stock In', 'Stock Out', 'Adjustments', 'Low Stock'):
            self.tabs.add(t)

        self.all_table = self._build_tx_tab(self.tabs.tab('All Transactions'), None)
        self.in_table  = self._build_tx_tab(self.tabs.tab('Stock In'),         'IN')
        self.out_table = self._build_tx_tab(self.tabs.tab('Stock Out'),         'OUT')
        self.adj_table = self._build_tx_tab(self.tabs.tab('Adjustments'),       'ADJUSTMENT')
        self._build_low_stock_tab(self.tabs.tab('Low Stock'))
        self.tabs.set('All Transactions')

    def _build_tx_tab(self, tab, tx_type):
        filter_row = ctk.CTkFrame(tab, fg_color='transparent')
        filter_row.pack(fill='x', pady=(8, 4))

        search_var = ctk.StringVar()
        ctk.CTkLabel(filter_row, text='🔍', font=('Segoe UI', 14)).pack(side='left', padx=(8,2))
        ctk.CTkEntry(filter_row, textvariable=search_var,
                      placeholder_text='Search product or SKU...', width=240,
                      fg_color='white', border_color='#D1D5DB',
                      text_color=config.TEXT_DARK).pack(side='left', padx=(0,12))

        ctk.CTkLabel(filter_row, text='From:', font=('Segoe UI', 12),
                      text_color=config.TEXT_MID).pack(side='left', padx=(0,4))
        from_var = ctk.StringVar()
        ctk.CTkEntry(filter_row, textvariable=from_var, width=110,
                      placeholder_text='YYYY-MM-DD', fg_color='white',
                      border_color='#D1D5DB', text_color=config.TEXT_DARK).pack(side='left')

        ctk.CTkLabel(filter_row, text='To:', font=('Segoe UI', 12),
                      text_color=config.TEXT_MID).pack(side='left', padx=(10,4))
        to_var = ctk.StringVar()
        ctk.CTkEntry(filter_row, textvariable=to_var, width=110,
                      placeholder_text='YYYY-MM-DD', fg_color='white',
                      border_color='#D1D5DB', text_color=config.TEXT_DARK).pack(side='left')

        count_lbl = ctk.CTkLabel(filter_row, text='', font=('Segoe UI', 11),
                                  text_color=config.TEXT_MID)
        count_lbl.pack(side='right', padx=12)

        def apply(*_):
            self._reload_tab(tx_type, search_var.get(), from_var.get(), to_var.get(), count_lbl)

        make_btn(filter_row, '🔍 Filter', apply, width=90, height=32).pack(side='left', padx=8)
        search_var.trace_add('write', apply)

        table = DataTable(tab, TX_COLS, TX_WIDTHS, height=18)
        table.pack(fill='both', expand=True, padx=4, pady=4)
        table._count_lbl = count_lbl
        return table

    def _reload_tab(self, tx_type, search='', date_from='', date_to='', count_lbl=None):
        txs = self.db.get_stock_transactions(
            tx_type=tx_type,
            date_from=date_from or None,
            date_to=date_to or None
        )
        if search:
            sl = search.lower()
            txs = [t for t in txs
                   if sl in (t.get('product_name','') + t.get('sku','')).lower()]

        rows = []
        for t in txs:
            buyer_ref = t.get('buyer_name') or t.get('reference_no','') or ''
            rows.append((
                format_date(t.get('created_at','')),
                t.get('sku',''),
                t.get('product_name','')[:25],
                t.get('transaction_type',''),
                t.get('quantity', 0),
                t.get('previous_qty', 0),
                t.get('new_qty', 0),
                format_currency(t.get('unit_price', 0)),
                format_currency(t.get('total_value', 0)),
                buyer_ref[:22],
                t.get('user_name',''),
                t.get('notes','')[:30],
            ))

        table = {None: self.all_table, 'IN': self.in_table,
                 'OUT': self.out_table, 'ADJUSTMENT': self.adj_table}.get(tx_type)
        if not table:
            return

        table.load_raw(rows)
        table.tree.tag_configure('in_tag',  background='#F0FFF4')
        table.tree.tag_configure('out_tag', background='#FFF5F5')
        table.tree.tag_configure('adj_tag', background='#FFFBEB')
        table.tree.tag_configure('ret_tag', background='#EFF6FF')
        type_tag_map = {'IN':'in_tag','OUT':'out_tag','ADJUSTMENT':'adj_tag','RETURN':'ret_tag'}
        for i, t in enumerate(txs):
            tag = type_tag_map.get(t.get('transaction_type',''), 'even')
            table.tree.item(str(i), tags=(tag,))

        if count_lbl:
            count_lbl.configure(text=f'{len(rows)} records')

    def _load_all_tabs(self):
        self._reload_tab(None,          count_lbl=self.all_table._count_lbl)
        self._reload_tab('IN',          count_lbl=self.in_table._count_lbl)
        self._reload_tab('OUT',         count_lbl=self.out_table._count_lbl)
        self._reload_tab('ADJUSTMENT',  count_lbl=self.adj_table._count_lbl)
        self._load_low_stock()

    def _build_low_stock_tab(self, tab):
        top = ctk.CTkFrame(tab, fg_color='transparent')
        top.pack(fill='x', pady=(8,4))
        ctk.CTkLabel(top, text='Products at or below minimum stock level',
                      font=('Segoe UI', 12), text_color=config.TEXT_MID).pack(side='left', padx=8)
        make_btn(top, '↻ Refresh', self._load_low_stock, width=100, height=30).pack(side='right', padx=8)

        cols = ('SKU','Product Name','Category','Current Qty','Min Stock','Shortage','Cost Price','Supplier')
        col_w = {'SKU':90,'Product Name':200,'Category':120,'Current Qty':90,
                  'Min Stock':80,'Shortage':80,'Cost Price':90,'Supplier':140}
        self.low_table = DataTable(tab, cols, col_w, height=20)
        self.low_table.pack(fill='both', expand=True, padx=4, pady=4)

    def _load_low_stock(self):
        products = self.db.get_products(low_stock_only=True)
        rows = [(p['sku'], p['name'], p.get('category_name',''), p['quantity'],
                  p['min_stock'], max(0, p['min_stock']-p['quantity']),
                  format_currency(p['cost_price']), p.get('supplier_name',''))
                for p in products]
        self.low_table.load_raw(rows)
        self.low_table.tree.tag_configure('danger', background='#FEE2E2')
        self.low_table.tree.tag_configure('low',    background='#FEF3C7')
        for i, p in enumerate(products):
            tag = 'danger' if p['quantity'] == 0 else 'low'
            self.low_table.tree.item(str(i), tags=(tag,))

    # ── Product search popup ─────────────────────────────────
    def _product_search_dialog(self, parent):
        result = [None]
        dlg = ctk.CTkToplevel(parent)
        dlg.title('Select Product')
        dlg.geometry('620x460')
        dlg.grab_set()
        ctk.CTkLabel(dlg, text='Search & Select Product',
                      font=('Segoe UI', 14, 'bold'), text_color=config.PRIMARY).pack(padx=20, pady=12)

        search_var = ctk.StringVar()
        ctk.CTkEntry(dlg, textvariable=search_var, placeholder_text='Type name or SKU...',
                      width=450, height=36, fg_color='white', border_color='#D1D5DB',
                      text_color=config.TEXT_DARK).pack(padx=20, pady=(0,8))

        cols = ('SKU','Name','Category','Stock','Unit','Sell Price')
        col_w = {'SKU':90,'Name':210,'Category':110,'Stock':65,'Unit':55,'Sell Price':90}
        table = DataTable(dlg, cols, col_w, height=11)
        table.pack(fill='both', expand=True, padx=12, pady=4)

        all_products = self.db.get_products()

        def load(*_):
            s = search_var.get().lower()
            filtered = [p for p in all_products
                         if s in (p['name']+p['sku']).lower()] if s else all_products
            table.load_raw([(p['sku'],p['name'],p.get('category_name',''),
                              p['quantity'],p.get('unit','pcs'),
                              format_currency(p['selling_price'])) for p in filtered])
            table._filtered = filtered

        search_var.trace_add('write', load)
        load()

        btn_row = ctk.CTkFrame(dlg, fg_color='transparent')
        btn_row.pack(pady=10)

        def select():
            vals = table.selected_values()
            if vals:
                result[0] = next((p for p in all_products if p['sku']==vals[0]), None)
                dlg.destroy()

        make_green_btn(btn_row, '✓ Select', select, width=120).pack(side='left', padx=8)
        make_btn(btn_row, 'Cancel', dlg.destroy, width=100).pack(side='left')
        table.bind_double(lambda e: select())
        dlg.wait_window()
        return result[0]

    # ── Buyer search popup ───────────────────────────────────
    def _buyer_search_dialog(self, parent):
        result = [None]
        dlg = ctk.CTkToplevel(parent)
        dlg.title('Select Buyer / Customer')
        dlg.geometry('580x420')
        dlg.grab_set()
        ctk.CTkLabel(dlg, text='Select Buyer / Customer',
                      font=('Segoe UI', 14, 'bold'), text_color=config.PRIMARY).pack(padx=20, pady=12)

        search_var = ctk.StringVar()
        ctk.CTkEntry(dlg, textvariable=search_var, placeholder_text='Search by name or phone...',
                      width=430, height=36, fg_color='white', border_color='#D1D5DB',
                      text_color=config.TEXT_DARK).pack(padx=20, pady=(0,8))

        cols = ('ID','Name','Phone','Email','Address')
        col_w = {'ID':40,'Name':200,'Phone':110,'Email':160,'Address':160}
        table = DataTable(dlg, cols, col_w, height=10)
        table.pack(fill='both', expand=True, padx=12, pady=4)

        all_buyers = self.db.get_buyers()

        def load(*_):
            s = search_var.get().lower()
            filtered = [b for b in all_buyers
                         if s in (b['name']+(b.get('phone') or '')).lower()] if s else all_buyers
            table.load_raw([(b['id'],b['name'],b.get('phone',''),
                              b.get('email',''),b.get('address','')) for b in filtered])

        search_var.trace_add('write', load)
        load()

        btn_row = ctk.CTkFrame(dlg, fg_color='transparent')
        btn_row.pack(pady=8)

        def select():
            vals = table.selected_values()
            if vals:
                result[0] = next((b for b in all_buyers if b['id']==vals[0]), None)
                dlg.destroy()

        make_green_btn(btn_row, '✓ Select', select, width=120).pack(side='left', padx=8)
        make_btn(btn_row, 'Cancel', dlg.destroy, width=100).pack(side='left')
        table.bind_double(lambda e: select())
        dlg.wait_window()
        return result[0]

    # ── Button handlers ──────────────────────────────────────
    def stock_in_dialog(self):   self._stock_dialog('IN')
    def stock_out_dialog(self):  self._stock_dialog('OUT')
    def return_dialog(self):     self._stock_dialog('RETURN')
    def adjust_dialog(self):     self._stock_dialog('ADJUSTMENT')

    # ── Main transaction dialog ──────────────────────────────
    def _stock_dialog(self, tx_type):
        META = {
            'IN':         ('📥 Stock In',        '#10B981'),
            'OUT':        ('📤 Stock Out',        '#EF4444'),
            'RETURN':     ('↩ Stock Return',      '#F59E0B'),
            'ADJUSTMENT': ('⚙ Stock Adjustment',  '#7C3AED'),
        }
        title_text, hdr_color = META[tx_type]

        dlg = ctk.CTkToplevel(self)
        dlg.title(title_text)
        dlg.geometry('580x580')
        dlg.resizable(False, False)
        dlg.grab_set()
        x = self.winfo_rootx() + self.winfo_width()//2 - 290
        y = max(30, self.winfo_rooty() + self.winfo_height()//2 - 290)
        dlg.geometry(f'580x580+{x}+{y}')

        # Header bar
        hdr = ctk.CTkFrame(dlg, fg_color=hdr_color, corner_radius=0, height=56)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=title_text, font=('Segoe UI', 16, 'bold'),
                      text_color='white').pack(side='left', padx=20, pady=14)

        scroll = ctk.CTkScrollableFrame(dlg, fg_color='#F8FAFC')
        scroll.pack(fill='both', expand=True)

        selected_product = [None]
        buyer_id_ref     = [None]

        # ── Product card ─────────────────────────────────────
        pc = ctk.CTkFrame(scroll, fg_color='white', corner_radius=10,
                           border_width=1, border_color='#E5E7EB')
        pc.pack(fill='x', padx=20, pady=(16,6))
        pc_row = ctk.CTkFrame(pc, fg_color='transparent')
        pc_row.pack(fill='x', padx=14, pady=10)

        ctk.CTkLabel(pc_row, text='Product *', font=('Segoe UI', 12, 'bold'),
                      text_color=config.TEXT_DARK, width=130, anchor='w').pack(side='left')
        prod_lbl = ctk.CTkLabel(pc_row, text='No product selected',
                                 font=('Segoe UI', 12), text_color='#9CA3AF')
        prod_lbl.pack(side='left', padx=8)

        def browse_prod():
            p = self._product_search_dialog(dlg)
            if p:
                selected_product[0] = p
                prod_lbl.configure(text=f"{p['name']}  [{p['sku']}]",
                                    text_color=config.PRIMARY)
                stock_lbl.configure(
                    text=f"  Current stock: {p['quantity']} {p.get('unit','pcs')}    "
                         f"Sell Price: {format_currency(p['selling_price'])}")
                price_e.delete(0, 'end')
                price_e.insert(0, str(p['selling_price']))

        make_btn(pc_row, '📦 Browse', browse_prod, width=100, height=32).pack(side='right')

        stock_lbl = ctk.CTkLabel(scroll, text='', font=('Segoe UI', 11), text_color=config.TEXT_MID)
        stock_lbl.pack(anchor='w', padx=20, pady=(0,4))

        # ── Reusable row builder ─────────────────────────────
        def entry_row(label, placeholder='', default=''):
            f = ctk.CTkFrame(scroll, fg_color='transparent')
            f.pack(fill='x', padx=20, pady=5)
            ctk.CTkLabel(f, text=label, font=('Segoe UI', 12, 'bold'),
                          text_color=config.TEXT_DARK, width=140, anchor='w').pack(side='left')
            e = ctk.CTkEntry(f, width=360, height=36, placeholder_text=placeholder,
                              fg_color='white', border_color='#D1D5DB',
                              text_color=config.TEXT_DARK, font=('Segoe UI', 12))
            e.insert(0, str(default))
            e.pack(side='left')
            return e

        qty_e   = entry_row('Quantity *', 'Enter quantity')
        price_e = entry_row('Unit Price (₹)', 'Unit price', '0')

        # ── Buyer card (OUT / RETURN only) ───────────────────
        if tx_type in ('OUT', 'RETURN'):
            bc = ctk.CTkFrame(scroll, fg_color='white', corner_radius=10,
                               border_width=1, border_color='#E5E7EB')
            bc.pack(fill='x', padx=20, pady=6)
            bc_row = ctk.CTkFrame(bc, fg_color='transparent')
            bc_row.pack(fill='x', padx=14, pady=10)

            ctk.CTkLabel(bc_row, text='Buyer / Customer', font=('Segoe UI', 12, 'bold'),
                          text_color=config.TEXT_DARK, width=140, anchor='w').pack(side='left')
            buyer_lbl = ctk.CTkLabel(bc_row, text='Select buyer (optional)',
                                      font=('Segoe UI', 12), text_color='#9CA3AF')
            buyer_lbl.pack(side='left', padx=8)

            def browse_buyer():
                b = self._buyer_search_dialog(dlg)
                if b:
                    buyer_id_ref[0] = b['id']
                    buyer_lbl.configure(
                        text=f"{b['name']}  {b.get('phone','')}",
                        text_color=config.PRIMARY)

            make_btn(bc_row, '👤 Browse', browse_buyer, width=100, height=32).pack(side='right')

        ref_e   = entry_row('Reference No',  'PO / Invoice number')
        notes_e = entry_row('Notes',         'Optional notes')

        newqty_e = None
        if tx_type == 'ADJUSTMENT':
            newqty_e = entry_row('New Total Qty *', 'Enter the corrected stock total')

        err_lbl = ctk.CTkLabel(scroll, text='', font=('Segoe UI', 11), text_color='#EF4444')
        err_lbl.pack(anchor='w', padx=20, pady=4)

        # ── Save button bar ──────────────────────────────────
        btn_bar = ctk.CTkFrame(dlg, fg_color='white', height=62)
        btn_bar.pack(fill='x', side='bottom')
        btn_bar.pack_propagate(False)

        def submit():
            p = selected_product[0]
            if not p:
                err_lbl.configure(text='⚠ Please select a product'); return
            try:
                qty   = int(float(qty_e.get()   or 0))
                price = float(price_e.get() or 0)
            except ValueError:
                err_lbl.configure(text='⚠ Invalid quantity or price'); return
            if qty <= 0:
                err_lbl.configure(text='⚠ Quantity must be > 0'); return
            if tx_type == 'OUT' and qty > p['quantity']:
                err_lbl.configure(text=f'⚠ Insufficient stock. Available: {p["quantity"]}'); return

            ref  = ref_e.get().strip() or f'{tx_type}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
            note = notes_e.get().strip()
            uid  = self.user['id']

            try:
                if tx_type == 'IN':
                    self.db.stock_in(p['id'], qty, price, ref, note, uid)
                elif tx_type == 'OUT':
                    self.db.stock_out(p['id'], qty, price, ref, note, uid, buyer_id_ref[0])
                elif tx_type == 'RETURN':
                    self.db.stock_in(p['id'], qty, price, ref, f'RETURN: {note}', uid)
                elif tx_type == 'ADJUSTMENT':
                    try:
                        new_qty = int(float(newqty_e.get() or 0))
                    except ValueError:
                        err_lbl.configure(text='⚠ Invalid new quantity'); return
                    self.db.stock_adjust(p['id'], new_qty, note, uid)

                self.db.log_action(uid, self.user['username'], f'STOCK_{tx_type}',
                                    'Inventory', f"{p['name']}: qty={qty}, ref={ref}")
                show_toast(self, f'✓ {title_text} recorded')
                self._load_all_tabs()
                dlg.destroy()
            except Exception as ex:
                err_lbl.configure(text=f'Error: {ex}')

        make_btn(btn_bar, f'✓ Save', submit, color=hdr_color, hover=hdr_color,
                  width=150, height=40).pack(side='right', padx=16, pady=10)
        make_btn(btn_bar, 'Cancel', dlg.destroy, width=100, height=40).pack(
            side='right', padx=4, pady=10)

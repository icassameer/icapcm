# ============================================================
#  ICA PMS — Products View  (Paginated — handles 50,000+)
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import (DataTable, make_btn, make_green_btn, make_danger_btn,
                            card_frame, show_toast, confirm_dialog, format_currency)

PAGE_SIZE = 100   # rows shown per page — fast even with 100,000 products


class ProductsView(ctk.CTkFrame):
    def __init__(self, parent, db, user, **kwargs):
        super().__init__(parent, fg_color=config.BG, **kwargs)
        self.db              = db
        self.user            = user
        self.is_admin        = user['role'] == config.ROLE_ADMIN
        self.selected_product = None
        self._current_page   = 0
        self._total_count    = 0
        self._search         = ''
        self._cat_id         = None
        self._low_stock_only = False
        self._search_after   = None   # debounce timer
        self._build()
        self.load_products()

    # ── UI BUILD ─────────────────────────────────────────────
    def _build(self):
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color='white', height=64)
        toolbar.pack(fill='x', pady=(0,2))
        toolbar.pack_propagate(False)
        ctk.CTkLabel(toolbar, text='📦  Product Management',
                      font=('Segoe UI', 18, 'bold'), text_color=config.PRIMARY).pack(
            side='left', padx=20, pady=16)

        btns = ctk.CTkFrame(toolbar, fg_color='transparent')
        btns.pack(side='right', padx=16, pady=12)
        if self.is_admin:
            make_danger_btn(btns, '🗑 Delete', self.delete_product, width=110).pack(side='right', padx=4)
        make_btn(btns, '✏ Edit', self.edit_product, width=100).pack(side='right', padx=4)
        make_green_btn(btns, '+ Add Product', self.add_product_dialog, width=130).pack(side='right', padx=4)

        # Filter bar
        fbar = ctk.CTkFrame(self, fg_color='white', height=54)
        fbar.pack(fill='x', pady=(0,2))
        fbar.pack_propagate(False)
        inner = ctk.CTkFrame(fbar, fg_color='transparent')
        inner.pack(side='left', padx=16, pady=8)

        # Search — debounced, DB-level
        ctk.CTkLabel(inner, text='🔍', font=('Segoe UI', 14)).pack(side='left', padx=(0,4))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add('write', self._on_search_type)
        ctk.CTkEntry(inner, textvariable=self._search_var,
                      placeholder_text='Search name, SKU or barcode...',
                      width=280, height=34, fg_color='white',
                      border_color='#D1D5DB', text_color=config.TEXT_DARK).pack(side='left', padx=(0,14))

        # Category filter
        ctk.CTkLabel(inner, text='Category:', font=('Segoe UI', 12),
                      text_color=config.TEXT_MID).pack(side='left')
        self._cat_var = ctk.StringVar(value='All')
        self._cat_combo = ctk.CTkComboBox(inner, variable=self._cat_var, width=170,
                                           command=self._on_filter_change,
                                           fg_color='white', border_color='#D1D5DB')
        self._cat_combo.pack(side='left', padx=(4,14))

        self._low_var = ctk.BooleanVar()
        ctk.CTkCheckBox(inner, text='Low Stock Only', variable=self._low_var,
                         fg_color=config.ACCENT, command=self._on_filter_change,
                         font=('Segoe UI', 12)).pack(side='left')

        # Count + page info
        self._info_lbl = ctk.CTkLabel(fbar, text='', font=('Segoe UI', 11),
                                       text_color=config.TEXT_MID)
        self._info_lbl.pack(side='right', padx=16)

        # Table
        tframe = ctk.CTkFrame(self, fg_color='white', corner_radius=12)
        tframe.pack(fill='both', expand=True, padx=16, pady=(4,0))

        cols = ('SKU','Name','Category','Supplier','Qty','Min Stk',
                 'Cost','Sell Price','Margin%','Status','Unit')
        col_w = {'SKU':90,'Name':200,'Category':110,'Supplier':120,
                  'Qty':60,'Min Stk':65,'Cost':85,'Sell Price':90,
                  'Margin%':68,'Status':88,'Unit':55}
        self.table = DataTable(tframe, cols, col_w, height=22)
        self.table.pack(fill='both', expand=True, padx=8, pady=(8,4))
        self.table.bind_double(lambda e: self.edit_product())
        self.table.bind_select(self._on_row_select)

        # ── Pagination bar ────────────────────────────────────
        pbar = ctk.CTkFrame(self, fg_color='white', height=44)
        pbar.pack(fill='x', pady=(0,0))
        pbar.pack_propagate(False)

        make_btn(pbar, '⏮ First',    self._go_first,    width=80,  height=30).pack(side='left', padx=(16,2), pady=7)
        make_btn(pbar, '◀ Prev',     self._go_prev,     width=80,  height=30).pack(side='left', padx=2,     pady=7)
        self._page_lbl = ctk.CTkLabel(pbar, text='', font=('Segoe UI', 12, 'bold'),
                                       text_color=config.PRIMARY, width=180)
        self._page_lbl.pack(side='left', padx=8)
        make_btn(pbar, 'Next ▶',     self._go_next,     width=80,  height=30).pack(side='left', padx=2,     pady=7)
        make_btn(pbar, 'Last ⏭',     self._go_last,     width=80,  height=30).pack(side='left', padx=2,     pady=7)

        # Page jump
        ctk.CTkLabel(pbar, text='Go to page:', font=('Segoe UI', 11),
                      text_color=config.TEXT_MID).pack(side='left', padx=(20,4))
        self._jump_var = ctk.StringVar()
        jump_e = ctk.CTkEntry(pbar, textvariable=self._jump_var, width=55, height=30,
                               fg_color='white', border_color='#D1D5DB',
                               text_color=config.TEXT_DARK)
        jump_e.pack(side='left')
        jump_e.bind('<Return>', self._go_jump)
        make_btn(pbar, 'Go', self._go_jump, width=45, height=30).pack(side='left', padx=4, pady=7)

        # Page size selector
        ctk.CTkLabel(pbar, text='Rows/page:', font=('Segoe UI', 11),
                      text_color=config.TEXT_MID).pack(side='right', padx=(0,4))
        self._page_size_var = ctk.StringVar(value=str(PAGE_SIZE))
        ctk.CTkComboBox(pbar, variable=self._page_size_var,
                         values=['50','100','200','500'],
                         width=80, height=30, fg_color='white',
                         border_color='#D1D5DB',
                         command=self._on_page_size_change).pack(side='right', padx=(0,16))

        self._refresh_categories()

    # ── Data loading ──────────────────────────────────────────
    def _refresh_categories(self):
        cats = ['All'] + [c['name'] for c in self.db.get_categories()]
        self._cat_combo.configure(values=cats)

    def load_products(self):
        search   = self._search
        cat_id   = self._cat_id
        low      = self._low_stock_only
        page_sz  = int(self._page_size_var.get() if hasattr(self, '_page_size_var') else PAGE_SIZE)
        offset   = self._current_page * page_sz

        # Count total (DB query — fast due to indexes)
        self._total_count = self.db.count_products(search, cat_id, low)
        total_pages = max(1, (self._total_count + page_sz - 1) // page_sz)

        # Clamp page
        if self._current_page >= total_pages:
            self._current_page = max(0, total_pages - 1)
            offset = self._current_page * page_sz

        # Fetch only this page (LIMIT/OFFSET — very fast)
        products = self.db.get_products(search, cat_id, low,
                                         limit=page_sz, offset=offset)

        # Build display rows
        rows = []
        for p in products:
            margin = 0.0
            if p['selling_price'] > 0 and p['cost_price'] > 0:
                margin = (p['selling_price'] - p['cost_price']) / p['selling_price'] * 100
            qty = p['quantity']
            status = '🚫 Out' if qty == 0 else ('⚠ Low' if qty <= p['min_stock'] else '✅ OK')
            rows.append((
                p['sku'], p['name'], p.get('category_name',''), p.get('supplier_name',''),
                qty, p['min_stock'],
                format_currency(p['cost_price']), format_currency(p['selling_price']),
                f"{margin:.1f}%", status, p.get('unit','pcs')
            ))

        self.table.load_raw(rows)

        # Row colouring
        for i, p in enumerate(products):
            tag = 'danger' if p['quantity']==0 else ('low' if p['quantity']<=p['min_stock'] else ('odd' if i%2 else 'even'))
            self.table.tree.item(str(i), tags=(tag,))
        self.table.tree.tag_configure('danger', background='#FEE2E2')
        self.table.tree.tag_configure('low',    background='#FEF3C7')

        # Update labels
        start = offset + 1 if self._total_count > 0 else 0
        end   = min(offset + page_sz, self._total_count)
        self._info_lbl.configure(
            text=f'Showing {start}–{end} of {self._total_count:,} products')
        self._page_lbl.configure(
            text=f'Page {self._current_page+1} of {total_pages}')
        self._products_cache = products

    # ── Search debounce (300ms) ───────────────────────────────
    def _on_search_type(self, *_):
        if self._search_after:
            self.after_cancel(self._search_after)
        self._search_after = self.after(300, self._apply_search)

    def _apply_search(self):
        self._search = self._search_var.get().strip()
        self._current_page = 0
        self.load_products()

    def _on_filter_change(self, *_):
        cat_name = self._cat_var.get()
        self._cat_id = None
        if cat_name != 'All':
            for c in self.db.get_categories():
                if c['name'] == cat_name:
                    self._cat_id = c['id']; break
        self._low_stock_only = self._low_var.get()
        self._current_page = 0
        self.load_products()

    def _on_page_size_change(self, *_):
        self._current_page = 0
        self.load_products()

    # ── Pagination controls ───────────────────────────────────
    def _total_pages(self):
        sz = int(self._page_size_var.get())
        return max(1, (self._total_count + sz - 1) // sz)

    def _go_first(self):
        self._current_page = 0; self.load_products()

    def _go_prev(self):
        if self._current_page > 0:
            self._current_page -= 1; self.load_products()

    def _go_next(self):
        if self._current_page < self._total_pages() - 1:
            self._current_page += 1; self.load_products()

    def _go_last(self):
        self._current_page = self._total_pages() - 1; self.load_products()

    def _go_jump(self, *_):
        try:
            pg = int(self._jump_var.get()) - 1
            pg = max(0, min(pg, self._total_pages()-1))
            self._current_page = pg
            self.load_products()
        except ValueError:
            pass

    # ── Row selection ─────────────────────────────────────────
    def _on_row_select(self, *_):
        vals = self.table.selected_values()
        if vals:
            self.selected_product = self.db.get_product_by_sku(vals[0])

    # ── CRUD actions ──────────────────────────────────────────
    def add_product_dialog(self):
        self._product_dialog()

    def edit_product(self):
        if not self.selected_product:
            messagebox.showinfo('Select', 'Please select a product first.'); return
        self._product_dialog(self.selected_product)

    def delete_product(self):
        if not self.is_admin:
            messagebox.showwarning('Access Denied', 'Only Admin can delete products.'); return
        if not self.selected_product:
            messagebox.showinfo('Select', 'Please select a product first.'); return
        if confirm_dialog(self, 'Delete Product',
                           f"Delete '{self.selected_product['name']}'?\nThis cannot be undone."):
            self.db.delete_product(self.selected_product['id'])
            self.db.log_action(self.user['id'], self.user['username'],
                                'DELETE_PRODUCT', 'Products',
                                f"Deleted: {self.selected_product['name']}")
            self.selected_product = None
            self.load_products()
            show_toast(self, '✓ Product deleted')

    # ── Add / Edit dialog ─────────────────────────────────────
    def _product_dialog(self, product=None):
        is_edit = product is not None
        dlg = ctk.CTkToplevel(self)
        dlg.title('Edit Product' if is_edit else 'Add New Product')
        dlg.geometry('680x680')
        dlg.resizable(False, False)
        dlg.grab_set()
        x = self.winfo_rootx() + self.winfo_width()//2 - 340
        y = max(20, self.winfo_rooty() + self.winfo_height()//2 - 340)
        dlg.geometry(f'680x680+{x}+{y}')

        hdr = ctk.CTkFrame(dlg, fg_color=config.PRIMARY, corner_radius=0, height=56)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text='✏ Edit Product' if is_edit else '+ Add New Product',
                      font=('Segoe UI', 16, 'bold'), text_color='white').pack(
            side='left', padx=20, pady=14)

        scroll = ctk.CTkScrollableFrame(dlg, fg_color='#F8FAFC')
        scroll.pack(fill='both', expand=True)

        def entry_row(label, default='', width=380):
            f = ctk.CTkFrame(scroll, fg_color='transparent')
            f.pack(fill='x', padx=24, pady=5)
            ctk.CTkLabel(f, text=label, font=('Segoe UI', 12, 'bold'),
                          text_color=config.TEXT_DARK, width=150, anchor='w').pack(side='left')
            e = ctk.CTkEntry(f, width=width, height=36, fg_color='white',
                              border_color='#D1D5DB', text_color=config.TEXT_DARK,
                              font=('Segoe UI', 12))
            e.insert(0, str(default) if default else '')
            e.pack(side='left')
            return e

        sku_e     = entry_row('SKU *',                product.get('sku','') if is_edit else self._gen_sku())
        name_e    = entry_row('Product Name *',        product.get('name','') if is_edit else '')
        barcode_e = entry_row('Barcode',               product.get('barcode','') if is_edit else '')
        desc_e    = entry_row('Description',           product.get('description','') if is_edit else '')

        # Category
        f_cat = ctk.CTkFrame(scroll, fg_color='transparent')
        f_cat.pack(fill='x', padx=24, pady=5)
        ctk.CTkLabel(f_cat, text='Category', font=('Segoe UI', 12, 'bold'),
                      text_color=config.TEXT_DARK, width=150, anchor='w').pack(side='left')
        cats = self.db.get_categories()
        cat_var = ctk.StringVar(value=product.get('category_name','') if is_edit else
                                 (cats[0]['name'] if cats else ''))
        ctk.CTkComboBox(f_cat, variable=cat_var, values=[c['name'] for c in cats],
                         width=380, fg_color='white', border_color='#D1D5DB').pack(side='left')

        # Supplier
        f_sup = ctk.CTkFrame(scroll, fg_color='transparent')
        f_sup.pack(fill='x', padx=24, pady=5)
        ctk.CTkLabel(f_sup, text='Supplier', font=('Segoe UI', 12, 'bold'),
                      text_color=config.TEXT_DARK, width=150, anchor='w').pack(side='left')
        sups = self.db.get_suppliers()
        sup_var = ctk.StringVar(value=product.get('supplier_name','') if is_edit else
                                 (sups[0]['name'] if sups else ''))
        ctk.CTkComboBox(f_sup, variable=sup_var, values=[s['name'] for s in sups],
                         width=380, fg_color='white', border_color='#D1D5DB').pack(side='left')

        cost_e    = entry_row('Cost Price (₹) *',   product.get('cost_price','') if is_edit else '')
        selling_e = entry_row('Selling Price (₹) *', product.get('selling_price','') if is_edit else '')
        qty_e     = entry_row('Opening Qty',         product.get('quantity','0') if is_edit else '0')
        min_e     = entry_row('Min Stock Level',     product.get('min_stock','10') if is_edit else '10')

        # Unit
        f_unit = ctk.CTkFrame(scroll, fg_color='transparent')
        f_unit.pack(fill='x', padx=24, pady=5)
        ctk.CTkLabel(f_unit, text='Unit', font=('Segoe UI', 12, 'bold'),
                      text_color=config.TEXT_DARK, width=150, anchor='w').pack(side='left')
        unit_var = ctk.StringVar(value=product.get('unit','pcs') if is_edit else 'pcs')
        ctk.CTkComboBox(f_unit, variable=unit_var,
                         values=['pcs','kg','g','ltr','ml','box','pack','set','roll','mtr'],
                         width=160, fg_color='white', border_color='#D1D5DB').pack(side='left')

        batch_e  = entry_row('Batch No',                   product.get('batch_no','') if is_edit else '')
        expiry_e = entry_row('Expiry Date (YYYY-MM-DD)',   product.get('expiry_date','') if is_edit else '')

        # Live margin display
        margin_lbl = ctk.CTkLabel(scroll, text='', font=('Segoe UI', 12),
                                   text_color=config.ACCENT)
        margin_lbl.pack(anchor='w', padx=24)

        def update_margin(*_):
            try:
                c = float(cost_e.get() or 0)
                s = float(selling_e.get() or 0)
                if s > 0 and c >= 0:
                    margin_lbl.configure(
                        text=f"  Margin: {((s-c)/s*100):.1f}%  |  Profit per unit: ₹{s-c:.2f}")
                else:
                    margin_lbl.configure(text='')
            except Exception:
                margin_lbl.configure(text='')

        cost_e.bind('<KeyRelease>', update_margin)
        selling_e.bind('<KeyRelease>', update_margin)

        err_lbl = ctk.CTkLabel(scroll, text='', font=('Segoe UI', 11),
                                text_color='#EF4444')
        err_lbl.pack(anchor='w', padx=24)

        # Footer buttons
        btn_bar = ctk.CTkFrame(dlg, fg_color='white', height=62)
        btn_bar.pack(fill='x', side='bottom')
        btn_bar.pack_propagate(False)

        def save():
            if not sku_e.get().strip():
                err_lbl.configure(text='⚠ SKU is required'); return
            if not name_e.get().strip():
                err_lbl.configure(text='⚠ Product name is required'); return
            try:
                cost = float(cost_e.get() or 0)
                sell = float(selling_e.get() or 0)
                qty  = int(float(qty_e.get() or 0))
                mins = int(float(min_e.get() or 10))
            except ValueError:
                err_lbl.configure(text='⚠ Invalid numeric values'); return

            cat_id = next((c['id'] for c in cats if c['name']==cat_var.get()), None)
            sup_id = next((s['id'] for s in sups if s['name']==sup_var.get()), None)

            data = dict(
                sku=sku_e.get().strip(), barcode=barcode_e.get().strip(),
                name=name_e.get().strip(), description=desc_e.get().strip(),
                category_id=cat_id, supplier_id=sup_id,
                cost_price=cost, selling_price=sell,
                quantity=qty, min_stock=mins,
                unit=unit_var.get(),
                batch_no=batch_e.get().strip(),
                expiry_date=expiry_e.get().strip()
            )
            try:
                if is_edit:
                    self.db.update_product(product['id'], data)
                    self.db.log_action(self.user['id'], self.user['username'],
                                       'UPDATE_PRODUCT','Products', f"Updated: {data['name']}")
                    show_toast(self, '✓ Product updated')
                else:
                    self.db.add_product(data)
                    self.db.log_action(self.user['id'], self.user['username'],
                                       'ADD_PRODUCT','Products', f"Added: {data['name']}")
                    show_toast(self, '✓ Product added')
                self.load_products()
                self._refresh_categories()
                dlg.destroy()
            except Exception as ex:
                err_lbl.configure(text=f'Error: {ex}')

        make_green_btn(btn_bar, '💾 Save', save, width=140, height=40).pack(
            side='right', padx=16, pady=10)
        make_btn(btn_bar, 'Cancel', dlg.destroy, width=110, height=40).pack(
            side='right', padx=4, pady=10)

        update_margin()

    def _gen_sku(self):
        import random
        count = self.db.get_product_count()
        rand  = random.randint(100, 999)
        sku   = f"SKU-{count+1:05d}-{rand}"
        while self.db.get_product_by_sku(sku):
            rand = random.randint(1000, 9999)
            sku  = f"SKU-{count+1:05d}-{rand}"
        return sku

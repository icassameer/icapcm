# ============================================================
#  ICA PMS — Suppliers & Categories View
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import (DataTable, make_btn, make_green_btn, make_danger_btn,
                            card_frame, show_toast, confirm_dialog)


class SuppliersView(ctk.CTkFrame):
    def __init__(self, parent, db, user, **kwargs):
        super().__init__(parent, fg_color=config.BG, **kwargs)
        self.db = db
        self.user = user
        self.is_admin = user['role'] == config.ROLE_ADMIN
        self._sups_cache = []
        self.selected_supplier = None
        self.selected_category = None
        self.selected_buyer = None
        self._build()
        self.load_suppliers()
        self.load_buyers()
        self.load_categories()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color='white', height=64, corner_radius=0)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text='🏭  Suppliers, Buyers & Categories',
                      font=('Segoe UI', 18, 'bold'), text_color=config.PRIMARY).pack(
            side='left', padx=20, pady=16)

        # Main tabs
        self.main_tabs = ctk.CTkTabview(
            self, fg_color='white',
            segmented_button_fg_color=config.PRIMARY,
            segmented_button_selected_color=config.ACCENT,
            segmented_button_selected_hover_color='#00B870',
            text_color='white'
        )
        self.main_tabs.pack(fill='both', expand=True, padx=16, pady=12)
        self.main_tabs.add('🏭 Suppliers')
        self.main_tabs.add('👤 Buyers / Customers')
        self.main_tabs.add('🏷 Categories')

        self._build_suppliers_tab(self.main_tabs.tab('🏭 Suppliers'))
        self._build_buyers_tab(self.main_tabs.tab('👤 Buyers / Customers'))
        self._build_categories_tab(self.main_tabs.tab('🏷 Categories'))

    def _build_suppliers_tab(self, tab):
        toolbar = ctk.CTkFrame(tab, fg_color='transparent')
        toolbar.pack(fill='x', pady=(8, 6))
        ctk.CTkLabel(toolbar, text='Manage your product suppliers',
                      font=('Segoe UI', 12), text_color=config.TEXT_MID).pack(side='left', padx=4)
        btn_row = ctk.CTkFrame(toolbar, fg_color='transparent')
        btn_row.pack(side='right')
        if self.is_admin:
            make_danger_btn(btn_row, '🗑 Delete', self.delete_supplier, width=100, height=34).pack(side='right', padx=4)
        make_btn(btn_row, '✏ Edit', self.edit_supplier, width=90, height=34).pack(side='right', padx=4)
        make_green_btn(btn_row, '+ Add Supplier', self.add_supplier, width=130, height=34).pack(side='right', padx=4)

        cols = ('ID','Name','Contact','Phone','Email','Address')
        col_w = {'ID':40,'Name':180,'Contact':130,'Phone':120,'Email':180,'Address':200}
        self.sup_table = DataTable(tab, cols, col_w, height=22)
        self.sup_table.pack(fill='both', expand=True, padx=4, pady=4)
        self.sup_table.bind_select(lambda e: self._on_sup_select())
        self.sup_table.bind_double(lambda e: self.edit_supplier())

    def _build_buyers_tab(self, tab):
        toolbar = ctk.CTkFrame(tab, fg_color='transparent')
        toolbar.pack(fill='x', pady=(8, 6))
        ctk.CTkLabel(toolbar, text='Manage buyers / customers for stock out transactions',
                      font=('Segoe UI', 12), text_color=config.TEXT_MID).pack(side='left', padx=4)
        btn_row = ctk.CTkFrame(toolbar, fg_color='transparent')
        btn_row.pack(side='right')
        if self.is_admin:
            make_danger_btn(btn_row, '🗑 Delete', self.delete_buyer, width=100, height=34).pack(side='right', padx=4)
        make_btn(btn_row, '✏ Edit', self.edit_buyer, width=90, height=34).pack(side='right', padx=4)
        make_green_btn(btn_row, '+ Add Buyer', self.add_buyer, width=120, height=34).pack(side='right', padx=4)

        cols = ('ID','Name','Contact','Phone','Email','Address')
        col_w = {'ID':40,'Name':180,'Contact':130,'Phone':120,'Email':180,'Address':200}
        self.buyer_table = DataTable(tab, cols, col_w, height=22)
        self.buyer_table.pack(fill='both', expand=True, padx=4, pady=4)
        self.buyer_table.bind_select(lambda e: self._on_buyer_select())
        self.buyer_table.bind_double(lambda e: self.edit_buyer())

    def _build_categories_tab(self, tab):
        toolbar = ctk.CTkFrame(tab, fg_color='transparent')
        toolbar.pack(fill='x', pady=(8, 6))
        ctk.CTkLabel(toolbar, text='Manage product categories',
                      font=('Segoe UI', 12), text_color=config.TEXT_MID).pack(side='left', padx=4)
        btn_row = ctk.CTkFrame(toolbar, fg_color='transparent')
        btn_row.pack(side='right')
        if self.is_admin:
            make_danger_btn(btn_row, '🗑 Delete', self.delete_category, width=100, height=34).pack(side='right', padx=4)
        make_green_btn(btn_row, '+ Add Category', self.add_category, width=140, height=34).pack(side='right', padx=4)

        cols = ('ID','Name','Description','Created')
        col_w = {'ID':50,'Name':200,'Description':300,'Created':130}
        self.cat_table = DataTable(tab, cols, col_w, height=22)
        self.cat_table.pack(fill='both', expand=True, padx=4, pady=4)
        self.cat_table.bind_select(lambda e: self._on_cat_select())

    def load_buyers(self):
        buyers = self.db.get_buyers()
        rows = [(b['id'], b['name'], b.get('contact',''), b.get('phone',''),
                  b.get('email',''), b.get('address','')) for b in buyers]
        self.buyer_table.load_raw(rows)
        self._buyers_cache = buyers

    def _on_buyer_select(self):
        vals = self.buyer_table.selected_values()
        if vals:
            self.selected_buyer = next((b for b in self._buyers_cache if b['id']==vals[0]), None)

    def add_buyer(self):
        self._buyer_dialog()

    def edit_buyer(self):
        if not self.selected_buyer:
            messagebox.showinfo('Select', 'Select a buyer first.'); return
        self._buyer_dialog(self.selected_buyer)

    def delete_buyer(self):
        if not self.selected_buyer:
            messagebox.showinfo('Select', 'Select a buyer first.'); return
        if confirm_dialog(self, 'Delete Buyer', f"Delete '{self.selected_buyer['name']}'?"):
            self.db.delete_buyer(self.selected_buyer['id'])
            self.selected_buyer = None
            self.load_buyers()
            show_toast(self, '✓ Buyer deleted')

    def _buyer_dialog(self, buyer=None):
        is_edit = buyer is not None
        dlg = ctk.CTkToplevel(self)
        dlg.title('Edit Buyer' if is_edit else 'Add Buyer')
        dlg.geometry('500x420')
        dlg.resizable(False, False)
        dlg.grab_set()
        hdr = ctk.CTkFrame(dlg, fg_color='#0891B2', height=52, corner_radius=0)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text='✏ Edit Buyer' if is_edit else '+ Add Buyer / Customer',
                      font=('Segoe UI', 14, 'bold'), text_color='white').pack(side='left', padx=16, pady=12)

        form = ctk.CTkFrame(dlg, fg_color='#F8FAFC')
        form.pack(fill='both', expand=True)

        def field(label, default=''):
            f = ctk.CTkFrame(form, fg_color='transparent')
            f.pack(fill='x', padx=20, pady=6)
            ctk.CTkLabel(f, text=label, font=('Segoe UI', 12, 'bold'),
                          text_color=config.TEXT_DARK, width=110, anchor='w').pack(side='left')
            e = ctk.CTkEntry(f, width=320, height=36, fg_color='white',
                              border_color='#D1D5DB', text_color=config.TEXT_DARK, font=('Segoe UI', 12))
            e.insert(0, str(default) if default else '')
            e.pack(side='left')
            return e

        name_e    = field('Name *',    buyer.get('name','') if is_edit else '')
        contact_e = field('Contact',   buyer.get('contact','') if is_edit else '')
        phone_e   = field('Phone',     buyer.get('phone','') if is_edit else '')
        email_e   = field('Email',     buyer.get('email','') if is_edit else '')
        addr_e    = field('Address',   buyer.get('address','') if is_edit else '')

        err = ctk.CTkLabel(form, text='', font=('Segoe UI', 11), text_color='#EF4444')
        err.pack(anchor='w', padx=20)

        btn_row = ctk.CTkFrame(dlg, fg_color='white', height=56)
        btn_row.pack(fill='x', side='bottom')
        btn_row.pack_propagate(False)

        def save():
            if not name_e.get().strip():
                err.configure(text='⚠ Name required'); return
            try:
                if is_edit:
                    self.db.update_buyer(buyer['id'], name_e.get().strip(),
                                          contact_e.get().strip(), phone_e.get().strip(),
                                          email_e.get().strip(), addr_e.get().strip())
                else:
                    self.db.add_buyer(name_e.get().strip(), contact_e.get().strip(),
                                       phone_e.get().strip(), email_e.get().strip(), addr_e.get().strip())
                self.load_buyers()
                show_toast(self, '✓ Buyer saved')
                dlg.destroy()
            except Exception as ex:
                err.configure(text=f'Error: {ex}')

        make_green_btn(btn_row, '💾 Save', save, width=120, height=38).pack(side='right', padx=12, pady=9)
        make_btn(btn_row, 'Cancel', dlg.destroy, width=90, height=38).pack(side='right', padx=4, pady=9)

    def load_suppliers(self):
        sups = self.db.get_suppliers()
        rows = [(s['id'], s['name'], s.get('contact',''), s.get('phone',''),
                  s.get('email',''), s.get('address','')) for s in sups]
        self.sup_table.load_raw(rows)
        self._sups_cache = sups

    def load_categories(self):
        from utils.helpers import format_date
        cats = self.db.get_categories()
        rows = [(c['id'], c['name'], c.get('description',''),
                  format_date(c.get('created_at',''))) for c in cats]
        self.cat_table.load_raw(rows)

    def _on_sup_select(self):
        vals = self.sup_table.selected_values()
        if vals:
            sup_id = vals[0]
            self.selected_supplier = next((s for s in self._sups_cache if s['id']==sup_id), None)

    def _on_cat_select(self):
        vals = self.cat_table.selected_values()
        if vals:
            self.selected_category = {'id': vals[0], 'name': vals[1]}

    # ── Supplier Actions ─────────────────────────────────────
    def add_supplier(self):
        self._supplier_dialog()

    def edit_supplier(self):
        if not self.selected_supplier:
            messagebox.showinfo('Select', 'Select a supplier first.'); return
        self._supplier_dialog(self.selected_supplier)

    def delete_supplier(self):
        if not self.selected_supplier:
            messagebox.showinfo('Select', 'Select a supplier first.'); return
        if confirm_dialog(self, 'Delete Supplier', f"Delete '{self.selected_supplier['name']}'?"):
            self.db.delete_supplier(self.selected_supplier['id'])
            self.selected_supplier = None
            self.load_suppliers()
            show_toast(self, '✓ Supplier deleted')

    def _supplier_dialog(self, supplier=None):
        is_edit = supplier is not None
        dlg = ctk.CTkToplevel(self)
        dlg.title('Edit Supplier' if is_edit else 'Add Supplier')
        dlg.geometry('500x440')
        dlg.resizable(False, False)
        dlg.grab_set()
        hdr = ctk.CTkFrame(dlg, fg_color=config.PRIMARY, height=52, corner_radius=0)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text='✏ Edit Supplier' if is_edit else '+ Add Supplier',
                      font=('Segoe UI', 14, 'bold'), text_color='white').pack(side='left', padx=16, pady=12)

        form = ctk.CTkFrame(dlg, fg_color='#F8FAFC')
        form.pack(fill='both', expand=True)

        def field(label, default=''):
            f = ctk.CTkFrame(form, fg_color='transparent')
            f.pack(fill='x', padx=20, pady=6)
            ctk.CTkLabel(f, text=label, font=('Segoe UI', 12, 'bold'),
                          text_color=config.TEXT_DARK, width=110, anchor='w').pack(side='left')
            e = ctk.CTkEntry(f, width=320, height=36, fg_color='white',
                              border_color='#D1D5DB', text_color=config.TEXT_DARK, font=('Segoe UI', 12))
            e.insert(0, str(default) if default else '')
            e.pack(side='left')
            return e

        name_e    = field('Name *', supplier.get('name','') if is_edit else '')
        contact_e = field('Contact', supplier.get('contact','') if is_edit else '')
        phone_e   = field('Phone', supplier.get('phone','') if is_edit else '')
        email_e   = field('Email', supplier.get('email','') if is_edit else '')
        addr_e    = field('Address', supplier.get('address','') if is_edit else '')

        err = ctk.CTkLabel(form, text='', font=('Segoe UI', 11), text_color='#EF4444')
        err.pack(anchor='w', padx=20)

        btn_row = ctk.CTkFrame(dlg, fg_color='white', height=56)
        btn_row.pack(fill='x', side='bottom')
        btn_row.pack_propagate(False)

        def save():
            if not name_e.get().strip():
                err.configure(text='⚠ Name required'); return
            try:
                if is_edit:
                    self.db.update_supplier(supplier['id'], name_e.get().strip(),
                                             contact_e.get().strip(), phone_e.get().strip(),
                                             email_e.get().strip(), addr_e.get().strip())
                else:
                    self.db.add_supplier(name_e.get().strip(), contact_e.get().strip(),
                                          phone_e.get().strip(), email_e.get().strip(), addr_e.get().strip())
                self.load_suppliers()
                show_toast(self, '✓ Supplier saved')
                dlg.destroy()
            except Exception as ex:
                err.configure(text=f'Error: {ex}')

        make_green_btn(btn_row, '💾 Save', save, width=120, height=38).pack(side='right', padx=12, pady=9)
        make_btn(btn_row, 'Cancel', dlg.destroy, width=90, height=38).pack(side='right', padx=4, pady=9)

    # ── Category Actions ─────────────────────────────────────
    def add_category(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title('Add Category')
        dlg.geometry('400x220')
        dlg.resizable(False, False)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text='Add New Category',
                      font=('Segoe UI', 14, 'bold'), text_color=config.PRIMARY).pack(pady=(20, 4))
        name_e = ctk.CTkEntry(dlg, placeholder_text='Category name *', width=320, height=38,
                               fg_color='white', border_color='#D1D5DB', text_color=config.TEXT_DARK)
        name_e.pack(padx=20, pady=8)
        desc_e = ctk.CTkEntry(dlg, placeholder_text='Description (optional)', width=320, height=38,
                               fg_color='white', border_color='#D1D5DB', text_color=config.TEXT_DARK)
        desc_e.pack(padx=20, pady=4)
        err = ctk.CTkLabel(dlg, text='', font=('Segoe UI', 11), text_color='#EF4444')
        err.pack()

        def save():
            if not name_e.get().strip():
                err.configure(text='⚠ Name required'); return
            try:
                self.db.add_category(name_e.get().strip(), desc_e.get().strip())
                self.load_categories()
                show_toast(self, '✓ Category added')
                dlg.destroy()
            except Exception as ex:
                err.configure(text=f'Error: {ex} (may already exist)')

        make_green_btn(dlg, '💾 Save', save, width=120, height=36).pack(pady=8)

    def delete_category(self):
        if not self.selected_category:
            messagebox.showinfo('Select', 'Select a category first.'); return
        if confirm_dialog(self, 'Delete Category', f"Delete '{self.selected_category['name']}'?"):
            self.db.delete_category(self.selected_category['id'])
            self.selected_category = None
            self.load_categories()
            show_toast(self, '✓ Category deleted')

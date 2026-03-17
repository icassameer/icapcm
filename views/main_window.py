# ============================================================
#  ICA PMS — Main Application Window
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import os, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import resource_path

NAV_ITEMS = [
    ('dashboard',  '📊  Dashboard'),
    ('products',   '📦  Products'),
    ('inventory',  '🏪  Inventory'),
    ('sales',      '💰  Sales'),
    ('suppliers',  '🏭  Suppliers'),
    ('reports',    '📈  Reports'),
    ('users',      '👥  Users'),
    ('backup',     '🛡  Backup & Restore'),
]
NAV_ITEMS_STORE = [
    ('dashboard',  '📊  Dashboard'),
    ('products',   '📦  Products'),
    ('inventory',  '🏪  Inventory'),
    ('sales',      '💰  Sales'),
    ('suppliers',  '🏭  Suppliers'),
    ('reports',    '📈  Reports'),
]


class MainWindow(ctk.CTk):
    def __init__(self, db, user, **kwargs):
        super().__init__()
        self.db               = db
        self.user             = user
        self.is_admin         = user['role'] == config.ROLE_ADMIN
        self.current_view_key = None
        self.current_view     = None
        self._nav_btns        = {}
        self._view_cache      = {}   # key → view widget (hide/show, not destroy/recreate)

        self.title(f"ICA PMS — {config.APP_FULL_NAME}")
        self.geometry("1280x800")
        self.minsize(1024, 600)
        self._center_window(1280, 800)
        self.configure(fg_color=config.BG)
        # Set ICA logo as window/taskbar icon
        try:
            icon_path = resource_path(os.path.join('assets', 'logo.ico'))
            self.iconbitmap(icon_path)
        except Exception:
            pass

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, lambda: self.navigate('dashboard'))

    def _center_window(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── UI BUILD ─────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar — fixed width, full height
        self.sidebar = ctk.CTkFrame(self, fg_color=config.SIDEBAR_BG,
                                     width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(2, weight=1)   # nav row expands
        self._build_sidebar()

        # Content
        self.content_frame = ctk.CTkFrame(self, fg_color=config.BG, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky='nsew')

    def _build_sidebar(self):
        sb = self.sidebar

        # ── Row 0: Logo ──────────────────────────────────────
        logo_frame = ctk.CTkFrame(sb, fg_color='#0F1A42', height=88, corner_radius=0)
        logo_frame.grid(row=0, column=0, sticky='ew')
        logo_frame.grid_propagate(False)
        logo_frame.grid_columnconfigure(0, weight=1)
        try:
            img = Image.open(resource_path(os.path.join('assets', 'logo.png')))
            img = img.resize((52, 40), Image.LANCZOS)
            self._logo_img = ctk.CTkImage(img, size=(52, 40))
            inner = ctk.CTkFrame(logo_frame, fg_color='transparent')
            inner.place(relx=0.5, rely=0.5, anchor='center')
            ctk.CTkLabel(inner, image=self._logo_img, text='').pack(side='left', padx=(0, 8))
            tf = ctk.CTkFrame(inner, fg_color='transparent')
            tf.pack(side='left')
            ctk.CTkLabel(tf, text='ICA PMS',
                          font=('Segoe UI', 15, 'bold'), text_color='white').pack(anchor='w')
            ctk.CTkLabel(tf, text='Management System',
                          font=('Segoe UI', 8), text_color='#7E90B4').pack(anchor='w')
        except Exception:
            ctk.CTkLabel(logo_frame, text='ICA PMS',
                          font=('Segoe UI', 17, 'bold'), text_color='white'
                          ).place(relx=0.5, rely=0.5, anchor='center')

        # ── Row 1: User card ─────────────────────────────────
        uf = ctk.CTkFrame(sb, fg_color='#1E2E5E', corner_radius=8)
        uf.grid(row=1, column=0, sticky='ew', padx=10, pady=(10, 0))
        ctk.CTkLabel(uf, text='👤', font=('Segoe UI', 18)).pack(side='left', padx=10, pady=8)
        ui = ctk.CTkFrame(uf, fg_color='transparent')
        ui.pack(side='left', pady=6)
        ctk.CTkLabel(ui, text=self.user['full_name'][:20],
                      font=('Segoe UI', 11, 'bold'), text_color='white').pack(anchor='w')
        ctk.CTkLabel(ui, text=self.user['role'], font=('Segoe UI', 9),
                      text_color=config.ACCENT if self.is_admin else '#7E90B4').pack(anchor='w')

        # ── Row 2: Nav buttons (grows with window) ───────────
        nav_outer = ctk.CTkFrame(sb, fg_color='transparent')
        nav_outer.grid(row=2, column=0, sticky='nsew', pady=(8, 0))
        nav_outer.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(nav_outer, height=1, fg_color='#2A3A6A').pack(fill='x', padx=12, pady=(0, 4))
        ctk.CTkLabel(nav_outer, text='NAVIGATION', font=('Segoe UI', 9, 'bold'),
                      text_color='#5A6A8A').pack(anchor='w', padx=16, pady=(0, 4))

        items = NAV_ITEMS if self.is_admin else NAV_ITEMS_STORE
        for key, label in items:
            btn = ctk.CTkButton(
                nav_outer, text=label, anchor='w',
                height=40, corner_radius=8,
                fg_color='transparent', hover_color=config.HOVER_NAV,
                text_color='#8899BB', font=('Segoe UI', 12),
                command=lambda k=key: self.navigate(k)
            )
            btn.pack(fill='x', padx=8, pady=1)
            self._nav_btns[key] = btn

        # ── Row 3: Bottom bar (fixed at bottom) ──────────────
        bottom = ctk.CTkFrame(sb, fg_color='transparent')
        bottom.grid(row=3, column=0, sticky='ew', padx=8, pady=(4, 8))

        ctk.CTkFrame(bottom, height=1, fg_color='#2A3A6A').pack(fill='x', pady=(0, 6))

        # Logout
        ctk.CTkButton(
            bottom, text='🚪  Logout', height=36, corner_radius=8,
            fg_color='#2A1A1A', hover_color='#4A1A1A',
            text_color='#FF6B6B', font=('Segoe UI', 12),
            command=self._logout
        ).pack(fill='x', pady=(0, 6))

        # WhatsApp
        wa = ctk.CTkFrame(bottom, fg_color='#1E2E5E', corner_radius=8)
        wa.pack(fill='x')
        ctk.CTkLabel(wa, text=f'📞 {config.SUPPORT_WHATSAPP}',
                      font=('Segoe UI', 10), text_color=config.ACCENT).pack(pady=(5, 0))
        ctk.CTkLabel(wa, text='WhatsApp Support',
                      font=('Segoe UI', 8), text_color='#5A6A8A').pack(pady=(0, 5))

        ctk.CTkLabel(bottom, text=f'v{config.APP_VERSION}',
                      font=('Segoe UI', 8), text_color='#3A4A6A').pack(pady=(4, 0))

        # Make sidebar rows respond to resize
        sb.grid_columnconfigure(0, weight=1)
        sb.grid_rowconfigure(2, weight=1)

    # ── Navigation ────────────────────────────────────────────
    def navigate(self, key):
        """Show cached view (instant) or create it first time."""
        # Highlight nav
        for k, btn in self._nav_btns.items():
            btn.configure(fg_color=config.SELECTED_NAV if k == key else 'transparent',
                           text_color='white' if k == key else '#8899BB')
        self.current_view_key = key

        # Hide current
        if self.current_view:
            try:
                self.current_view.pack_forget()
            except Exception:
                pass

        # Serve from cache if exists
        if key in self._view_cache:
            self.current_view = self._view_cache[key]
            self.current_view.pack(fill='both', expand=True)
            # Refresh data-heavy views so they stay current
            if hasattr(self.current_view, 'refresh'):
                self.current_view.refresh()
            elif hasattr(self.current_view, 'load_data'):
                self.current_view.load_data()
            return

        # First load — show spinner then build
        self._show_loading()
        self.after(10, lambda: self._build_view(key))

    def _show_loading(self):
        """Briefly show a loading indicator while view is building."""
        for w in self.content_frame.winfo_children():
            try: w.pack_forget()
            except: pass
        f = ctk.CTkFrame(self.content_frame, fg_color=config.BG)
        f.pack(fill='both', expand=True)
        ctk.CTkLabel(f, text='⏳  Loading...',
                      font=('Segoe UI', 14), text_color=config.TEXT_MID
                      ).place(relx=0.5, rely=0.5, anchor='center')
        self._loading_frame = f
        self.update_idletasks()

    def _build_view(self, key):
        try:
            self._loading_frame.destroy()
        except Exception:
            pass

        try:
            if key == 'dashboard':
                from views.dashboard import DashboardView as Cls
            elif key == 'products':
                from views.products import ProductsView as Cls
            elif key == 'inventory':
                from views.inventory import InventoryView as Cls
            elif key == 'sales':
                from views.sales import SalesView as Cls
            elif key == 'suppliers':
                from views.suppliers import SuppliersView as Cls
            elif key == 'reports':
                from views.reports import ReportsView as Cls
            elif key == 'users':
                from views.users import UsersView as Cls
            elif key == 'backup':
                from views.backup import BackupView as Cls
            else:
                return
            view = Cls(self.content_frame, self.db, self.user)
            self._view_cache[key] = view
            self.current_view = view
            view.pack(fill='both', expand=True)
        except Exception as e:
            ctk.CTkLabel(self.content_frame,
                          text=f'Error loading {key}: {e}',
                          text_color='red').pack(pady=40)

    def _logout(self):
        if messagebox.askyesno('Logout', 'Are you sure you want to logout?'):
            self.destroy()

    def _on_close(self):
        if messagebox.askyesno('Exit', 'Are you sure you want to exit ICA PMS?'):
            self.destroy()

# ============================================================
#  ICA PMS — Login Window
# ============================================================

import customtkinter as ctk
import tkinter as tk
from PIL import Image
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import resource_path


class LoginWindow(ctk.CTk):
    def __init__(self, db, on_login_success):
        super().__init__()
        self.db               = db
        self.on_login_success = on_login_success
        self.failed_attempts  = 0

        self.title("ICA PMS — Login")
        self.geometry("900x580")
        self.resizable(False, False)
        self.configure(fg_color=config.BG)
        # Set ICA logo as window/taskbar icon
        try:
            icon_path = resource_path(os.path.join('assets', 'logo.ico'))
            self.iconbitmap(icon_path)
        except Exception:
            pass
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"900x580+{(sw-900)//2}+{(sh-580)//2}")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Left — Brand panel ───────────────────────────────
        left = ctk.CTkFrame(self, fg_color=config.PRIMARY, corner_radius=0)
        left.grid(row=0, column=0, sticky='nsew')

        brand = ctk.CTkFrame(left, fg_color='transparent')
        brand.place(relx=0.5, rely=0.5, anchor='center')

        try:
            img = Image.open(resource_path(os.path.join('assets', 'logo.png')))
            img = img.resize((150, 112), Image.LANCZOS)
            self._logo = ctk.CTkImage(img, size=(150, 112))
            ctk.CTkLabel(brand, image=self._logo, text='').pack(pady=(0, 14))
        except Exception:
            ctk.CTkLabel(brand, text='ICA', font=('Segoe UI', 52, 'bold'),
                          text_color=config.ACCENT).pack(pady=(0, 8))

        ctk.CTkLabel(brand, text=config.APP_FULL_NAME,
                      font=('Segoe UI', 13, 'bold'), text_color='white',
                      wraplength=210, justify='center').pack(pady=(0, 8))
        ctk.CTkFrame(brand, height=2, width=160, fg_color=config.ACCENT).pack(pady=6)
        ctk.CTkLabel(brand, text='Product & Inventory\nManagement System',
                      font=('Segoe UI', 11), text_color='#B0BAD4',
                      justify='center').pack(pady=4)
        ctk.CTkLabel(brand, text=f'📞 WhatsApp: {config.SUPPORT_WHATSAPP}',
                      font=('Segoe UI', 10), text_color=config.ACCENT,
                      justify='center').pack(pady=(20, 0))

        # ── Right — Login form ───────────────────────────────
        right = ctk.CTkFrame(self, fg_color='white', corner_radius=0)
        right.grid(row=0, column=1, sticky='nsew')

        form = ctk.CTkFrame(right, fg_color='transparent')
        form.place(relx=0.5, rely=0.5, anchor='center')

        ctk.CTkLabel(form, text='Welcome Back!',
                      font=('Segoe UI', 26, 'bold'), text_color=config.PRIMARY).pack(anchor='w')
        ctk.CTkLabel(form, text='Sign in to your account',
                      font=('Segoe UI', 12), text_color=config.TEXT_MID).pack(anchor='w', pady=(4, 22))

        # Username
        ctk.CTkLabel(form, text='Username', font=('Segoe UI', 12, 'bold'),
                      text_color=config.TEXT_DARK).pack(anchor='w')
        self.username_entry = ctk.CTkEntry(
            form, placeholder_text='Enter your username',
            width=300, height=42, fg_color='#F8FAFC',
            border_color='#D1D5DB', text_color=config.TEXT_DARK,
            font=('Segoe UI', 13))
        self.username_entry.pack(anchor='w', pady=(4, 14))

        # Password
        ctk.CTkLabel(form, text='Password', font=('Segoe UI', 12, 'bold'),
                      text_color=config.TEXT_DARK).pack(anchor='w')
        pwd_row = ctk.CTkFrame(form, fg_color='transparent')
        pwd_row.pack(anchor='w', pady=(4, 6))
        self.password_entry = ctk.CTkEntry(
            pwd_row, placeholder_text='Enter your password',
            width=258, height=42, fg_color='#F8FAFC',
            border_color='#D1D5DB', text_color=config.TEXT_DARK,
            font=('Segoe UI', 13), show='•')
        self.password_entry.pack(side='left')
        self._show = False
        ctk.CTkButton(pwd_row, text='👁', width=36, height=42,
                       fg_color='#F8FAFC', hover_color='#E5E7EB',
                       text_color=config.TEXT_MID, border_color='#D1D5DB',
                       border_width=1, corner_radius=8,
                       command=self._toggle_pwd).pack(side='left', padx=(4, 0))

        self.err_lbl = ctk.CTkLabel(form, text='', font=('Segoe UI', 11),
                                     text_color='#EF4444')
        self.err_lbl.pack(anchor='w', pady=(2, 6))

        self.login_btn = ctk.CTkButton(
            form, text='Sign In', width=300, height=44, corner_radius=10,
            fg_color=config.PRIMARY, hover_color=config.HOVER_NAV,
            font=('Segoe UI', 14, 'bold'), command=self._do_login)
        self.login_btn.pack()

        ctk.CTkLabel(right, text=f'v{config.APP_VERSION}  •  © 2025 ICA',
                      font=('Segoe UI', 10), text_color=config.TEXT_LIGHT
                      ).place(relx=0.5, rely=0.97, anchor='s')

        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self._do_login())

    def _toggle_pwd(self):
        self._show = not self._show
        self.password_entry.configure(show='' if self._show else '•')

    def _do_login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get()
        if not u or not p:
            self.err_lbl.configure(text='⚠ Please enter username and password')
            return
        self.login_btn.configure(state='disabled', text='Signing in...')
        self.after(100, lambda: self._auth(u, p))

    def _auth(self, u, p):
        user = self.db.authenticate(u, p)
        if user:
            self.withdraw()
            self.on_login_success(user)
        else:
            self.failed_attempts += 1
            self.err_lbl.configure(
                text=f'✖ Invalid username or password (#{self.failed_attempts})')
            self.login_btn.configure(state='normal', text='Sign In')
            self.password_entry.delete(0, 'end')

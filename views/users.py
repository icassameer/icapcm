# ============================================================
#  ICA PMS — User Management View (Admin Only)
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import (DataTable, make_btn, make_green_btn, make_danger_btn,
                            card_frame, show_toast, confirm_dialog, format_date)


class UsersView(ctk.CTkFrame):
    def __init__(self, parent, db, user, **kwargs):
        super().__init__(parent, fg_color=config.BG, **kwargs)
        self.db = db
        self.user = user
        self.selected_user = None
        self._build()
        self.load_users()

    def _build(self):
        # ── Toolbar ─────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color='white', height=64)
        toolbar.pack(fill='x', pady=(0, 2))
        toolbar.pack_propagate(False)

        ctk.CTkLabel(toolbar, text='👥  User Management',
                      font=('Segoe UI', 18, 'bold'), text_color=config.PRIMARY).pack(
            side='left', padx=20, pady=16)

        btn_row = ctk.CTkFrame(toolbar, fg_color='transparent')
        btn_row.pack(side='right', padx=16, pady=12)

        make_danger_btn(btn_row, '🗑 Delete', self.delete_user, width=100).pack(side='right', padx=4)
        make_btn(btn_row, '🔑 Reset Pwd', self.reset_password, width=120).pack(side='right', padx=4)
        make_btn(btn_row, '✏ Edit', self.edit_user, width=90).pack(side='right', padx=4)
        make_green_btn(btn_row, '+ Add User', self.add_user, width=110).pack(side='right', padx=4)

        # ── Main content ─────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=16, pady=8)

        # Users table
        users_frame = card_frame(content)
        users_frame.pack(fill='both', expand=True)

        ctk.CTkLabel(users_frame, text='System Users',
                      font=('Segoe UI', 13, 'bold'), text_color=config.PRIMARY).pack(
            anchor='w', padx=16, pady=(12, 4))

        cols = ('ID', 'Username', 'Full Name', 'Role', 'Email', 'Phone', 'Status', 'Last Login', 'Created')
        col_w = {'ID':40,'Username':120,'Full Name':180,'Role':110,
                  'Email':180,'Phone':110,'Status':80,'Last Login':140,'Created':120}
        self.table = DataTable(users_frame, cols, col_w, height=12)
        self.table.pack(fill='both', expand=True, padx=8, pady=(4,8))
        self.table.bind_select(self._on_select)
        self.table.bind_double(lambda e: self.edit_user())

        # Login history
        hist_frame = card_frame(content)
        hist_frame.pack(fill='x', pady=(12, 0))

        ctk.CTkLabel(hist_frame, text='🔑 Recent Login History',
                      font=('Segoe UI', 13, 'bold'), text_color=config.PRIMARY).pack(
            anchor='w', padx=16, pady=(12, 4))

        hist_cols = ('Date/Time', 'Username', 'Full Name', 'Status')
        hist_w = {'Date/Time': 150, 'Username': 140, 'Full Name': 200, 'Status': 100}
        self.hist_table = DataTable(hist_frame, hist_cols, hist_w, height=7)
        self.hist_table.pack(fill='x', padx=8, pady=(4, 8))
        self.load_login_history()

    def load_users(self):
        users = self.db.get_all_users()
        rows = [(u['id'], u['username'], u['full_name'], u['role'],
                  u.get('email',''), u.get('phone',''),
                  '✅ Active' if u['is_active'] else '❌ Inactive',
                  format_date(u.get('last_login','')),
                  format_date(u.get('created_at',''))) for u in users]
        self.table.load_raw(rows)
        self._users_cache = users

    def load_login_history(self):
        data = self.db.get_login_history(50)
        rows = [(format_date(d.get('created_at','')), d.get('username',''),
                  d.get('full_name',''), d.get('status','')) for d in data]
        self.hist_table.load_raw(rows)
        for i, d in enumerate(data):
            tag = 'success' if d.get('status')=='SUCCESS' else 'failed'
            self.hist_table.tree.item(str(i), tags=(tag,))
        self.hist_table.tree.tag_configure('success', background='#F0FFF4')
        self.hist_table.tree.tag_configure('failed', background='#FFF5F5')

    def _on_select(self, *_):
        vals = self.table.selected_values()
        if vals:
            uid = vals[0]
            self.selected_user = self.db.get_user(uid)

    def add_user(self):
        self._user_dialog()

    def edit_user(self):
        if not self.selected_user:
            messagebox.showinfo('Select User', 'Please select a user first.')
            return
        self._user_dialog(self.selected_user)

    def delete_user(self):
        if not self.selected_user:
            messagebox.showinfo('Select User', 'Please select a user.'); return
        if self.selected_user['id'] == self.user['id']:
            messagebox.showwarning('Error', 'You cannot delete your own account.'); return
        if confirm_dialog(self, 'Delete User',
                          f"Delete user '{self.selected_user['username']}'?"):
            self.db.delete_user(self.selected_user['id'])
            self.db.log_action(self.user['id'], self.user['username'],
                                'DELETE_USER', 'Users',
                                f"Deleted user: {self.selected_user['username']}")
            self.selected_user = None
            self.load_users()
            show_toast(self, '✓ User deleted')

    def reset_password(self):
        if not self.selected_user:
            messagebox.showinfo('Select User', 'Please select a user.'); return
        if messagebox.askyesno('Reset Password',
                                f"Reset password for '{self.selected_user['username']}' to '{config.DEFAULT_RESET_PASSWORD}'?"):
            self.db.reset_password(self.selected_user['id'], config.DEFAULT_RESET_PASSWORD)
            self.db.log_action(self.user['id'], self.user['username'],
                                'RESET_PASSWORD', 'Users',
                                f"Reset password for: {self.selected_user['username']}")
            show_toast(self, f"✓ Password reset to '{config.DEFAULT_RESET_PASSWORD}'")

    def _user_dialog(self, user=None):
        is_edit = user is not None
        dlg = ctk.CTkToplevel(self)
        dlg.title('Edit User' if is_edit else 'Add New User')
        dlg.geometry('520x560')
        dlg.resizable(False, False)
        dlg.grab_set()
        # Center
        x = self.winfo_rootx() + self.winfo_width()//2 - 260
        y = self.winfo_rooty() + self.winfo_height()//2 - 280
        dlg.geometry(f'520x560+{x}+{y}')

        # Header
        hdr = ctk.CTkFrame(dlg, fg_color=config.PRIMARY, corner_radius=0, height=56)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text='✏ Edit User' if is_edit else '+ Add New User',
                      font=('Segoe UI', 16, 'bold'), text_color='white').pack(
            side='left', padx=20, pady=14)

        form = ctk.CTkScrollableFrame(dlg, fg_color='#F8FAFC')
        form.pack(fill='both', expand=True)

        def field(label, default='', show=''):
            f = ctk.CTkFrame(form, fg_color='transparent')
            f.pack(fill='x', padx=24, pady=8)
            ctk.CTkLabel(f, text=label, font=('Segoe UI', 12, 'bold'),
                          text_color=config.TEXT_DARK, width=130, anchor='w').pack(side='left')
            e = ctk.CTkEntry(f, width=300, height=38, fg_color='white',
                              border_color='#D1D5DB', text_color=config.TEXT_DARK,
                              font=('Segoe UI', 12), show=show)
            e.insert(0, str(default) if default else '')
            e.pack(side='left')
            return e

        username_e  = field('Username *', user.get('username','') if is_edit else '')
        fullname_e  = field('Full Name *', user.get('full_name','') if is_edit else '')
        email_e     = field('Email', user.get('email','') if is_edit else '')
        phone_e     = field('Phone', user.get('phone','') if is_edit else '')

        # Role
        f_role = ctk.CTkFrame(form, fg_color='transparent')
        f_role.pack(fill='x', padx=24, pady=8)
        ctk.CTkLabel(f_role, text='Role *', font=('Segoe UI', 12, 'bold'),
                      text_color=config.TEXT_DARK, width=130, anchor='w').pack(side='left')
        role_var = ctk.StringVar(value=user.get('role', config.ROLE_STOREKEEPER) if is_edit else config.ROLE_STOREKEEPER)
        ctk.CTkComboBox(f_role, variable=role_var,
                         values=[config.ROLE_ADMIN, config.ROLE_STOREKEEPER],
                         width=300, fg_color='white', border_color='#D1D5DB').pack(side='left')

        # Active status
        f_active = ctk.CTkFrame(form, fg_color='transparent')
        f_active.pack(fill='x', padx=24, pady=8)
        ctk.CTkLabel(f_active, text='Status', font=('Segoe UI', 12, 'bold'),
                      text_color=config.TEXT_DARK, width=130, anchor='w').pack(side='left')
        active_var = ctk.BooleanVar(value=bool(user.get('is_active', 1)) if is_edit else True)
        ctk.CTkSwitch(f_active, text='Active', variable=active_var,
                       fg_color='#D1D5DB', progress_color=config.ACCENT).pack(side='left')

        # Password (only for new users)
        if not is_edit:
            pwd_e    = field('Password *', show='•')
            cpwd_e   = field('Confirm Pwd *', show='•')
        else:
            pwd_e = cpwd_e = None

        err_lbl = ctk.CTkLabel(form, text='', font=('Segoe UI', 11), text_color='#EF4444')
        err_lbl.pack(anchor='w', padx=24)

        # Buttons
        btn_frame = ctk.CTkFrame(dlg, fg_color='white', height=62)
        btn_frame.pack(fill='x', side='bottom')
        btn_frame.pack_propagate(False)

        def save():
            uname = username_e.get().strip()
            fname = fullname_e.get().strip()
            if not uname or not fname:
                err_lbl.configure(text='⚠ Username and Full Name are required'); return

            if not is_edit:
                pwd = pwd_e.get()
                cpwd = cpwd_e.get()
                if not pwd:
                    err_lbl.configure(text='⚠ Password is required'); return
                if pwd != cpwd:
                    err_lbl.configure(text='⚠ Passwords do not match'); return

            try:
                if is_edit:
                    self.db.update_user(user['id'], fname, role_var.get(),
                                         email_e.get().strip(), phone_e.get().strip(),
                                         int(active_var.get()))
                    self.db.log_action(self.user['id'], self.user['username'],
                                       'UPDATE_USER', 'Users', f"Updated: {uname}")
                    show_toast(self, '✓ User updated')
                else:
                    self.db.create_user(uname, pwd_e.get(), fname, role_var.get(),
                                         email_e.get().strip(), phone_e.get().strip())
                    self.db.log_action(self.user['id'], self.user['username'],
                                       'CREATE_USER', 'Users', f"Created: {uname}")
                    show_toast(self, '✓ User created')
                self.load_users()
                dlg.destroy()
            except Exception as ex:
                err_lbl.configure(text=f'Error: {ex} (Username may already exist)')

        make_green_btn(btn_frame, '💾 Save', save, width=130, height=40).pack(
            side='right', padx=16, pady=10)
        make_btn(btn_frame, 'Cancel', dlg.destroy, width=100, height=40).pack(
            side='right', padx=4, pady=10)

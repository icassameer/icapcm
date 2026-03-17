# ============================================================
#  ICA PMS — Backup & Restore View
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os, sys, datetime, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import make_btn, make_green_btn, make_danger_btn, card_frame, show_toast


class BackupView(ctk.CTkFrame):
    def __init__(self, parent, db, user, **kwargs):
        super().__init__(parent, fg_color=config.BG, **kwargs)
        self.db = db
        self.user = user
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color='white', height=64, corner_radius=0)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text='🛡  Backup & Restore',
                      font=('Segoe UI', 18, 'bold'), text_color=config.PRIMARY).pack(
            side='left', padx=20, pady=16)

        scroll = ctk.CTkScrollableFrame(self, fg_color=config.BG)
        scroll.pack(fill='both', expand=True, padx=20, pady=16)

        # ── Backup Card ──────────────────────────────────────
        backup_card = card_frame(scroll)
        backup_card.pack(fill='x', pady=(0, 16))

        inner = ctk.CTkFrame(backup_card, fg_color='transparent')
        inner.pack(fill='x', padx=24, pady=20)

        # Icon + title
        ctk.CTkLabel(inner, text='💾  Create Backup',
                      font=('Segoe UI', 16, 'bold'), text_color=config.PRIMARY).pack(anchor='w')
        ctk.CTkLabel(inner, text='Create a full backup of your database. Store it in a safe location.',
                      font=('Segoe UI', 12), text_color=config.TEXT_MID).pack(anchor='w', pady=(4, 16))

        # DB info
        db_path = self.db.db_path
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        info_frame = ctk.CTkFrame(inner, fg_color='#F0F4FF', corner_radius=8)
        info_frame.pack(fill='x', pady=(0, 16))
        info_inner = ctk.CTkFrame(info_frame, fg_color='transparent')
        info_inner.pack(padx=16, pady=12)
        ctk.CTkLabel(info_inner, text=f'📁 Database Path:  {db_path}',
                      font=('Segoe UI', 11), text_color=config.TEXT_DARK).pack(anchor='w')
        ctk.CTkLabel(info_inner, text=f'📦 Database Size:  {db_size/1024:.1f} KB',
                      font=('Segoe UI', 11), text_color=config.TEXT_DARK).pack(anchor='w', pady=4)
        ctk.CTkLabel(info_inner, text=f'🕒 Current Time:   {datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")}',
                      font=('Segoe UI', 11), text_color=config.TEXT_DARK).pack(anchor='w')

        self.backup_status = ctk.CTkLabel(inner, text='', font=('Segoe UI', 12), text_color=config.ACCENT)
        self.backup_status.pack(anchor='w', pady=8)

        btn_row = ctk.CTkFrame(inner, fg_color='transparent')
        btn_row.pack(anchor='w')

        make_green_btn(btn_row, '💾 Backup to File', self.do_backup, width=160, height=42).pack(
            side='left', padx=(0, 12))
        make_btn(btn_row, '📂 Quick Backup', self.quick_backup, width=150, height=42).pack(side='left')

        # ── Restore Card ─────────────────────────────────────
        restore_card = card_frame(scroll)
        restore_card.pack(fill='x', pady=(0, 16))

        inner2 = ctk.CTkFrame(restore_card, fg_color='transparent')
        inner2.pack(fill='x', padx=24, pady=20)

        ctk.CTkLabel(inner2, text='🔄  Restore Database',
                      font=('Segoe UI', 16, 'bold'), text_color=config.PRIMARY).pack(anchor='w')
        ctk.CTkLabel(inner2,
                      text='⚠ Warning: Restoring will replace your current database. All unsaved data will be lost.',
                      font=('Segoe UI', 12), text_color='#F59E0B').pack(anchor='w', pady=(4, 16))

        self.restore_status = ctk.CTkLabel(inner2, text='', font=('Segoe UI', 12), text_color='#EF4444')
        self.restore_status.pack(anchor='w', pady=4)

        make_danger_btn(inner2, '🔄 Restore from Backup', self.do_restore, width=200, height=42).pack(
            anchor='w')

        # ── Backup Schedule Card ─────────────────────────────
        sched_card = card_frame(scroll)
        sched_card.pack(fill='x', pady=(0, 16))

        inner3 = ctk.CTkFrame(sched_card, fg_color='transparent')
        inner3.pack(fill='x', padx=24, pady=20)

        ctk.CTkLabel(inner3, text='⏰  Backup Recommendations',
                      font=('Segoe UI', 16, 'bold'), text_color=config.PRIMARY).pack(anchor='w')

        tips = [
            '✅  Create a backup at the start and end of every business day',
            '✅  Store backups on an external drive or USB stick',
            '✅  Keep at least 7 days of backup history',
            '✅  Test restores periodically to ensure backups are valid',
            '✅  Name backups with dates: ICA_Backup_2025-01-15.db',
        ]
        for tip in tips:
            ctk.CTkLabel(inner3, text=tip, font=('Segoe UI', 12),
                          text_color=config.TEXT_DARK).pack(anchor='w', pady=3)

        # ── Database Stats Card ───────────────────────────────
        stats_card = card_frame(scroll)
        stats_card.pack(fill='x', pady=(0, 16))

        inner4 = ctk.CTkFrame(stats_card, fg_color='transparent')
        inner4.pack(fill='x', padx=24, pady=20)

        ctk.CTkLabel(inner4, text='📊  Database Statistics',
                      font=('Segoe UI', 16, 'bold'), text_color=config.PRIMARY).pack(anchor='w', pady=(0, 12))

        stats = self.db.get_dashboard_stats()
        stat_items = [
            ('Total Products', stats['total_products']),
            ('Total Categories', stats['total_categories']),
            ('Total Suppliers', stats['total_suppliers']),
            ('Total Users', stats['total_users']),
        ]

        stats_row = ctk.CTkFrame(inner4, fg_color='transparent')
        stats_row.pack(anchor='w')
        for label, val in stat_items:
            f = ctk.CTkFrame(stats_row, fg_color='#F0F4FF', corner_radius=8, width=140, height=70)
            f.pack(side='left', padx=8)
            f.pack_propagate(False)
            ctk.CTkLabel(f, text=str(val), font=('Segoe UI', 24, 'bold'),
                          text_color=config.PRIMARY).pack(pady=(8, 0))
            ctk.CTkLabel(f, text=label, font=('Segoe UI', 10),
                          text_color=config.TEXT_MID).pack()

    def do_backup(self):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f'ICA_Backup_{timestamp}.db'
        path = filedialog.asksaveasfilename(
            defaultextension='.db',
            filetypes=[('ICA Database Backup', '*.db'), ('All Files', '*.*')],
            initialfile=default_name,
            title='Save Backup As')
        if path:
            try:
                self.db.backup_database(path)
                self.backup_status.configure(
                    text=f'✅ Backup saved: {os.path.basename(path)}',
                    text_color=config.ACCENT)
                self.db.log_action(self.user['id'], self.user['username'],
                                    'BACKUP', 'System', f'Backup saved to: {path}')
                show_toast(self, '✓ Backup created successfully')
            except Exception as e:
                self.backup_status.configure(
                    text=f'❌ Backup failed: {e}', text_color='#EF4444')

    def quick_backup(self):
        """Auto-save backup to app directory."""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(os.path.dirname(self.db.db_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            path = os.path.join(backup_dir, f'ICA_QuickBackup_{timestamp}.db')
            self.db.backup_database(path)
            self.backup_status.configure(
                text=f'✅ Quick backup saved to backups folder',
                text_color=config.ACCENT)
            show_toast(self, '✓ Quick backup saved')
        except Exception as e:
            self.backup_status.configure(text=f'❌ Failed: {e}', text_color='#EF4444')

    def do_restore(self):
        if not messagebox.askyesno('Confirm Restore',
                                    '⚠ WARNING!\n\nThis will replace your entire database.\n'
                                    'All current data will be lost.\n\nAre you absolutely sure?',
                                    icon='warning'):
            return

        path = filedialog.askopenfilename(
            filetypes=[('ICA Database', '*.db'), ('All Files', '*.*')],
            title='Select Backup File to Restore')
        if path:
            try:
                self.db.restore_database(path)
                self.restore_status.configure(
                    text=f'✅ Database restored from: {os.path.basename(path)}',
                    text_color=config.ACCENT)
                show_toast(self, '✓ Database restored. Please restart the application.')
                messagebox.showinfo('Restore Complete',
                                     'Database restored successfully.\n\nPlease restart the application.')
            except Exception as e:
                self.restore_status.configure(
                    text=f'❌ Restore failed: {e}', text_color='#EF4444')

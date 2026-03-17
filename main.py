#!/usr/bin/env python3
# ============================================================
#  ICA PMS — Main Entry Point
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Silence CustomTkinter focus/animation errors on Windows ──
import tkinter as tk, tkinter.ttk as ttk

_orig_focus_set = tk.BaseWidget.focus_set
def _safe_focus_set(self, *a, **kw):
    try: _orig_focus_set(self, *a, **kw)
    except Exception: pass
tk.BaseWidget.focus_set = _safe_focus_set

_orig_misc_focus = tk.Misc.focus
def _safe_misc_focus(self, *a, **kw):
    try: return _orig_misc_focus(self, *a, **kw)
    except Exception: pass
tk.Misc.focus = _safe_misc_focus

_orig_ttk_focus = ttk.Treeview.focus
def _safe_ttk_focus(self, item=None):
    try: return _orig_ttk_focus(self, item)
    except Exception: return ''
ttk.Treeview.focus = _safe_ttk_focus

# Silence ALL background Tk callback errors
tk.Tk.report_callback_exception = lambda self, exc, val, tb: None
# ─────────────────────────────────────────────────────────────

import customtkinter as ctk
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

from database.db_manager import DatabaseManager
from auth.login_window import LoginWindow


def main():
    db = DatabaseManager()

    def on_login_success(user):
        from views.main_window import MainWindow
        app = MainWindow(db, user)
        app.report_callback_exception = lambda e, v, tb: None
        app.mainloop()

    login = LoginWindow(db, on_login_success)
    login.report_callback_exception = lambda e, v, tb: None
    login.mainloop()


if __name__ == '__main__':
    main()

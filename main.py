#!/usr/bin/env python3
# ============================================================
#  ICA PMS — Main Entry Point
# ============================================================
from utils.logger import setup_logger, log_error
setup_logger()

import sys

def handle_exception(exc_type, exc_value, exc_traceback):
    log_error(f"[Main/unhandled_exception] {exc_type.__name__} | error={exc_value}")

sys.excepthook = handle_exception

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Silence CustomTkinter focus/animation errors on Windows ──
import tkinter as tk, tkinter.ttk as ttk

_orig_focus_set = tk.BaseWidget.focus_set
def _safe_focus_set(self, *a, **kw):
    try:
        _orig_focus_set(self, *a, **kw)
    except Exception as e:
        log_error(f"[UI/focus_set] Failed to set focus | widget={type(self).__name__} | error={e}")
tk.BaseWidget.focus_set = _safe_focus_set

_orig_misc_focus = tk.Misc.focus
def _safe_misc_focus(self, *a, **kw):
    try:
        return _orig_misc_focus(self, *a, **kw)
    except Exception as e:
        log_error(f"[UI/misc_focus] Failed to get focus | widget={type(self).__name__} | error={e}")
        return None
tk.Misc.focus = _safe_misc_focus

_orig_ttk_focus = ttk.Treeview.focus
def _safe_ttk_focus(self, item=None):
    try:
        return _orig_ttk_focus(self, item)
    except Exception as e:
        log_error(f"[UI/treeview_focus] Failed to access tree focus | item={item} | error={e}")
        return ''
ttk.Treeview.focus = _safe_ttk_focus

# Silence ALL background Tk callback errors
def tk_exception_logger(self, exc, val, tb):
    exc_name = exc.__name__ if hasattr(exc, "__name__") else str(exc)
    log_error(f"[Tkinter/callback] callback crashed | exception={exc_name} | error={val}")

tk.Tk.report_callback_exception = tk_exception_logger
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
        login.report_callback_exception = lambda e, v, tb: log_error(
    f"[LoginWindow/callback] UI callback failed | exception={e.__name__ if hasattr(e, '__name__') else e} | error={v}"
)
        app.mainloop()

    login = LoginWindow(db, on_login_success)
    login.report_callback_exception = lambda e, v, tb: log_error(
    f"[LoginWindow/callback] UI callback failed | exception={e.__name__ if hasattr(e, '__name__') else e} | error={v}"
)
    login.mainloop()


if __name__ == '__main__':
    main()

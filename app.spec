# ============================================================
#  ICA PMS — PyInstaller build spec
#  Do NOT run directly. Use BUILD_DEMO.bat or BUILD_FULL.bat
# ============================================================
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

EXE_NAME = os.environ.get("ICA_EXE_NAME", "ICA_PMS")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("assets/logo.png", "assets"),
        ("config.py",       "."),
    ] + collect_data_files("customtkinter"),
    hiddenimports=[
        "customtkinter",
        "PIL", "PIL._tkinter_finder",
        "matplotlib", "matplotlib.backends.backend_tkagg",
        "openpyxl",
        "reportlab", "reportlab.platypus",
        "sqlite3",
    ] + collect_submodules("customtkinter"),
    hookspath=[],
    runtime_hooks=[],
    excludes=["numpy", "scipy", "pandas", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name=EXE_NAME,
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon="assets/logo.ico",
)

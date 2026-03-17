# Called by build scripts to switch edition in config.py
# Usage:  python _set_edition.py DEMO   or   python _set_edition.py FULL
import sys

edition = sys.argv[1].upper() if len(sys.argv) > 1 else "FULL"
if edition not in ("DEMO", "FULL"):
    print("Usage: python _set_edition.py DEMO|FULL")
    sys.exit(1)

content = open("config.py", encoding="utf-8").read()
if 'APP_EDITION      = "DEMO"' in content:
    content = content.replace('APP_EDITION      = "DEMO"', f'APP_EDITION      = "{edition}"')
elif 'APP_EDITION      = "FULL"' in content:
    content = content.replace('APP_EDITION      = "FULL"', f'APP_EDITION      = "{edition}"')
else:
    print("ERROR: APP_EDITION line not found in config.py")
    sys.exit(1)

open("config.py", "w", encoding="utf-8").write(content)
print(f"   config.py  ->  APP_EDITION = {edition}")

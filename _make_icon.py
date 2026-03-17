# Converts assets/logo.png -> assets/logo.ico for PyInstaller
try:
    from PIL import Image
    img = Image.open("assets/logo.png")
    img.save("assets/logo.ico", format="ICO",
             sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    print("   assets/logo.ico  ->  created")
except Exception as e:
    print(f"   Icon skipped (non-fatal): {e}")

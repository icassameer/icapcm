import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from utils.license_manager import get_machine_id, generate_signature

OUTPUT_DIR = "license"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "license.json")


def main():
    customer_name = input("Customer name: ").strip()
    license_type = input("License type (Basic/Standard/Professional): ").strip().title() or "Standard"
    expiry_date = input("Expiry date (YYYY-MM-DD): ").strip()
    machine_id = input("Machine ID (leave blank for this PC): ").strip()

    if not machine_id:
        machine_id = get_machine_id()

    data = {
        "customer_name": customer_name,
        "license_type": license_type,
        "expiry_date": expiry_date,
        "machine_id": machine_id,
    }

    data["signature"] = generate_signature(data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"License created: {OUTPUT_FILE}")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
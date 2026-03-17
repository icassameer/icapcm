import os
import json
import hmac
import uuid
import socket
import hashlib
from datetime import datetime

LICENSE_DIR = "license"
LICENSE_FILE = os.path.join(LICENSE_DIR, "license.json")

SECRET_KEY = b"CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY_12345"


def get_machine_id():
    raw = f"{socket.gethostname()}-{uuid.getnode()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _build_payload(data):
    payload = {
        "customer_name": data["customer_name"],
        "license_type": data["license_type"],
        "expiry_date": data["expiry_date"],
        "machine_id": data["machine_id"],
    }
    return json.dumps(payload, sort_keys=True).encode()


def generate_signature(data):
    payload = _build_payload(data)
    return hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()


def load_license():
    if not os.path.exists(LICENSE_FILE):
        return None
    with open(LICENSE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_license():
    data = load_license()
    if not data:
        return False, "License file not found"

    required_fields = [
        "customer_name",
        "license_type",
        "expiry_date",
        "machine_id",
        "signature",
    ]
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"

    expected_signature = generate_signature(data)
    if not hmac.compare_digest(expected_signature, data["signature"]):
        return False, "Invalid license signature"

    current_machine_id = get_machine_id()
    if data["machine_id"] != current_machine_id:
        return False, "License is not valid for this machine"

    try:
        expiry = datetime.strptime(data["expiry_date"], "%Y-%m-%d").date()
    except ValueError:
        return False, "Invalid expiry date format"

    if datetime.today().date() > expiry:
        return False, "License expired"

    return True, f"Licensed to {data['customer_name']} ({data['license_type']})"
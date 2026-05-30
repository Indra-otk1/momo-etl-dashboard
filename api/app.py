"""
api/app.py
REST API for MoMo SMS transactions using Python's built-in http.server.
Supports Basic Authentication and full CRUD operations.

Usage:
    python api/app.py                          # uses data/raw/modified_sms_v2.xml
    python api/app.py data/raw/my_file.xml     # custom XML path
"""

import sys
import os
import json
import base64
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Allow importing parse_xml from parent or sibling directory
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "etl"))
from parse_xml import parse_xml


# ── Configuration ─────────────────────────────────────────────────────────────

HOST      = "localhost"
PORT      = 8080
XML_PATH  = sys.argv[1] if len(sys.argv) > 1 else "data/raw/modified_sms_v2.xml"

# Basic Auth credentials (in production use env vars / a real auth system)
VALID_USERNAME = "admin"
VALID_PASSWORD = "momo2024"


# ── In-memory data store ──────────────────────────────────────────────────────

try:
    _transactions_list, _ = parse_xml(XML_PATH)
except FileNotFoundError:
    print(f"[WARNING] XML file not found at {XML_PATH}. Starting with empty dataset.")
    _transactions_list = []

# Dictionary for O(1) lookups (DSA: hash map)
transactions_db = {txn["id"]: txn for txn in _transactions_list}
next_id         = max(transactions_db.keys(), default=0) + 1


# ── Auth helper ───────────────────────────────────────────────────────────────

def is_authenticated(handler):
    """
    Check the Authorization header for valid Basic Auth credentials.
    Returns True if credentials match, False otherwise.
    """
    auth_header = handler.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        return False
    try:
        decoded    = base64.b64decode(auth_header[6:]).decode("utf-8")
        username, password = decoded.split(":", 1)
        return username == VALID_USERNAME and password == VALID_PASSWORD
    except Exception:
        return False


# ── Response helpers ──────────────────────────────────────────────────────────

def send_json(handler, status, data):
    body = json.dumps(data, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def send_401(handler):
    handler.send_response(401)
    handler.send_header("WWW-Authenticate", 'Basic realm="MoMo API"')
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps({"error": "Unauthorized. Provide valid credentials."}).encode())


def send_404(handler):
    send_json(handler, 404, {"error": "Transaction not found."})


def parse_id(path):
    """Extract integer ID from paths like /transactions/42"""
    match = re.match(r"^/transactions/(\d+)$", path)
    return int(match.group(1)) if match else None


# ── Request Handler ───────────────────────────────────────────────────────────

class MoMoHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """Override to keep terminal output clean."""
        print(f"  {self.address_string()} [{self.log_date_time_string()}] {format % args}")

    # ── GET ──────────────────────────────────────────────────────────────────

    def do_GET(self):
        if not is_authenticated(self):
            return send_401(self)

        path = urlparse(self.path).path

        # GET /transactions → list all
        if path == "/transactions":
            txns = list(transactions_db.values())
            send_json(self, 200, {"count": len(txns), "transactions": txns})

        # GET /transactions/{id} → single record
        elif parse_id(path) is not None:
            txn = transactions_db.get(parse_id(path))
            if txn:
                send_json(self, 200, txn)
            else:
                send_404(self)

        else:
            send_json(self, 404, {"error": "Endpoint not found."})

    # ── POST ─────────────────────────────────────────────────────────────────

    def do_POST(self):
        if not is_authenticated(self):
            return send_401(self)

        global next_id
        path = urlparse(self.path).path

        if path != "/transactions":
            send_json(self, 404, {"error": "Endpoint not found."})
            return

        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            send_json(self, 400, {"error": "Invalid JSON body."})
            return

        # Validate required fields
        required = ["category", "amount", "transaction_date"]
        missing  = [f for f in required if f not in data]
        if missing:
            send_json(self, 400, {"error": f"Missing required fields: {missing}"})
            return

        new_txn = {
            "id":              next_id,
            "external_id":     f"TXN-{next_id:05d}",
            "category":        data.get("category"),
            "amount":          float(data.get("amount", 0)),
            "balance_after":   data.get("balance_after"),
            "phone_number":    data.get("phone_number", ""),
            "transaction_date": data.get("transaction_date"),
            "status":          data.get("status", "SUCCESS"),
            "raw_sms":         data.get("raw_sms", ""),
        }
        transactions_db[next_id] = new_txn
        next_id += 1

        send_json(self, 201, {"message": "Transaction created.", "transaction": new_txn})

    # ── PUT ──────────────────────────────────────────────────────────────────

    def do_PUT(self):
        if not is_authenticated(self):
            return send_401(self)

        path = urlparse(self.path).path
        txn_id = parse_id(path)

        if txn_id is None:
            send_json(self, 404, {"error": "Endpoint not found."})
            return

        if txn_id not in transactions_db:
            send_404(self)
            return

        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        try:
            updates = json.loads(body)
        except json.JSONDecodeError:
            send_json(self, 400, {"error": "Invalid JSON body."})
            return

        # Merge updates into existing record (cannot change id or external_id)
        txn = transactions_db[txn_id]
        for key, value in updates.items():
            if key not in ("id", "external_id"):
                txn[key] = value

        send_json(self, 200, {"message": "Transaction updated.", "transaction": txn})

    # ── DELETE ────────────────────────────────────────────────────────────────

    def do_DELETE(self):
        if not is_authenticated(self):
            return send_401(self)

        path   = urlparse(self.path).path
        txn_id = parse_id(path)

        if txn_id is None:
            send_json(self, 404, {"error": "Endpoint not found."})
            return

        if txn_id not in transactions_db:
            send_404(self)
            return

        deleted = transactions_db.pop(txn_id)
        send_json(self, 200, {"message": "Transaction deleted.", "deleted": deleted})


# ── Server entrypoint ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), MoMoHandler)
    print(f"\n MoMo REST API running at http://{HOST}:{PORT}")
    print(f" Loaded {len(transactions_db)} transactions from {XML_PATH}")
    print(f" Credentials: {VALID_USERNAME} / {VALID_PASSWORD}")
    print(" Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n Server stopped.")

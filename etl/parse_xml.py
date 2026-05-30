"""
etl/parse_xml.py
Parses modified_sms_v2.xml into a list of transaction dictionaries.
"""

import xml.etree.ElementTree as ET
import json
import re
import os
from datetime import datetime


# ── helpers ──────────────────────────────────────────────────────────────────

def clean_amount(text):
    """Extract numeric value from strings like '5,000 RWF' → 5000.0"""
    if not text:
        return 0.0
    digits = re.sub(r"[^\d.]", "", text.replace(",", ""))
    try:
        return float(digits)
    except ValueError:
        return 0.0


def parse_date(text):
    """Try common date formats and return ISO string, or raw text if unrecognised."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%b %d, %Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt).isoformat()
        except (ValueError, AttributeError):
            continue
    return text  # return raw if nothing matched


def categorize(body):
    body_lower = (body or "").lower()
    if "you have received" in body_lower:
        return "INCOMING_MONEY"
    if "bank deposit" in body_lower:
        return "CASH_DEPOSIT"
    if "withdrawn" in body_lower or "cash withdrawal" in body_lower:
        return "CASH_WITHDRAWAL"
    if "airtime" in body_lower:
        return "AIRTIME_PURCHASE"
    if "bundles and packs" in body_lower:
        return "BUNDLE_PURCHASE"
    if "cash power" in body_lower or "wasac" in body_lower:
        return "PAYMENT"
    if "transferred to" in body_lower:
        return "OUTGOING_MONEY"
    if "your payment of" in body_lower:
        return "PAYMENT"
    if "one-time password" in body_lower or "password is" in body_lower:
        return None  # skip OTP messages
    return "UNKNOWN"


def extract_phone(body):
    """Pull the first phone number found in the SMS body."""
    match = re.search(r"\+?2507\d{8}|\b07\d{8}\b", body or "")
    return match.group(0) if match else None


def extract_amount(body):
    """Pull the first RWF amount from the SMS body."""
    match = re.search(r"([\d,]+)\s*RWF", body or "", re.IGNORECASE)
    if match:
        return clean_amount(match.group(1))
    return 0.0


def extract_balance(body):
    """Pull the balance figure that usually follows 'balance' or 'new balance'."""
    match = re.search(
        r"(?:balance[:\s]+|new balance[:\s]+)([\d,]+)\s*RWF",
        body or "",
        re.IGNORECASE,
    )
    if match:
        return clean_amount(match.group(1))
    return None


# ── main parser ───────────────────────────────────────────────────────────────

def parse_xml(filepath):
    """
    Parse the MoMo XML file and return a list of transaction dicts.

    Expected XML structure (each SMS record):
        <sms address="..." date="..." body="..." type="..." readable_date="..." />
    or wrapped in a <smses> root element.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"XML file not found: {filepath}")

    tree = ET.parse(filepath)
    root = tree.getroot()

    # Support both <smses><sms .../></smses> and flat <sms .../> roots
    sms_elements = root.findall(".//sms")
    if not sms_elements:
        # Maybe the root itself is a single sms element
        sms_elements = [root] if root.tag == "sms" else []

    transactions = []
    dead_letters = []

    for idx, sms in enumerate(sms_elements, start=1):
        body    = sms.get("body", "")
        address = sms.get("address", "")
        date    = sms.get("readable_date") or sms.get("date", "")
        sms_type = sms.get("type", "")  # 1 = received, 2 = sent (Android backup format)

        # Skip non-MoMo messages
        category = categorize(body)
        if category is None:
            dead_letters.append({"index": idx, "body": body[:120]})
            continue

        transaction = {
            "id":           idx,
            "external_id":  f"TXN-{idx:05d}",
            "category":     categorize(body),
            "amount":       extract_amount(body),
            "balance_after": extract_balance(body),
            "phone_number": extract_phone(body) or address,
            "transaction_date": parse_date(date),
            "status":       "SUCCESS",          # assume success unless body says failed
            "raw_sms":      body,
        }

        # Mark failed transactions
        if any(w in body.lower() for w in ["failed", "unsuccessful", "not completed"]):
            transaction["status"] = "FAILED"

        transactions.append(transaction)

    print(f"[parse_xml] Parsed {len(transactions)} transactions, "
          f"{len(dead_letters)} records skipped.")
    return transactions, dead_letters


# ── CLI entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import os

    # Always resolve paths relative to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if len(sys.argv) > 1:
        xml_path = sys.argv[1]
    else:
        xml_path = os.path.join(project_root, "data", "raw", "modified_sms_v2.xml")

    print(f"Looking for XML at: {xml_path}")
    txns, dead = parse_xml(xml_path)
    print(json.dumps(txns[:3], indent=2))
    print(f"\nTotal parsed: {len(txns)}")
    print(f"Dead letters: {len(dead)}")
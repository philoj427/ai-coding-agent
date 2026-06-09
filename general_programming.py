from __future__ import annotations

import csv
import io
import json
import re
from collections import defaultdict
from urllib.parse import parse_qs


def normalize_phone_number(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("phone number must contain 10 digits")
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def parse_log_line(line: str) -> dict[str, str]:
    level, timestamp, message = line.split(" ", 2)
    return {"level": level.strip("[]"), "timestamp": timestamp, "message": message}


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-+", "-", normalized)


def parse_query_string(query: str) -> dict[str, str]:
    parsed = parse_qs(query.lstrip("?"), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def apply_coupon(total: float, coupon: dict[str, float | str]) -> float:
    kind = coupon.get("type")
    value = float(coupon.get("value", 0))
    if kind == "percent":
        discount = total * value / 100
    elif kind == "fixed":
        discount = value
    else:
        discount = 0
    return max(0.0, round(total - discount, 2))


def calculate_invoice_total(items: list[dict[str, float]], tax_rate: float = 0.0) -> float:
    subtotal = sum(item["price"] * item.get("quantity", 1) for item in items)
    return round(subtotal * (1 + tax_rate), 2)


def merge_user_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for record in records:
        email = record["email"].lower()
        current = merged.setdefault(email, {"email": email})
        current.update({key: value for key, value in record.items() if value})
        current["email"] = email
    return [merged[email] for email in sorted(merged)]


def load_config_with_defaults(text: str, defaults: dict[str, object]) -> dict[str, object]:
    loaded = json.loads(text or "{}")
    return {**defaults, **loaded}


def generate_csv_report(rows: list[dict[str, object]], fields: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return output.getvalue()


def group_by_status(records: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        grouped[record["status"]].append(record)
    return dict(grouped)


def validate_state_transition(current: str, next_state: str) -> bool:
    allowed = {
        "new": {"paid", "cancelled"},
        "paid": {"shipped", "refunded"},
        "shipped": {"delivered"},
        "delivered": set(),
        "cancelled": set(),
        "refunded": set(),
    }
    return next_state in allowed.get(current, set())


class RateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._counts: dict[str, int] = {}

    def allow(self, key: str) -> bool:
        count = self._counts.get(key, 0)
        if count >= self.limit:
            return False
        self._counts[key] = count + 1
        return True

    def reset(self, key: str) -> None:
        self._counts.pop(key, None)

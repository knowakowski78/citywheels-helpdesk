"""Read-only tools. Money is calculated here, never by the language model."""

import json
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOW = datetime.fromisoformat("2026-06-10T09:00:00+02:00")
CONTACT = "Contact CityWheels staff: help@citywheels.example, +48 000 000 000."


class Tools:
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else ROOT / "data"
        self.bookings = json.loads((self.data_dir / "bookings.json").read_text(encoding="utf-8"))
        self.policies = [
            (p.name, p.read_text(encoding="utf-8"))
            for p in sorted((self.data_dir / "policies").glob("*.md"))
        ]

    def search_policies(self, query):
        """Lexical search over complete small documents, preserving related exceptions."""
        terms = set(re.findall(r"[\w-]+", query.casefold()))
        terms -= {"the", "a", "an", "is", "are", "what", "how", "do", "i", "can", "to", "of", "my", "you", "for", "in", "on", "and", "it", "we", "your"}
        aliases = {
            "refund": {"refund", "refunded", "cancelled", "cancelling"},
            "cancel": {"cancelling", "cancelled", "cancellations"},
            "zwrot": {"refund", "deposit"}, "anulować": {"cancelling", "refund"},
            "price": {"prices", "price"}, "cost": {"price", "prices"},
            "cena": {"prices", "price"}, "godziny": {"open"},
            "saturday": {"open", "saturday"}, "hours": {"open", "hours"},
            "14": {"age", "16"}, "helmet": {"helmets", "helmet"},
            "electric": {"electric", "e-bike"}, "ebike": {"electric", "e-bike"},
        }
        expanded = set(terms)
        for term in terms:
            expanded.update(aliases.get(term, ()))
        hits = []
        for name, content in self.policies:
            words = set(re.findall(r"[\w-]+", content.casefold()))
            headings = "\n".join(line for line in content.splitlines() if line.startswith("#"))
            heading_words = set(re.findall(r"[\w-]+", headings.casefold()))
            score = len(expanded & words) + 2 * len(expanded & heading_words)
            if score:
                hits.append({"source": f"data/policies/{name}", "text": content, "score": score})
        hits.sort(key=lambda h: (-h["score"], h["source"]))
        return {"found": bool(hits), "matches": hits[:3], "contact": CONTACT}

    def get_booking(self, booking_id):
        normalized = booking_id.strip().upper()
        booking = next((b for b in self.bookings if b["id"] == normalized), None)
        if booking is None:
            return {"found": False, "booking_id": normalized, "message": "Booking not found.", "contact": CONTACT}
        return {"found": True, "booking": dict(booking)}

    def calculate_refund(self, booking_id):
        lookup = self.get_booking(booking_id)
        if not lookup["found"]:
            return lookup
        booking = lookup["booking"]
        eligible = booking["status"] == "confirmed"
        # Use the assignment clock, even when running on a different day.
        hours = (
            datetime.fromisoformat(booking["start"]).astimezone(timezone.utc)
            - NOW.astimezone(timezone.utc)
        ).total_seconds() / 3600
        rate = Decimal("1") if hours >= 48 else Decimal("0.5") if hours >= 24 else Decimal("0")
        if not eligible:
            rate = Decimal("0")
        rental = Decimal(str(booking["rental_price_eur"])) * rate
        deposit = Decimal(str(booking["deposit_eur"])) if eligible else Decimal("0")

        def money(value):
            return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        return {
            "found": True, "booking_id": booking["id"], "can_cancel": eligible,
            "status": booking["status"], "as_of": NOW.isoformat(),
            "hours_before_start": hours, "rental_refund_percent": int(rate * 100),
            "rental_refund_eur": money(rental), "deposit_refund_eur": money(deposit),
            "booking_fee_refund_eur": "0.00", "total_refund_eur": money(rental + deposit),
            "refund_method": (
                "new voucher; deposit returned by original payment method"
                if booking["paid_with"] == "voucher" else "original card within 5 working days"
            ) if eligible else "none",
            "reason": "Standard cancellation rules applied." if eligible else "This booking status cannot be cancelled; nothing is refunded.",
            "source": "data/policies/cancellations.md",
            "note": "Quote only; no booking is changed. Storm-warning exceptions require staff approval.",
            "contact": CONTACT,
        }

    def execute(self, name, arguments):
        required = {"search_policies": "query", "get_booking": "booking_id", "calculate_refund": "booking_id"}
        if name not in required:
            return {"error": "Unknown tool", "contact": CONTACT}
        key = required[name]
        if (
            not isinstance(arguments, dict)
            or set(arguments) != {key}
            or not isinstance(arguments[key], str)
            or not arguments[key].strip()
        ):
            return {"error": f"Expected exactly one non-empty string argument: {key}", "contact": CONTACT}
        if len(arguments[key]) > 4000:
            return {"error": "Argument too long", "contact": CONTACT}
        return getattr(self, name)(**arguments)


TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": {argument: {"type": "string", "description": hint}}, "required": [argument], "additionalProperties": False},
    }}
    for name, argument, description, hint in [
        ("search_policies", "query", "Look up CityWheels prices, opening hours, age limits, helmets, payments and cancellation rules. Call this for shop-policy questions.", "English keywords, e.g. opening hours Saturday, e-bike prices, age limits."),
        ("get_booking", "booking_id", "Look up a booking by ID. Never guess booking details.", "Booking ID, e.g. CW-1001."),
        ("calculate_refund", "booking_id", "Calculate a cancellation refund NOW using fixed 2026-06-10 09:00 UTC+02. Includes deposit, non-refundable fee and payment method. Does not cancel anything.", "Booking ID, e.g. CW-1002."),
    ]
]

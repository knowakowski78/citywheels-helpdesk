import unittest
from datetime import timedelta, timezone

from citywheels.tools import NOW, Tools


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.tools = Tools()

    def test_booking_lookup_normalizes_id(self):
        booking = self.tools.get_booking(" cw-1002 ")["booking"]
        self.assertEqual(booking["bikes"], 2)
        self.assertEqual(booking["deposit_eur"], 300)

    def test_missing_booking(self):
        for method in (self.tools.get_booking, self.tools.calculate_refund):
            result = method("CW-9999")
            self.assertFalse(result["found"])
            self.assertIn("not found", result["message"])

    def test_known_refunds(self):
        expected = {"CW-1001": "90.00", "CW-1002": "340.00", "CW-1003": "50.00",
                    "CW-1004": "73.00", "CW-1007": "186.00", "CW-1010": "170.00"}
        for booking_id, total in expected.items():
            with self.subTest(booking_id=booking_id):
                result = self.tools.calculate_refund(booking_id)
                self.assertEqual(result["total_refund_eur"], total)
                self.assertEqual(result["booking_fee_refund_eur"], "0.00")

    def test_thresholds_to_the_second(self):
        for hours, percent, total in [(48, 100, "90.00"), (48 - 1/3600, 50, "70.00"),
                                      (24, 50, "70.00"), (24 - 1/3600, 0, "50.00"),
                                      (0, 0, "50.00"), (-1, 0, "50.00")]:
            with self.subTest(hours=hours):
                self.tools.bookings[0]["start"] = (NOW + timedelta(hours=hours)).isoformat()
                result = self.tools.calculate_refund("CW-1001")
                self.assertEqual(result["rental_refund_percent"], percent)
                self.assertEqual(result["total_refund_eur"], total)

    def test_timezone_offsets_represent_same_instant(self):
        self.tools.bookings[0]["start"] = (NOW + timedelta(hours=48)).astimezone(timezone.utc).isoformat()
        self.assertEqual(self.tools.calculate_refund("CW-1001")["total_refund_eur"], "90.00")

    def test_nonconfirmed_statuses_refund_nothing_including_deposit(self):
        for booking_id in ("CW-1005", "CW-1006", "CW-1008"):
            with self.subTest(booking_id=booking_id):
                result = self.tools.calculate_refund(booking_id)
                self.assertFalse(result["can_cancel"])
                self.assertEqual(result["total_refund_eur"], "0.00")
                self.assertEqual(result["deposit_refund_eur"], "0.00")
                self.assertEqual(result["refund_method"], "none")

    def test_voucher_and_card_methods(self):
        self.assertIn("voucher", self.tools.calculate_refund("CW-1004")["refund_method"])
        self.assertIn("5 working days", self.tools.calculate_refund("CW-1002")["refund_method"])

    def test_decimal_rounding(self):
        self.tools.bookings[1]["rental_price_eur"] = 10.01
        result = self.tools.calculate_refund("CW-1002")
        self.assertEqual(result["rental_refund_eur"], "5.01")
        self.assertEqual(result["total_refund_eur"], "305.01")

    def test_calculation_is_read_only(self):
        before = self.tools.get_booking("CW-1002")
        self.tools.calculate_refund("CW-1002")
        self.assertEqual(self.tools.get_booking("CW-1002"), before)

    def test_policy_sources_and_exceptions(self):
        for query, source, fact in [
            ("cancel refund", "cancellations.md", "storm warning"),
            ("e-bike prices", "prices.md", "40 EUR"),
            ("opening hours Saturday", "faq.md", "08:00–20:00"),
            ("zwrot", "cancellations.md", "deposit"),
        ]:
            with self.subTest(query=query):
                result = self.tools.search_policies(query)
                match = next(m for m in result["matches"] if m["source"].endswith(source))
                self.assertIn(fact, match["text"])

    def test_policy_no_match_and_empty(self):
        for query in ("", "quasarxyz", "What is the"):
            self.assertFalse(self.tools.search_policies(query)["found"])

    def test_opening_hours_rank_above_cancellation_time_limits(self):
        result = self.tools.search_policies("opening hours Saturday June")
        self.assertEqual(result["matches"][0]["source"], "data/policies/faq.md")

    def test_dispatch_rejects_bad_arguments(self):
        for name, args in [("delete_booking", {}), ("get_booking", {}),
                           ("get_booking", {"booking_id": 42}), ("get_booking", None),
                           ("get_booking", {"booking_id": ""}),
                           ("calculate_refund", {"booking_id": "CW-1001", "now": "tomorrow"}),
                           ("search_policies", {"query": "x" * 4001})]:
            with self.subTest(name=name, args=str(args)[:80]):
                self.assertIn("error", self.tools.execute(name, args))


if __name__ == "__main__":
    unittest.main()

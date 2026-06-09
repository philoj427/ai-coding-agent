import unittest

from general_programming import (
    RateLimiter,
    apply_coupon,
    calculate_invoice_total,
    generate_csv_report,
    group_by_status,
    load_config_with_defaults,
    merge_user_records,
    normalize_phone_number,
    parse_log_line,
    parse_query_string,
    slugify,
    validate_state_transition,
)


class TestGeneralProgramming(unittest.TestCase):
    def test_normalize_phone_number(self):
        self.assertEqual(normalize_phone_number("+1 (415) 555-0101"), "(415) 555-0101")
        with self.assertRaises(ValueError):
            normalize_phone_number("123")

    def test_parse_log_line(self):
        self.assertEqual(
            parse_log_line("[INFO] 2026-06-10 service started"),
            {"level": "INFO", "timestamp": "2026-06-10", "message": "service started"},
        )

    def test_slugify(self):
        self.assertEqual(slugify(" Hello, General Programming! "), "hello-general-programming")

    def test_parse_query_string(self):
        self.assertEqual(parse_query_string("?a=1&b=&a=2"), {"a": "2", "b": ""})

    def test_apply_coupon(self):
        self.assertEqual(apply_coupon(100, {"type": "percent", "value": 15}), 85.0)
        self.assertEqual(apply_coupon(20, {"type": "fixed", "value": 50}), 0.0)

    def test_calculate_invoice_total(self):
        items = [{"price": 10.0, "quantity": 2}, {"price": 5.0, "quantity": 1}]
        self.assertEqual(calculate_invoice_total(items, 0.1), 27.5)

    def test_merge_user_records(self):
        records = [
            {"email": "A@EXAMPLE.COM", "name": "Ada"},
            {"email": "a@example.com", "phone": "123"},
        ]
        self.assertEqual(merge_user_records(records), [{"email": "a@example.com", "name": "Ada", "phone": "123"}])

    def test_load_config_with_defaults(self):
        self.assertEqual(load_config_with_defaults('{"timeout": 10}', {"timeout": 5, "retries": 3}), {"timeout": 10, "retries": 3})

    def test_generate_csv_report(self):
        self.assertEqual(generate_csv_report([{"name": "Ada", "score": 10}], ["name", "score"]), "name,score\nAda,10\n")

    def test_group_by_status(self):
        grouped = group_by_status([{"id": "1", "status": "open"}, {"id": "2", "status": "closed"}])
        self.assertEqual([item["id"] for item in grouped["open"]], ["1"])

    def test_validate_state_transition(self):
        self.assertTrue(validate_state_transition("new", "paid"))
        self.assertFalse(validate_state_transition("delivered", "paid"))

    def test_rate_limiter(self):
        limiter = RateLimiter(2)
        self.assertTrue(limiter.allow("user"))
        self.assertTrue(limiter.allow("user"))
        self.assertFalse(limiter.allow("user"))
        limiter.reset("user")
        self.assertTrue(limiter.allow("user"))


if __name__ == "__main__":
    unittest.main()

import unittest

from demo_add import add


class TestDemoAdd(unittest.TestCase):
    def test_add_handles_positive_numbers(self):
        self.assertEqual(add(2, 3), 5)

    def test_add_handles_negative_numbers(self):
        self.assertEqual(add(-2, -3), -5)

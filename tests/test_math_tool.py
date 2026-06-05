import unittest

from math_tool import divide


class TestMathTool(unittest.TestCase):
    def test_divide(self):
        self.assertEqual(divide(6, 2), 3)

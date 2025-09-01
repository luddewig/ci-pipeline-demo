import unittest
from function import add

class TestAddFunction(unittest.TestCase):
    def test_positive_numbers(self):
        self.assertEqual(add(2, 3), 5)

    def test_negative_numbers(self):
        self.assertEqual(add(-2, -3), -4)

    def test_mixed_numbers(self):
        self.assertEqual(add(-2, 3), 1)

    def test_zero(self):
        self.assertEqual(add(0, 0), 0)
        self.assertEqual(add(0, 5), 5)
        self.assertEqual(add(7, 0), 7)

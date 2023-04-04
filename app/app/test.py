"""
Sample test file
"""

from django.test import SimpleTestCase
from app import calc


class CalTests(SimpleTestCase):

    def test_add_numbers(self):
        """Test that two numbers are added together"""
        self.assertEqual(calc.add(3, 8), 11)

    def test_subtract_numbers(self):
        """Test that values are subtracted and returned"""
        self.assertEqual(calc.subtract(10, 15), 5)

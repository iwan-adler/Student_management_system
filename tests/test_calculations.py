"""Tests for centrally defined calculation rules."""

import unittest

from utils.calculations import attendance_percentage, calculate_gpa, fee_details, grade_for


class CalculationTests(unittest.TestCase):
    def test_grade_and_gpa(self):
        self.assertEqual(grade_for(90), ("A+", 10))
        self.assertEqual(grade_for(39), ("F", 0))
        records = [{"grade": "A+", "credits": 4}, {"grade": "B", "credits": 2}]
        self.assertEqual(calculate_gpa(records), 9.0)

    def test_attendance_and_fees(self):
        self.assertEqual(attendance_percentage(40, 50), 80.0)
        self.assertEqual(fee_details(50000, 30000), (20000, "PARTIALLY PAID"))
        self.assertEqual(fee_details(50000, 0), (50000, "PENDING"))

"""Tests for basic input validation."""

import unittest

from utils.validators import valid_date, valid_email, valid_phone


class ValidatorTests(unittest.TestCase):
    def test_values(self):
        self.assertTrue(valid_email("student@example.edu"))
        self.assertFalse(valid_email("bad-address"))
        self.assertTrue(valid_phone("+91 98765 43210"))
        self.assertFalse(valid_phone("abc"))
        self.assertTrue(valid_date("2026-09-17"))
        self.assertFalse(valid_date("17/09/2026"))

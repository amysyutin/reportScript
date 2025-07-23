import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import to_utc_iso


def test_to_utc_iso_moscow():
    result = to_utc_iso('2025-07-21 15:00:00', 'Europe/Moscow')
    assert result == '2025-07-21T12:00:00Z'

"""Helpers shared by every test package.

Integration fixtures live in tests/integration/conftest.py, unit helpers
in tests/unit/conftest.py.
"""

from __future__ import annotations

import random


def generate_random_phone() -> str:
    """Генерирует случайный номер телефона для тестов."""
    return f"+7{random.randint(1000000000, 1999999999)}"

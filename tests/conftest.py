"""Shared helpers for legacy root-level tests.

Integration fixtures live under tests/integration/conftest.py.
"""

from __future__ import annotations

import random

# Константы для тестов Customer API
EXISTING_CUSTOMER_PHONE = "+79858038700"
NOT_FOUND_CUSTOMER_PHONE = "+71234567890"


def generate_random_phone() -> str:
    """Генерирует случайный номер телефона для тестов."""
    return f"+7{random.randint(1000000000, 1999999999)}"

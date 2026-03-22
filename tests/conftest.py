"""
Shared test configuration.

Sets required environment variables BEFORE any application module is imported,
so that settings.py validation (JWT_SECRET, DATABASE_URL) does not fail during
test collection.
"""
import os

# Provide safe dummy values for settings validation.
# These are only used when the env vars are not already set (e.g. CI).
_TEST_DEFAULTS = {
    "JWT_SECRET": "test-secret-not-for-production",
    "DATABASE_URL": "sqlite:///:memory:",
}

for key, value in _TEST_DEFAULTS.items():
    os.environ.setdefault(key, value)

"""Top-level legacy tests file renamed to avoid pytest import collision.

This file used to be `user_management/tests.py` but was renamed so the
`user_management.tests` import now points to the `user_management/tests/`
package. Keeping this file here for historical reference; pytest will not
collect it because it doesn't match the test module pattern.
"""

# Legacy placeholder

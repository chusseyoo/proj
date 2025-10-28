"""Top-level legacy tests file renamed to avoid pytest import collision.

This file used to be `session_management/tests.py` but was renamed so the
`session_management.tests` import now points to the `session_management/tests/`
package. Keeping this file here for historical reference; pytest will not
collect it because it doesn't match the test module pattern.
"""

# Legacy placeholder

"""Top-level legacy tests file renamed to avoid pytest import collision.

This file used to be `email_notifications/tests.py` but was renamed so the
`email_notifications.tests` import now points to the `email_notifications/tests/`
package. Keeping this file here for historical reference; pytest will not
collect it because it doesn't match the test module pattern.
"""

# Legacy placeholder

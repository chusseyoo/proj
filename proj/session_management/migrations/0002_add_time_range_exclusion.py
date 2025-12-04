from django.db import migrations


PG_FORWARD_SQL = """
-- Ensure the extension needed for btree_gist is available
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Add a tstzrange expression column to hold the time window (if not present)
ALTER TABLE IF EXISTS sessions ADD COLUMN IF NOT EXISTS time_range tstzrange;

-- Populate existing rows' time_range
UPDATE sessions SET time_range = tstzrange(time_created, time_ended) WHERE time_range IS NULL;

-- Create a GIST index for range queries
CREATE INDEX IF NOT EXISTS idx_sessions_time_range ON sessions USING GIST (time_range);

-- Add an exclusion constraint to prevent overlapping sessions for the same lecturer
ALTER TABLE sessions
ADD CONSTRAINT IF NOT EXISTS sessions_lecturer_time_excl
EXCLUDE USING gist (lecturer_id WITH =, time_range WITH &&);
"""

PG_REVERSE_SQL = """
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_lecturer_time_excl;
DROP INDEX IF EXISTS idx_sessions_time_range;
ALTER TABLE sessions DROP COLUMN IF EXISTS time_range;
"""


def forwards(apps, schema_editor):
    # Run Postgres-specific SQL only when using Postgres. Keeps sqlite dev/test working.
    conn = schema_editor.connection
    if conn.vendor != "postgresql":
        # noop on sqlite or other DBs
        return
    schema_editor.execute(PG_FORWARD_SQL)


def backwards(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != "postgresql":
        return
    schema_editor.execute(PG_REVERSE_SQL)


class Migration(migrations.Migration):
    dependencies = [("session_management", "0001_initial")]

    operations = [migrations.RunPython(forwards, backwards)]

Deployment & infra ideas (kept for later)
=========================================

This file collects the production and CI deployment ideas discussed during the
reporting work. It's intentionally short and actionable so we can pick it up
later when the project is ready for production-grade exports.

1) MEDIA_ROOT
   - Set a real `MEDIA_ROOT` in production (example: `/var/lib/<project>/media`)
   - Consider object storage (S3/GCS) for scale; implement a storage adapter
     that writes to S3 and returns a stable URL instead of a filesystem path.

2) File permissions & ownership
   - Ensure the directory is owned by the application user (e.g. `proj`), group to web user or job runner.
   - Recommended perms: directories 750, files 640. Avoid world-writable locations.
   - Consider `umask` and process user in containers/hosts.

3) Atomic writes & mounts
   - For local disk: use temp file + `os.replace()` (already in FilesystemStorageAdapter).
   - For shared/NFS mounts: validate that `os.replace()`/rename is atomic on target FS; otherwise write with unique names and coordinate.

4) Reconciliation / garbage collection
   - Consider a periodic job (management command or cron) to reconcile files on disk with DB rows (orphaned files) and to report missing files referenced by DB.

5) CI and test guidance
   - Tests should use a test MEDIA_ROOT (we use `proj/test_settings.py` with `media_test/`).
   - CI snippet: create a temp MEDIA_ROOT and set `DJANGO_SETTINGS_MODULE=proj.test_settings` before `pytest`.

6) Monitoring & retries
   - Log exporter successes/failures and the final file path on export.
   - Retries should be idempotent: the repository uses a row-locked `update_export_details` to avoid double-marking.

7) Optional: storage abstraction
   - Keep FilesystemStorageAdapter simple and add S3Adapter later. Use the DI factory to switch adapters in config.

8) Checklist to enable production exports (when ready)
   - Set MEDIA_ROOT in production settings or configure S3 adapter and credentials
   - Ensure app user has write access
   - Add monitoring/alerts for export failures
   - Add reconciliation job and run a smoke export in staging

References
- See: UPDATE_EXPORT_DETAILS.md for DB-side atomicity reasoning.

Update export details (atomic)

Purpose
-------
This document describes the approach used to safely mark a report as exported in the database and
why we make the update transactional and row-locked.

Context
-------
The export flow performs these steps:
 1. The exporter produces bytes for the report payload.
 2. The storage adapter persists the bytes to disk, returning a final path.
 3. The repository method `update_export_details(report_id, file_path, file_type)` records the final
    path and file type on the `Report` row.

Problem
-------
If two exporters run concurrently for the same report (e.g., retry or parallel workers), we can get a
race where both write files and both update the DB. That can lead to inconsistent state and lost
atomicity guarantees.

Solution
--------
We implement `update_export_details` using a DB transaction and a `SELECT ... FOR UPDATE` (via
Django's `select_for_update`) to acquire a row-level lock for the report. Inside the same transaction we
re-check whether the report is already exported and only then set `file_path` and `file_type`.

Why this ordering
-----------------
We expect callers to follow this ordering:
 1. call exporter to produce and persist bytes to the final path (or temp->move into final path)
 2. call `update_export_details(report_id, final_path, file_type)` to atomically mark the report
    exported in DB

This reduces the window where the DB says 'exported but file missing'. If a crash occurs after the
file write and before the DB update, the file exists but the DB doesn't mark it exported — the export
can be retried safely.

Implementation notes
--------------------
- Use `transaction.atomic()` and `Report.objects.select_for_update().get(pk=report_id)`.
- Raise `ValueError("report already exported")` if `file_path` is already set.
- Raise `ValueError("report <id> not found")` if report missing.

Testing checklist
-----------------
- Unit test: calling update_export_details twice should raise on second call.
- Integration test: perform export (storage write then update_export_details) and verify the DB row
  contains the file path.
- Optional concurrency test: spawn two threads that both call update_export_details; assert exactly one
  succeeds.

Operational notes
-----------------
- Storage write must complete before calling update_export_details, otherwise the DB may reference a
  non-existent file.
- Consider periodic reconciliation job to detect files on disk with no DB reference, if needed.

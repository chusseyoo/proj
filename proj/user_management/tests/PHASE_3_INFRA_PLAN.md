# Phase 3 – Infrastructure Layer Testing Plan

Goal
- Validate Django ORM repository implementations for User, StudentProfile, and LecturerProfile.
- Ensure correct persistence, retrieval, updates, uniqueness constraints, and FK integrity.
- Verify mapping fidelity between domain entities/value objects and DB records.

Scope
- Repositories (paths to be confirmed):
  - UserRepository
  - StudentProfileRepository
  - LecturerProfileRepository
- Test location: `proj/user_management/tests/infrastructure/`
- All tests using DB: `@pytest.mark.django_db`

## Files to create
- infrastructure/
  - conftest.py (shared fixtures, simple factories)
  - test_user_repository.py
  - test_student_profile_repository.py
  - test_lecturer_profile_repository.py

## Shared fixtures (conftest.py)
- Factories (functions, not external deps):
  - program_factory(program_code='BCS', has_streams=True)
  - stream_factory(program, name='Software Engineering')
  - user_factory(role, email, has_password, active=True)
  - student_profile_factory(user, program_id, stream_id=None, year=1, student_id='ABC/123456')
  - lecturer_profile_factory(user, department_name='Dept X')
- Value Objects: use Email and StudentId for clarity

## Test suites and cases

### test_user_repository.py
1. create_persists_user_with_password_hash
2. create_student_without_password_hash
3. exists_by_email_true_after_create
4. exists_by_email_false_for_unknown
5. find_by_email_returns_correct_user
6. find_by_id_returns_correct_user
7. update_changes_first_and_last_name
8. update_email_normalization_effect (if applicable)
9. delete_removes_user_and_cascade_profiles (if cascade configured)
10. duplicate_email_raises_integrity_error
11. create_admin_role_persistence
12. deactivate_and_reactivate_user (if supported)
Edge: email case-insensitive uniqueness ensured

### test_student_profile_repository.py
1. create_persists_profile_with_user_fk
2. find_by_student_id_returns_profile
3. exists_by_student_id_true_after_create
4. exists_by_student_id_false_for_unknown
5. create_stores_qr_code_equal_student_id
6. update_year_of_study_valid
7. update_year_of_study_invalid_out_of_range (expect domain/infra behavior)
8. update_stream_changes_stream_id (has_streams=True)
9. stream_required_when_program_has_streams
10. stream_not_allowed_when_program_no_streams
11. stream_must_belong_to_program
12. delete_user_cascades_student_profile
13. duplicate_student_id_raises_integrity_error
Edge: student_id normalization stored as uppercase

### test_lecturer_profile_repository.py
1. create_persists_profile
2. find_by_user_id_returns_profile
3. update_department_name
4. delete_user_cascades_lecturer_profile
5. multiple_profiles_not_allowed_per_user
Edge: department_name blanks/length validation if enforced

## Execution order
- Start with user repository, then student (depends on user/program/stream), then lecturer.
- Tests are independent; each uses fresh data and @pytest.mark.django_db transactional isolation.

## Negative & edge cases
- Uniqueness: duplicate email and student_id → IntegrityError (or repository-mapped exception)
- FK violations: invalid user/program/stream → IntegrityError
- Year_of_study outside 1–4 → domain validation or infra note
- Stream-program mismatch
- Null forbidden fields

## Assertions strategy
- After create: re-fetch via repository to avoid in-memory assumptions
- For cascades: delete user and assert profiles no longer exist
- For uniqueness: assert IntegrityError on second insert

## Coverage & metrics
- Target 100% line coverage for repositories; add branch coverage where feasible
- Run: `pytest -q --cov=user_management.infrastructure.repositories --cov-report=term-missing`
- Optional threshold: `--cov-fail-under=95`

## Risks & mitigations
- Schema mismatch: review Django models before implementing tests; align cases accordingly
- Domain enforces most rules: focus infra tests on persistence/constraints
- Cascades not configured: document and create a follow-up task if missing

## Next steps
1. Inspect repository classes and Django models to align tests with real schema
2. Scaffold `tests/infrastructure/` and `conftest.py`
3. Implement and green `test_user_repository.py`
4. Proceed to student and lecturer repository tests
5. Add coverage reporting

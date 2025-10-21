# Contexts Overview

This folder contains high-level guides for each bounded context in the project. Each context holds documentation (guides) that explain the domain model, repository and service layer designs, API contracts, and testing strategies. Use these guides as the canonical design artifacts for implementation and review.

Contexts included:

- `academic-structure/` - Models for programs, courses, streams, cohorts; repository and service patterns for enrollment and eligibility.
- `attendance-recording/` - Three-factor attendance capture (token + QR + GPS), validator services, API contract for marking attendance, and testing plans.
- `email-notifications/` - Token generation (JWT), email sending services, notification lifecycle and bulk sending patterns.
- `reporting/` - Report metadata, classification (Present/Late/Absent), CSV/Excel export orchestration, and report access control.
- `session-management/` - Session lifecycle, location/time windows, active session queries and lecturer ownership rules.
- `user-management/` - User and student profile models, role and account lifecycle, and identity used by other contexts.

How to use these guides

1. Start with the `models_guide.md` in a context to understand the data shape and constraints.
2. Read the `repositories_guide.md` for the recommended data access patterns and query optimization.
3. Implement business rules from the `services_guide.md`, which orchestrates repositories and other services.
4. Use `api_guide.md` to implement REST endpoints and clear request/response contracts.
5. Follow `testing_guide.md` to create unit and integration tests that validate the behavior described.

Cross-context pointers

- Many contexts assume shared contracts (JWT format, student id format, session id semantics). Use the corresponding `models_guide.md` and `services_guide.md` in those contexts to align implementations.
- `attendance-recording` relies on tokens from `email-notifications` and session details from `session-management`.
- `reporting` reads data from `attendance-recording`, `academic-structure`, and `session-management`.

Where to start

- If you are implementing the full flow: start with `user-management` and `academic-structure`, then `session-management`, `email-notifications`, `attendance-recording`, and finally `reporting`.
- If you are focused only on testing or maintenance: the `testing_guide.md` files provide clear test plans per context.

Contact and ownership

These documents are intended to be living design artifacts. Keep them updated as code evolves. For questions about a specific context, open the corresponding `README.md` inside the context folder and reference the `services_guide.md` for business rules.

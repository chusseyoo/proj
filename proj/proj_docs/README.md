
# Project Documentation Structure

This repository contains comprehensive documentation for the QR Code-Based Attendance Management System, organized following Domain-Driven Design (DDD) principles and Clean Architecture patterns.

## 📁 Directory Structure

```
proj_docs/
├── docs/
│   ├── shared/                  # Shared documentation (system flows, overview, roles, etc.)
│   │   ├── BOUNDED_CONTEXTS_OVERVIEW.md
│   │   ├── COMPLETE_SYSTEM_FLOWS.md
│   │   ├── api_guide.md
│   │   ├── attendance_management_doc.md
│   │   ├── entities_relationships.md
│   │   ├── models_guide.md
│   │   ├── project_overview.md
│   │   ├── repositories_guide.md
│   │   ├── services_guide.md
│   │   ├── user_roles.md
│   │   └── workflow.md
│   └── contexts/               # One folder per bounded context
│       ├── academic-structure/
│       │   ├── README.md
│       │   ├── academic_structure app structure.ini
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       ├── attendance-recording/
│       │   ├── README.md
│       │   ├── attendance_recording app structure.ini
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       ├── email-notifications/
│       │   ├── README.md
│       │   ├── email_notification app struccture.ini
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       ├── reporting/
│       │   ├── README.md
│       │   ├── reporting app structure.ini
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       ├── session-management/
│       │   ├── README.md
│       │   ├── session_management app structure
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       └── user-management/
│           ├── README.md
│           ├── user-management app structure
│           ├── api_guide.md
│           ├── models_guide.md
│           ├── repositories_guide.md
│           ├── services_guide.md
│           └── testing_guide.md
├── requirements.txt
├── README.md
```

## 📚 Documentation Guide



### Getting Started

1. **Start with Project Overview**
   - Read `docs/shared/project_overview.md` to understand the system purpose
   - Review `docs/shared/workflow.md` for general system flow
   - Check `docs/shared/user_roles.md` for role definitions

2. **Explore Bounded Contexts & Blueprints**
   - Go to `docs/contexts/` for a summary of all DDD bounded contexts
   - Each context folder contains:
     - An app structure file (folder/file tree with descriptions)
     - Implementation guides (models, repositories, services, API, testing)
   - Use these as blueprints for implementation and onboarding

3. **Understand the Domain**
   - Read `docs/shared/attendance_management_doc.md` for the bounded context
   - Review `docs/shared/entities_relationships.md` for entity relationships

4. **Learn the Architecture**
   - Read `docs/shared/COMPLETE_SYSTEM_FLOWS.md` for end-to-end flows
   - Study other shared guides in `docs/shared/`

### Documentation by Concern

#### 🏛️ **Architecture & Design**
- **System Flows**: `docs/COMPLETE_SYSTEM_FLOWS.md`
  - Complete trace of every use case through all layers
  - Request/response examples
  - Error handling flows
  
- **Domain Model**: `design/domain_model.md`
  - Aggregates, entities, and value objects
  - Domain services and repositories
  - Business rules and invariants

- **ERD**: `design/erd.md`
  - Database schema design
  - Entity relationships
  - Constraints and indexes

#### 💻 **Implementation Guides**

- **Application Layer**: `docs/implementation/APPLICATION_LAYER_GUIDE.md`
  - Commands and handlers
  - DTOs (Data Transfer Objects)
  - Event bus and subscribers
  - Use case orchestration

- **Domain Layer**: `docs/implementation/DOMAIN_LAYER_GUIDE.md`
  - Domain entities implementation
  - Value objects (Email, Location, PasswordHash)
  - Domain services (LocationValidator, AttendancePolicy)
  - Repository interfaces

- **Infrastructure Layer**: `docs/implementation/INFRASTRUCTURE_LAYER_GUIDE.md`
  - JWT token provider
  - Password hashing service
  - Email service and background tasks
  - Repository implementations (Django ORM)
  - Dependency injection container

- **Technical Implementation**: `docs/implementation/TECHNICAL_IMPLEMENTATION.md`
  - Haversine distance calculation
  - QR code handling
  - Email system setup
  - Token security
  - Web app specifics

#### 🔌 **API & Integration**

- **API Specification**: `design/api_spec.md`
  - Endpoint definitions
  - Request/response formats
  - Authentication requirements
  - Error responses

- **Sequence & Token Flow**: `design/sequence_and_token_flow.md`
  - Token lifecycle
  - Sequence diagrams
  - Email notification flow
  - Token validation process

- **Security & Deployment**: `design/security_and_deployment.md`
  - Security best practices
  - Token management
  - Deployment guidelines
  - Monitoring and logging

## 🎯 Documentation by Role

### **For Developers**

**Starting Development:**
1. `docs/project_overview.md` - Understand what you're building
2. `docs/implementation/INSTRUCTIONS_DDD_PY.md` - Setup and DDD guidelines
3. `docs/implementation/DOMAIN_LAYER_GUIDE.md` - Start with domain entities
4. `docs/implementation/APPLICATION_LAYER_GUIDE.md` - Build use cases
5. `docs/implementation/INFRASTRUCTURE_LAYER_GUIDE.md` - Implement services

**During Development:**
- Reference `docs/COMPLETE_SYSTEM_FLOWS.md` for understanding data flow
- Use `design/api_spec.md` for API contracts
- Check `docs/implementation/TECHNICAL_IMPLEMENTATION.md` for algorithms

### **For Project Managers**

**Understanding Scope:**
1. `docs/project_overview.md` - Project goals
2. `docs/workflow.md` - System workflow
3. `docs/attendance_management_doc.md` - Features and requirements

**Monitoring Progress:**
- `docs/COMPLETE_SYSTEM_FLOWS.md` - Track feature implementation
- `design/api_spec.md` - API readiness checklist

### **For System Architects**

**Architecture Review:**
1. `docs/COMPLETE_SYSTEM_FLOWS.md` - System architecture layers
2. `design/domain_model.md` - Domain design
3. `design/erd.md` - Data model
4. `design/security_and_deployment.md` - Infrastructure planning

**Design Patterns:**
- All files in `docs/implementation/` - Layer-specific patterns
- `design/sequence_and_token_flow.md` - Interaction patterns

### **For QA/Testers**

**Test Planning:**
1. `docs/workflow.md` - User workflows to test
2. `docs/COMPLETE_SYSTEM_FLOWS.md` - Expected system behavior
3. `design/api_spec.md` - API test cases
4. `docs/implementation/TECHNICAL_IMPLEMENTATION.md` - Edge cases (location, tokens)

## 🔄 Documentation Maintenance

### Structure Principles

This documentation follows the structure established in the DETAILS project:

1. **Top-level docs/** - High-level documentation and complete system flows
2. **docs/implementation/** - Layer-specific implementation guides
3. **design/** - Design specifications and API contracts
4. **src/** - Reference code implementations
5. **examples/** - Working code examples
6. **tests/** - Test examples

### When to Update

- **Domain changes**: Update `design/domain_model.md` and `docs/implementation/DOMAIN_LAYER_GUIDE.md`
- **API changes**: Update `design/api_spec.md` and corresponding flow documents
- **New features**: Add to `docs/COMPLETE_SYSTEM_FLOWS.md` and relevant guides
- **Infrastructure changes**: Update `docs/implementation/INFRASTRUCTURE_LAYER_GUIDE.md`

## 🚀 Quick Reference

### Most Used Documents

| Task | Document |
|------|----------|
| Understanding the system | `docs/project_overview.md` |
| Implementing a feature | `docs/COMPLETE_SYSTEM_FLOWS.md` |
| Working with domain entities | `docs/implementation/DOMAIN_LAYER_GUIDE.md` |
| Building API endpoints | `design/api_spec.md` |
| Setting up JWT tokens | `docs/implementation/INFRASTRUCTURE_LAYER_GUIDE.md` |
| Calculating distances | `docs/implementation/TECHNICAL_IMPLEMENTATION.md` |
| Understanding database | `design/erd.md` |

### Code Examples

- **JWT Token Generation**: `src/infrastructure/jwt_provider.py`
- **Email Service**: `src/infrastructure/emailer.py`
- **Background Tasks**: `src/infrastructure/email_tasks.py`
- **Complete Example**: `examples/token_email_example.py`

## 📝 Contributing to Documentation

When adding new documentation:

1. **Choose the right location**:
   - High-level concepts → `docs/`
   - Implementation details → `docs/implementation/`
   - Design specs → `design/`
   - Code examples → `src/` or `examples/`

2. **Follow naming conventions**:
   - Use UPPERCASE for major guides (e.g., `DOMAIN_LAYER_GUIDE.md`)
   - Use snake_case for specific docs (e.g., `attendance_management_doc.md`)
   - Be descriptive in file names

3. **Include in this README**:
   - Add new documents to the structure diagram
   - Add to relevant "Documentation by Concern" section
   - Update quick reference if applicable

## 🔗 Related Resources

- **DETAILS Project** (reference): `/home/chussey/Desktop/DETAILS/docs/`
- **Main Codebase**: `/home/chussey/Desktop/DETAILS/apps/user_management/`

---

**Last Updated**: October 14, 2025  
**Restructured**: Based on DETAILS project documentation patterns

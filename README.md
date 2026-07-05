# DroneNav API

## Overview

The DroneNav API is the operational services layer of the DroneNav platform. It provides a secure, RESTful interface for managing aviation data, spatial overlays, flight configuration, and operational services used by the DroneNav ecosystem.

The API is designed around a simple principle:

> **The API is the authoritative source for operational data.**

Applications such as the React web client, the DroneNav governance portal, and future flight controller integrations interact with the system exclusively through the API.

---

# Project Goals

The DroneNav API is designed to:

* Provide a clean REST API for operational services.
* Support multiple geographic authorities within a single installation.
* Maintain a clear separation between governance and operational data.
* Scale from small municipalities to regional deployments.
* Serve as the integration point for future autonomous flight services.

---

# Architecture

The project follows a layered architecture that separates HTTP processing, business logic, and database access.

```
Client
   │
   ▼
Routes (HTTP Interface)
   │
   ▼
Services (Business Logic)
   │
   ▼
Models (Database Access)
   │
   ▼
PostgreSQL / PostGIS
```

Each layer has a single responsibility.

---

## Route Layer

The Route layer is responsible for:

* Exposing REST endpoints
* Request parsing
* Authentication and authorization
* Input validation
* HTTP status codes
* JSON serialization

Routes should remain thin and delegate all business decisions to the Service layer.

---

## Service Layer

The Service layer contains the business rules of the application.

Responsibilities include:

* Workflow orchestration
* Business validation
* Transaction management
* Spatial processing coordination
* Error handling
* Calling one or more Model classes as required

Services contain the operational behavior of the system and remain independent of HTTP-specific concerns.

---

## Model Layer

The Model layer provides all database interaction.

Responsibilities include:

* SQL execution
* CRUD operations
* Transaction support
* Query optimization
* Mapping database results into Python objects

Models do not contain business rules. Their responsibility is persistence.

---

# Database

DroneNav uses PostgreSQL with PostGIS for spatial data management.

Spatial objects include:

* Sites
* Zones
* DronePorts
* Routes
* Future operational datasets

The database is designed for long-term scalability while maintaining a straightforward relational model.

---

# REST Principles

The API follows standard REST conventions.

Typical resources provide:

* GET
* POST
* PUT
* PATCH
* DELETE

JSON is used for both requests and responses.

Meaningful HTTP status codes and validation messages are returned for all operations.

---

# Design Philosophy

Several principles guide the implementation.

## Thin Routes

Routes should contain minimal logic.

Business decisions belong in Services.

---

## Single Responsibility

Each layer has one responsibility.

Keeping responsibilities isolated improves maintainability and testing.

---

## Explicit over Implicit

Configuration should be explicit whenever practical.

Hidden behavior and undocumented defaults are avoided unless they improve usability without introducing ambiguity.

---

## Transactional Consistency

Operations affecting multiple tables are executed within a single database transaction.

The system should never leave partially completed operational data.

---

## API as the System of Record

Operational data is owned by the API.

External applications consume the API rather than accessing the database directly.

This provides a stable integration surface and allows internal implementation details to evolve independently.

---

# Error Handling

The API returns consistent JSON error responses containing:

* HTTP status
* Error message
* Validation details (when applicable)

Validation failures are intended to be descriptive enough for client applications to present directly to users.

---

# Security

The API is designed to support authenticated access and role-based authorization.

Operational endpoints validate permissions before modifying protected resources.

Future releases will continue expanding security capabilities as additional operational services are introduced.

---

# Project Structure

```
api/
│
├── routes/        # HTTP endpoints
├── services/      # Business logic
├── models/        # Database operations
├── utils/         # Shared utilities
├── database/      # Database configuration
├── config/        # Application configuration
└── app.py         # Application entry point
```

---

# Future Direction

The DroneNav API is being developed incrementally to support a growing set of capabilities, including:

* Operational airspace management
* Flight configuration services
* Flight execution support
* Telemetry ingestion
* Conflict detection
* Fleet management
* Autonomous navigation services

The layered architecture is intended to support these capabilities while remaining maintainable, testable, and extensible.

---

# License

This project is released under the GNU Affero General Public License v3.0 (AGPL-3.0).

See the `LICENSE` file for details.

# Project Coding Standards & Security Rules

To maintain professional-grade code and ensure high reliability across different environments, the following rules MUST be followed:

## 1. Version Compatibility
*   **Python Version**: Always check the target Python version compatibility before using modern syntax (e.g., `|` for Union types, which requires Python 3.10+).
*   **Backward Compatibility**: If working on environments with older Python versions (like 3.9), use `from __future__ import annotations` or the `typing` module (`Union`, `Optional`) to ensure stability.

## 2. Security & Accountability
*   **Audit Logging**: ALL security-sensitive code (Key Management, Data Access, Training Jobs) must include comprehensive audit logging.
*   **Logging Detail**: Logs should capture the actor, event type, timestamp, and relevant non-sensitive metadata for every critical operation.

## 3. API Standards
*   **Documentation**: Every API service must include an interactive `/docs` (Swagger) and `/redoc` endpoint.
*   **Self-Discovery**: APIs should be self-documenting, with clear tags, descriptions, and health check endpoints.

# 1. Provision encrypted datasets
python -m secure_training_platform.tools.provision_datasets

# 2. Start the platform
python -m secure_training_platform.main

# 3. Open interactive API docs
open http://localhost:8100/docs

## 4. Performance & Efficiency
*   **Caching**: Implement data caching systems where applicable to make apps fast and responsive.
*   **Resource Management**: Ensure proper resource cleanup (e.g., memory wipes, container destruction) after intensive tasks.

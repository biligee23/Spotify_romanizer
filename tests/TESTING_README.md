# Spotify Romanizer - Test Suite

This document outlines the testing strategy for the Spotify Romanizer project and provides instructions on how to run the test suite.

## Testing Philosophy

The test suite is built with a few key principles in mind:

1.  **Isolation:** Tests should never make real network calls to external APIs (Spotify, Genius, YouTube). This makes the test suite fast, reliable, and independent of external factors. All external services are "mocked" during testing using `pytest-mock`.
2.  **Separation of Concerns:**
    - **Unit Tests** (`tests/services/`, `tests/tasks/`) are used to test the internal logic of individual functions and Celery tasks in isolation.
    - **Integration Tests** (`tests/routes/`) are used to test the entire request-response cycle of the Flask application, ensuring that routes, services, and mocks work together correctly.
3.  **Maintainability:** Tests are organized in a structure that mirrors the application source code. Shared setup logic is placed in `tests/conftest.py` using `pytest` fixtures to keep tests clean and DRY (Don't Repeat Yourself).

## Prerequisites

- The project must be running via Docker Compose.
- All Python dependencies, including `pytest` and `pytest-mock`, must be installed in the Docker image (as defined in `requirements.txt`).

## How to Run the Test Suite

The tests are designed to be run inside the running `web` container to ensure a consistent environment.

### 1. Start the Application Stack

If the application is not already running, start it from the project root:

```bash
docker-compose up -d
```

_(The `-d` flag runs the containers in detached mode in the background.)_

### 2. Execute the Tests

To run the entire test suite, use the `docker-compose exec` command:

```bash
docker-compose exec web pytest -v
```

- `web`: The name of the service container where the tests will run.
- `pytest`: The command to execute.
- `-v`: The "verbose" flag, which provides more detailed output for each test.

### Running a Specific Test File

To run only the tests in a single file, you can specify the path:

```bash
docker-compose exec web pytest -v tests/test_api_routes.py
```

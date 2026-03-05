# Contributing to DERIM Middleware

Thank you for your interest in contributing to the **Distributed Energy Resource Integration Middleware (DERIM)**. This project aims to become a community-driven standard for DER integration, and contributions of all kinds are welcome.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Architecture Overview](#architecture-overview)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code. Please report unacceptable behaviour to the maintainers.

## How Can I Contribute?

There are many ways to contribute to DERIM, regardless of your experience level.

**Report Bugs.** Found a problem? Open an issue using the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md). Include as much detail as possible: steps to reproduce, expected versus actual behaviour, logs, and environment information.

**Suggest Features.** Have an idea for a new feature or improvement? Open an issue using the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md). Describe the use case and how it would benefit the community.

**Write Code.** Pick an open issue labelled `good first issue` or `help wanted`, or implement a feature from the roadmap. See the [Development Setup](#development-setup) section below to get started.

**Improve Documentation.** Documentation improvements are always valued. This includes the README, docstrings, Jupyter notebooks, and inline comments.

**Add Protocol Adapters.** The middleware is designed to be extensible. If you work with a DER protocol not yet supported (e.g., DNP3, IEC 61850, OpenADR), consider contributing an adapter.

**Share Sample Data.** Real-world (anonymised) DER telemetry datasets help improve the digital twin models and make the project more useful for researchers.

## Development Setup

### Prerequisites

- Python 3.10 or later
- Git
- Docker and Docker Compose (optional, for containerised development)

### Local Installation

```bash
# Clone the repository.
git clone https://github.com/your-org/derim-middleware.git
cd derim-middleware

# Create and activate a virtual environment.
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install all dependencies (base + dev + ML).
pip install -r requirements/base.txt
pip install -r requirements/dev.txt
pip install -r requirements/ml.txt

# Install the package in editable mode.
pip install -e .

# Set up pre-commit hooks.
pre-commit install
```

### Running the API Locally

```bash
# Start with SQLite (no external dependencies).
uvicorn derim.main:app --reload

# Open the interactive API docs.
# http://localhost:8000/docs
```

### Running with Docker

```bash
docker compose up -d
# API available at http://localhost:8000
# InfluxDB UI at http://localhost:8086
```

## Coding Standards

DERIM follows strict coding standards to maintain consistency and readability across the codebase.

**Formatting.** All Python code must be formatted with [Black](https://black.readthedocs.io/) (line length 100) and imports sorted with [isort](https://pycqa.github.io/isort/). Run `black src/ tests/` and `isort src/ tests/` before committing.

**Linting.** Code must pass [Flake8](https://flake8.pycqa.org/) checks. Run `flake8 src/ tests/`.

**Type Hints.** Use type annotations for all function signatures and class attributes. The codebase targets Python 3.10+ and uses `from __future__ import annotations` where appropriate.

**Docstrings.** All public modules, classes, and functions must have NumPy-style docstrings. Include `Parameters`, `Returns`, and `Raises` sections where applicable.

**Commit Messages.** Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: add DNP3 protocol adapter
fix: correct register scaling in Modbus adapter
docs: update API endpoint documentation
test: add integration tests for SQLite storage
chore: update CI workflow to Python 3.12
```

## Testing

All contributions must include appropriate tests.

```bash
# Run the full test suite.
pytest tests/ -v

# Run with coverage report.
pytest tests/ --cov=derim --cov-report=term-missing

# Run a specific test file.
pytest tests/test_models.py -v

# Run tests matching a pattern.
pytest tests/ -k "test_solar" -v
```

**Test guidelines:**

- Place unit tests in `tests/` with filenames matching `test_*.py`.
- Use pytest fixtures (defined in `conftest.py`) for shared setup.
- Mock external dependencies (Modbus devices, MQTT brokers, etc.).
- Aim for at least 80% code coverage on new code.

## Pull Request Process

1. **Fork** the repository and create a feature branch from `main`.
2. **Write** your code following the coding standards above.
3. **Add tests** for any new functionality or bug fixes.
4. **Run** the full test suite and ensure all tests pass.
5. **Format** your code with `black` and `isort`.
6. **Commit** with a descriptive conventional commit message.
7. **Push** your branch and open a Pull Request against `main`.
8. **Fill out** the PR template completely.
9. **Respond** to review feedback promptly.

A maintainer will review your PR and may request changes. Once approved, it will be merged into `main`.

## Architecture Overview

Understanding the project architecture will help you contribute effectively.

```
src/derim/
├── adapters/       # Protocol adapters (Modbus, MQTT, SunSpec, OCPP)
├── api/            # FastAPI routes and dependencies
│   └── routes/     # Endpoint handlers (data, control, digital_twin)
├── digital_twin/   # ML forecasting and simulation engine
│   └── models/     # Baseline and LSTM forecasters
├── models/         # Pydantic data models (common, adapters)
├── storage/        # Storage backends (InfluxDB, SQLite)
├── utils/          # Logging, helpers
├── config.py       # Pydantic Settings configuration
└── main.py         # FastAPI application factory
```

**Adding a new protocol adapter:**

1. Create `src/derim/adapters/your_protocol.py`.
2. Inherit from `BaseAdapter` and implement `connect()`, `disconnect()`, `read_data()`, and `write_command()`.
3. Normalise all data into `DERTelemetry` (or a subclass).
4. Add tests in `tests/test_adapters.py`.
5. Update the README and configuration documentation.

**Adding a new storage backend:**

1. Create `src/derim/storage/your_backend.py`.
2. Inherit from `StorageBackend` and implement all abstract methods.
3. Register the backend in `src/derim/storage/__init__.py`.
4. Add tests in `tests/test_storage.py`.

---

Thank you for helping make DERIM a better tool for the smart grid community.

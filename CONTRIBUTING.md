# Contributing to HondaLink Controller

Thank you for your interest in contributing to HondaLink Controller! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing Guidelines](#testing-guidelines)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Getting Help](#getting-help)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **uv** package manager ([installation guide](https://github.com/astral-sh/uv))
- **ADB (Android Debug Bridge)** installed and in PATH
- **Git** for version control
- **Android device or emulator** with HondaLink app (for integration testing)

### Quick Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/hondalink-app-controller.git
   cd hondalink-app-controller
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/tahmidul612/hondalink-app-controller.git
   ```

4. **Install dependencies**:
   ```bash
   uv sync
   ```

5. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Run tests to verify setup**:
   ```bash
   uv run pytest
   ```

## Development Setup

### Environment Configuration

For development, use these `.env` settings:

```ini
# Development settings
USE_MOCK_DRIVER=True           # Test without real device
REQUIRE_AUTHENTICATION=False   # Simplify testing
ENABLE_RATE_LIMITING=False     # No limits during development
```

### IDE Setup

**Visual Studio Code** (Recommended)

Install recommended extensions:
- Python
- Pylance
- Ruff

Settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

**PyCharm/IntelliJ**

1. Configure interpreter: `.venv/bin/python`
2. Enable Ruff plugin
3. Configure Python Integrated Tools → Testing → pytest

## Project Structure

```
hondalink-app-controller/
├── src/
│   └── hondalink/          # Main package
│       ├── main.py         # FastAPI application
│       ├── controller.py   # Business logic (vehicle operations)
│       ├── driver.py       # Abstract driver interface
│       ├── driver_impl.py  # Real Android driver (uiautomator2)
│       ├── driver_mock.py  # Mock driver for testing
│       ├── models.py       # Pydantic models
│       ├── config.py       # Configuration management
│       └── security.py     # Authentication & authorization
├── tests/                  # Test suite
│   ├── test_api.py         # API endpoint tests
│   ├── test_controller.py  # Controller logic tests
│   ├── test_controller_pin.py
│   └── test_security.py    # Security feature tests
├── pyproject.toml          # Project dependencies and config
├── uv.lock                 # Locked dependencies
├── .env.example            # Example environment variables
├── README.md               # User documentation
├── CONTRIBUTING.md         # This file
├── SECURITY.md             # Security documentation
└── CODE_OF_CONDUCT.md      # Community guidelines
```

### Key Components

**`main.py`** - FastAPI application entry point
- All HTTP endpoints defined here
- Lifespan management for controller initialization
- Global controller with asyncio lock for thread safety

**`controller.py`** - Core business logic
- Vehicle command execution
- UI element detection and interaction
- Retry logic with exponential backoff
- Remote start status monitoring

**`driver_*.py`** - Hardware abstraction
- `driver.py`: Abstract base class (ABC)
- `driver_impl.py`: Real Android device via uiautomator2
- `driver_mock.py`: In-memory mock for testing

**`security.py`** - Security features
- API key authentication
- IP whitelist validation
- Rate limiting (two-tier)
- Audit logging

**`models.py`** - Data models
- `CommandType`: Enum for vehicle commands
- `VehicleStatus`: Vehicle state data
- `RemoteStartStatus`: Active session info

## Development Workflow

### Creating a Feature Branch

```bash
# Update your fork
git checkout main
git pull upstream main
git push origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Write tests first** (TDD approach recommended)
2. **Implement the feature**
3. **Run tests**: `uv run pytest`
4. **Run linter**: `uv run ruff check src/ tests/`
5. **Format code**: `uv run ruff format src/ tests/`
6. **Test manually** if applicable
7. **Update documentation** if needed

### Testing Your Changes

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_controller.py

# Run specific test
uv run pytest tests/test_controller.py::test_lock_command

# Run with verbose output
uv run pytest -v

# Run without real device
USE_MOCK_DRIVER=True uv run pytest
```

### Manual Testing

For features that interact with real devices:

```bash
# Start server in development mode
uv run uvicorn src.hondalink.main:app --reload

# In another terminal, test endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/action/lock
```

## Testing Guidelines

### Test Requirements

- **All new features must include tests**
- **Bug fixes should include regression tests**
- **Maintain or improve code coverage** (currently >80%)
- **Tests must pass in CI before merging**

### Test Structure

Follow existing patterns:

```python
import pytest
from src.hondalink.controller import HondaLinkController
from src.hondalink.driver_mock import MockDriver

@pytest.fixture
def mock_driver():
    """Create a mock driver for testing."""
    driver = MockDriver()
    driver.connect()
    # Register UI elements
    driver.register_element("text=Lock")
    return driver

@pytest.fixture
def controller(mock_driver):
    """Create controller with mock driver."""
    return HondaLinkController(mock_driver)

def test_your_feature(controller, mock_driver):
    """Test description."""
    # Arrange
    mock_driver.register_element("text=SomeButton")
    
    # Act
    result = controller.some_method()
    
    # Assert
    assert result is not None
    mock_button = mock_driver.find_by_text("SomeButton")
    assert mock_button.clicked
```

### Testing Best Practices

- **Use descriptive test names**: `test_lock_command_succeeds_when_vehicle_unlocked`
- **Follow AAA pattern**: Arrange, Act, Assert
- **Test edge cases**: Empty inputs, timeouts, errors
- **Mock external dependencies**: Use `MockDriver` for Android device
- **Keep tests isolated**: Each test should be independent
- **Use fixtures**: Share common setup with pytest fixtures

## Code Style

### Python Style Guide

We follow **PEP 8** with enforcement via **Ruff**:

```bash
# Check for issues
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/
```

### Key Conventions

**Imports**
- Standard library first
- Third-party packages second
- Local imports last
- Sorted alphabetically within each group
- Ruff automatically organizes imports

**Naming**
- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Descriptive names over abbreviations

**Type Hints**
- Use type hints for function parameters and return values
- Use `from __future__ import annotations` for forward references
- Use `|` for union types (Python 3.10+)

**Example:**
```python
from __future__ import annotations

from typing import Any

def get_vehicle_status(device_id: str) -> dict[str, Any]:
    """Get vehicle status from HondaLink app.
    
    Args:
        device_id: Android device identifier
        
    Returns:
        Dictionary containing vehicle status data
        
    Raises:
        HondaLinkException: If status retrieval fails
    """
    # Implementation
    pass
```

**Comments**
- Use docstrings for modules, classes, and functions
- Keep comments concise and relevant
- Explain "why", not "what" (code should be self-documenting)
- Update comments when code changes

### Ruff Configuration

Our `pyproject.toml` includes:
```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
```

## Pull Request Process

### Before Submitting

- [ ] Tests pass: `uv run pytest`
- [ ] Linting passes: `uv run ruff check src/ tests/`
- [ ] Code is formatted: `uv run ruff format src/ tests/`
- [ ] Documentation updated (if applicable)
- [ ] Commit messages follow guidelines
- [ ] Branch is up to date with main

### Submitting PR

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub:
   - Use descriptive title: "Add remote start status monitoring"
   - Reference related issues: "Closes #123"
   - Describe what changed and why
   - Include testing instructions
   - Add screenshots for UI changes

3. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Motivation
   Why is this change necessary?
   
   ## Changes
   - Added X feature
   - Fixed Y bug
   - Updated Z documentation
   
   ## Testing
   - [ ] Unit tests pass
   - [ ] Manual testing performed
   - [ ] Tested with real Android device
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   ```

### Review Process

1. **Automated checks run** (tests, linting)
2. **Maintainer reviews code**
3. **Feedback addressed** by contributor
4. **Approved and merged** by maintainer

### After Merge

- Delete your feature branch
- Update your fork's main branch
- Celebrate! 🎉

## Commit Message Guidelines

We follow **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring (no feature/bug change)
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build)

### Examples

```bash
# Simple feature
git commit -m "feat: add remote start status endpoint"

# Bug fix with details
git commit -m "fix(controller): handle timeout in command execution

The command execution would hang indefinitely if the app didn't respond.
Added 30-second timeout with proper error handling.

Fixes #123"

# Breaking change
git commit -m "feat(api)!: change authentication to use bearer tokens

BREAKING CHANGE: API key header changed from X-API-Key to Authorization.
Users must update their clients to use Bearer tokens."
```

### Best Practices

- Use imperative mood: "add feature" not "added feature"
- Keep subject line under 50 characters
- Wrap body at 72 characters
- Reference issues: "Fixes #123", "Closes #456"
- Explain "what" and "why", not "how"

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Pull Request Comments**: Code-specific questions

### Asking Good Questions

When asking for help:

1. **Search existing issues** first
2. **Provide context**: What are you trying to do?
3. **Include details**: OS, Python version, error messages
4. **Show what you tried**: Steps to reproduce
5. **Minimal example**: Simplest code that demonstrates the issue

### Good First Issues

Look for issues labeled:
- `good first issue` - Great for newcomers
- `help wanted` - Maintainers need assistance
- `documentation` - Non-code contributions

### What Makes a Good Contribution?

- **Solves a real problem** (not just code golf)
- **Well-tested** with edge cases covered
- **Properly documented** with clear explanations
- **Follows existing patterns** and conventions
- **Considers backward compatibility**
- **Includes helpful error messages**

## Thank You!

Your contributions make this project better for everyone. Whether it's code, documentation, bug reports, or feature ideas—every contribution matters.

Happy coding! 🚗💨

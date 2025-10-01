# Contributing to Aurora Pro AI

Thank you for your interest in contributing to Aurora Pro AI! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the project
- Show empathy towards other contributors

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/usephedm/aurora-pro-ai/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or screenshots

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear use case
   - Proposed solution
   - Alternatives considered
   - Impact assessment

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Write/update tests
5. Run tests: `pytest tests/`
6. Commit with clear messages
7. Push to your fork
8. Create a Pull Request

## Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Local Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/aurora-pro-ai.git
cd aurora-pro-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available

# Set up pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_orchestrator.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run with verbose output
pytest tests/ -v
```

### Running Locally

```bash
# Start dependencies
docker-compose up -d redis ollama

# Run API
python -m uvicorn src.api.main:app --reload

# Run GUI (in another terminal)
streamlit run src/gui/app.py
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Maximum line length: 100 characters

### Formatting

```bash
# Format code
black src/

# Check style
flake8 src/

# Type checking
mypy src/
```

### Example

```python
"""Module description"""
from typing import Dict, Any, Optional


def my_function(param: str, optional: Optional[int] = None) -> Dict[str, Any]:
    """
    Brief description of function
    
    Args:
        param: Description of param
        optional: Description of optional parameter
    
    Returns:
        Dict with result
    """
    return {"result": param, "optional": optional}
```

## Testing Guidelines

### Writing Tests

- Write tests for new features
- Update tests for bug fixes
- Aim for >80% code coverage
- Use descriptive test names

### Test Structure

```python
def test_feature_does_something():
    """Test that feature does what it should"""
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result["status"] == "success"
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await my_async_function()
    assert result is not None
```

## Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Include parameter descriptions
- Document return values
- Add usage examples where helpful

### Project Documentation

Update relevant documentation:
- README.md
- API.md
- DEPLOYMENT.md
- Architecture diagrams

## Git Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(agents): add support for custom agent types

- Implement BaseAgent extension interface
- Add custom agent registration
- Update documentation

Closes #123
```

```
fix(api): correct health check database connection

The health check was not properly closing database connections,
causing connection pool exhaustion.

Fixes #456
```

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How to test these changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] All tests passing
```

### Review Process

1. Automated tests run via CI/CD
2. Code review by maintainers
3. Address feedback
4. Approval and merge

## Project Structure

```
aurora-pro-ai/
├── src/                # Source code
│   ├── api/           # FastAPI application
│   ├── agents/        # Multi-agent system
│   ├── cache/         # Redis integration
│   ├── core/          # Core utilities
│   ├── db/            # Database models
│   ├── gui/           # Streamlit UI
│   └── utils/         # Utilities
├── tests/             # Test suite
├── docs/              # Documentation
├── config/            # Configuration templates
├── scripts/           # Utility scripts
└── plugins/           # Plugin examples
```

## Adding Features

### New Agent Type

1. Create agent class in `src/agents/`
2. Extend `BaseAgent`
3. Implement required methods
4. Add tests
5. Update documentation

### New API Endpoint

1. Add route in `src/api/routes/`
2. Define Pydantic models
3. Implement logic
4. Add tests
5. Update API documentation

### New Plugin

1. Create plugin directory in `plugins/`
2. Implement `BasePlugin` interface
3. Add plugin documentation
4. Create example usage

## Getting Help

- GitHub Issues
- Discussions
- Documentation
- Code comments

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be acknowledged in:
- GitHub contributors page
- Release notes
- Project README (for significant contributions)

Thank you for contributing to Aurora Pro AI! 🎉

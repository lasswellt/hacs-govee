# Contributing

Thank you for your interest in contributing to this project!

---

## Ways to Contribute

- Report bugs via [GitHub Issues](../../issues)
- Submit feature requests
- Create pull requests
- Improve documentation

---

## Development Setup

### Prerequisites

- Python 3.12 or 3.13
- Home Assistant development environment (optional)

### Quick Start

```bash
# Clone and install dependencies
git clone https://github.com/lasswellt/hacs-govee.git
cd hacs-govee
pip install -r requirements_test.txt

# Run tests
tox

# Format code
black .
```

### VS Code DevContainer

A devcontainer is provided in `.devcontainer/` that sets up a complete Home Assistant development instance accessible at `localhost:9123`.

---

## Pull Request Process

### 1. Fork and Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow existing code patterns
- Add tests for new functionality
- Update documentation if needed

### 3. Verify

```bash
# Format code
black .

# Run linting
flake8 .

# Run type checking
mypy custom_components/govee

# Run tests
pytest
```

### 4. Commit

Use conventional commit messages:

```
feat(light): add color temperature support
fix(coordinator): resolve state sync issue
docs(readme): update installation guide
test(config): add reauth flow tests
```

### 5. Submit PR

- Provide clear description
- Reference any related issues
- Ensure CI passes

---

## Code Standards

### Type Hints

All functions must have type annotations:

```python
async def async_turn_on(
    self,
    brightness: int | None = None,
    rgb_color: tuple[int, int, int] | None = None,
) -> None:
    """Turn on the light."""
    ...
```

### Async Architecture

All I/O operations must be async:

```python
# Correct - parallel execution
tasks = [self._fetch_state(d) for d in devices]
results = await asyncio.gather(*tasks)

# Incorrect - sequential
for device in devices:
    result = await self._fetch_state(device)
```

### Docstrings

Use Google-style docstrings:

```python
def process_state(self, data: dict[str, Any]) -> GoveeDeviceState:
    """Process raw API state data into domain model.

    Args:
        data: Raw state dictionary from API response.

    Returns:
        Processed device state object.

    Raises:
        ValueError: If required fields are missing.
    """
```

---

## Testing Requirements

| Requirement | Standard |
|-------------|----------|
| Coverage | 95%+ overall |
| Python versions | 3.12 and 3.13 |
| Async tests | Use `@pytest.mark.asyncio` |
| Mocking | Mock all external dependencies |

See [TESTING.md](TESTING.md) for detailed testing guide.

---

## Architecture Guidelines

When making changes:

1. **Models** (`models/`): Immutable dataclasses, no I/O
2. **Protocols** (`protocols/`): Interfaces only, no implementation
3. **API Layer** (`api/`): HTTP/MQTT clients, exception handling
4. **Coordinator**: State management, orchestration
5. **Entities**: Home Assistant platform integration

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture.

---

## Bug Reports

Good bug reports include:

- Summary and background
- Steps to reproduce
- Expected vs actual behavior
- Debug logs (enable with `custom_components.govee: debug`)
- Diagnostics download

---

## License

Contributions are licensed under the MIT License.

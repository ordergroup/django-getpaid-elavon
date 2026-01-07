# Elavon GetPaid Plugin

Elavon Payment Gateway plugin for Django projects using the GetPaid framework. This integration handles webhook-based confirmation flows for Elavon transactions via REST.

## Project Structure

```
.
├── getpaid_elavon/          # Main plugin package with payment processing logic
├── tests/                   # Main Django app for testing (settings, urls)
├── test_app/                # Minimal Django app for testing purposes only
└── pyproject.toml           # Project dependencies and configuration
```

**Note:** No migrations are needed when running `python manage.py runserver` as this is a plugin package, not a standalone Django application.

## Example configuration

1. Add `"getpaid_elavon"` to `INSTALLED_APPS`.

```python
GETPAID_BACKENDS_SETTINGS = {
    "getpaid_elavon": {
        "merchant_alias_id": "your_merchant_alias_id",
        "secret_key": "your_secret_key",
        "confirmation_method": "PUSH",
        "webhook_shared_secret": "your_webhook_shared_secret",
        "webhook_signer_id": "your_signer_id",
        "sandbox": True,
        "method": "REST",
        "logger_name": "your_logger_name",
    },
}
```

> **Note:** The plugin is configured exclusively for webhook confirmations. Ensure your project accepts and verifies Elavon webhook calls with the shared secret before going live.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Setup

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest -v

# Run linting
uv run ruff check .

# Format code
uv run ruff format .
```

### Available Make Commands

```bash
make test       # Run all tests
make test-cov   # Run tests with coverage
make lint       # Check code with ruff
make format     # Format code with ruff
make fix        # Fix and format code with ruff
```

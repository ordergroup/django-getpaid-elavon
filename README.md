# Elavon GetPaid Plugin

Elavon Payment Gateway plugin for Django projects using the GetPaid framework. This integration handles webhook-based confirmation flows for Elavon transactions via REST.

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
    },
}
```

> **Note:** The plugin is configured exclusively for webhook confirmations. Ensure your project accepts and verifies Elavon webhook calls with the shared secret before going live.

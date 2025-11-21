from decimal import Decimal

import pytest

from getpaid_elavon.client import Client


def pytest_configure():
    """Configure Django settings for pytest."""
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    import django

    django.setup()


@pytest.fixture
def client():
    return Client(
        merchant_alias_id="test_merchant_alias",
        secret_key="test_secret_key",
        sandbox=True,
    )


@pytest.fixture
def order():
    from factories import OrderFactory

    return OrderFactory.build(
        pk=123,
        total=Decimal("100.50"),
        currency="EUR",
        description="Test order for payment",
    )


@pytest.fixture
def expected_payload(order):
    return {
        "orderReference": "123",
        "total": {
            "currencyCode": "EUR",
            "amount": "100.50",
        },
        "description": order.get_description(),
        "items": [
            {
                "total": {
                    "amount": 1,
                    "currencyCode": "EUR",
                },
                "description": order.get_description(),
            }
        ],
    }


@pytest.fixture
def mock_order_response():
    return {
        "id": "elavon_order_123",
        "href": "https://uat.api.converge.eu.elavonaws.com/orders/elavon_order_123",
        "orderReference": "123",
        "total": {
            "currency": "EUR",
            "amount": "100.50",
        },
        "status": "created",
    }

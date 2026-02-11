import textwrap
from decimal import Decimal

from django.db import models
from getpaid.models import AbstractOrder


class Order(AbstractOrder):
    """Test Order model for getpaid_elavon testing."""

    name = models.CharField(max_length=255)
    total = models.DecimalField(decimal_places=2, max_digits=10)
    currency = models.CharField(max_length=3, default="EUR")
    amount_paid = models.DecimalField(decimal_places=2, max_digits=10, default=Decimal("0"))
    description = models.TextField()

    def get_total_amount(self):
        return self.total - self.amount_paid

    def get_description(self):
        return self.description

    def get_currency(self):
        return self.currency

    def get_items(self):
        return [
            {
                "name": textwrap.shorten(self.get_description(), 255, placeholder="..."),
                "quantity": 1,
                "unit_price": self.get_total_amount(),
            }
        ]

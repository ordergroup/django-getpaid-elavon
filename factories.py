import textwrap

import factory
import swapper

from test_app.models import Order


class OrderFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("color_name")
    total = factory.Faker(
        "pydecimal", positive=True, right_digits=2, min_value=10, max_value=500
    )
    currency = "EUR"
    amount_paid = 0
    description = factory.Faker("sentence", nb_words=6)

    class Meta:
        model = Order


class PaymentFactory(factory.django.DjangoModelFactory):
    order = factory.SubFactory(OrderFactory)
    amount_required = factory.SelfAttribute("order.total")
    currency = factory.SelfAttribute("order.currency")
    description = factory.SelfAttribute("order.name")
    backend = "getpaid_elavon"

    class Meta:
        model = swapper.load_model("getpaid", "Payment")

import hashlib
import logging
from decimal import Decimal

from django.conf import settings
from django.db.transaction import atomic
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect)
from django.urls import reverse
from getpaid.processor import BaseProcessor

from getpaid_elavon.client import Client

logger = logging.getLogger(__name__)


class PaymentProcessor(BaseProcessor):
    display_name = "Elavon"
    slug = "elavon"
    accepted_currencies = []  # use ISO codes here, e.g. "EUR", "USD"
    # logo_url = None

    method = "REST"
    # template_name = None  # used only if method == "POST"
    production_url = None  #: Base URL of production environment.
    sandbox_url = None  #: Base URL of sandbox environment.
    # post_form_class = None
    # post_template_name = None
    client_class = Client
    #: List of potentially successful HTTP status codes returned by paywall
    # when creating payment
    ok_statuses = [200, 201, 302]

    def get_client_params(self):
        return {
            "merchant_id": self.get_setting("merchant_id"),
            "user_id": self.get_setting("user_id"),
            "pin": self.get_setting("pin"),
            "sandbox": self.get_setting("sandbox", True),
        }

    @atomic()
    def prepare_transaction(self, request=None, view=None, **kwargs):
        payment = self.payment
        order = payment.order

        client = self.get_client()
        # Create order on Elavon, get response which contains order URL
        elavon_order_resp = client.create_order(
            order_id=order.pk, amount=float(order.total_amount), currency=order.currency
        )
        elavon_order_url = (
            elavon_order_resp.get("url")
            or elavon_order_resp.get("self")
            or elavon_order_resp.get("id")
        )
        #    e.g. https://uat.api.converge.eu.elavonaws.com/orders/xxxxxxxxxx

        success_url = request.build_absolute_uri(
            reverse("payment-success", kwargs={"pk": order.pk})
        )
        fail_url = request.build_absolute_uri(
            reverse("payment-fail", kwargs={"pk": order.pk})
        )

        # Create payment session referencing the order URL
        session_resp = client.create_payment_session(
            elavon_order_url=elavon_order_url,
            return_url=success_url,
            cancel_url=fail_url,
        )

        payment.external_id = elavon_order_resp.get("id")
        payment.save(update_fields=["external_id"])

        payment_url = session_resp.get("href")
        if not payment_url:
            payment.mark_as_failed()
            return HttpResponseRedirect(fail_url)

        return HttpResponseRedirect(payment_url)

    def handle_paywall_callback(self, request, view_kwargs=None):
        payment = self.payment
        data = request.POST.dict() if request.method == "POST" else request.GET.dict()

        # Add response validation here

        status = data.get("status", "").lower()

        if status == "success":
            payment.amount_paid = Decimal(data.get("amount", payment.amount_required))
            payment.mark_as_paid()
        elif status == "failure":
            payment.mark_as_failed()
        else:
            payment.mark_as_prepared()  # or handle differently as needed

        return HttpResponse("OK")

    # you need to define at least these methods:
    def get_redirect_params(self) -> dict:
        """
        Must return a dictionary containing all the data required by
        backend to process the payment in appropriate format.

        Refer to your broker's API documentation for info what keys the API
        expects and what types should the values be in.

        The Payment instance is here: self.payment
        """
        return {}

    def get_redirect_url(self) -> str:
        """
        Returns URL where the user will be redirected to complete the payment.
        This URL should be provided in your broker's documentation.

        The Payment instance is here: self.payment
        """
        return ""

    def handle_callback(self, request, *args, **kwargs):
        """
        One of most popular payment workflows uses a callback endpoint
        that should accept a POST request, parse it and act accordingly
        (e.g. mark payment as accepted or failed) and return a response.
        """
        return HttpResponse()

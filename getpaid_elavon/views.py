import json
import logging

import swapper
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from getpaid_elavon import PaymentProcessor

Payment = swapper.load_model("getpaid", "Payment")
logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class CallbackView(View):
    """Handle Elavon webhook notifications."""

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if settings.DEBUG:
            logger.debug(
                "Sandbox webhook received",
                extra={
                    "headers": dict(request.headers),
                    "body": data,
                },
            )

        # Example: "https://uat.api.converge.eu.elavonaws.com/payment-sessions/7p7rmqwgrcyytp7jdy4tgtfbfcpy"
        resource_url = data.get("resource")
        payment_session_id = resource_url.rstrip("/").split("/")[-1]

        Payment = swapper.load_model("getpaid", "Payment")
        payment = get_object_or_404(
            Payment,
            external_id=payment_session_id,
            backend=f"getpaid_{PaymentProcessor.slug}",
        )

        return payment.handle_paywall_callback(request, *args, **kwargs)

import json

import swapper
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from getpaid_elavon import PaymentProcessor
from getpaid_elavon.utils import get_logger

Payment = swapper.load_model("getpaid", "Payment")

logger = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
class CallbackView(View):
    """Handle Elavon webhook notifications."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request body: %s", request.body)
            return HttpResponse(status=200)

        logger.info(
            "Sandbox webhook received | headers=%s | body=%s",
            str(dict(request.headers)),
            str(data),
        )

        # Example: "https://uat.api.converge.eu.elavonaws.com/payment-sessions/7p7rmqwgrcyytp7jdy4tgtfbfcpy"
        resource_url = data.get("resource")
        resource_type = data.get("resourceType")

        if resource_type != "paymentSession":
            logger.warning(
                "Received webhook for non-paymentSession resource: %s",
                resource_type,
            )
            return HttpResponse(status=200)
        payment_session_id = resource_url.rstrip("/").split("/")[-1]

        try:
            payment = Payment.objects.get(
                external_id=payment_session_id,
                backend=f"getpaid_{PaymentProcessor.slug}",
            )
        except Payment.DoesNotExist:
            logger.warning(
                "Payment not found for webhook external_id: %s event_type: %s",
                payment_session_id,
                data.get("eventType"),
            )
            return HttpResponse(status=200)

        return payment.handle_paywall_callback(request, *args, **kwargs)

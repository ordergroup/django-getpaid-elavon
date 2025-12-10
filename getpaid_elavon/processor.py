import base64
import hashlib
import hmac
import json
import logging

from django.db.transaction import atomic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django_fsm import can_proceed
from getpaid.processor import BaseProcessor

from getpaid_elavon.client import Client
from getpaid_elavon.types import PaymentStatus

logger = logging.getLogger(__name__)


class PaymentProcessor(BaseProcessor):
    display_name = "Elavon"
    slug = "elavon"
    accepted_currencies = []
    method = "REST"
    production_url = "https://api.eu.elavonpayments.com"
    sandbox_url = "https://uat.api.converge.eu.elavonaws.com"
    client_class = Client
    ok_statuses = [200, 201, 302]

    def get_client_params(self):
        return {
            "merchant_alias_id": self.get_setting("merchant_alias_id"),
            "secret_key": self.get_setting("secret_key"),
            "sandbox": self.get_setting("sandbox", True),
        }

    def get_paywall_context(self, request=None) -> dict:
        """
        Prepare context parameters for creating an order.

        Returns:
            Dict with order parameters ready for client.create_order()
        """
        order = self.payment.order

        items = [
            {
                "total": {
                    "amount": item.get("quantity", 1),
                    "currencyCode": order.get_currency(),
                },
                "description": item.get("name", ""),
            }
            for item in order.get_items()
        ]

        return {
            "order_reference": str(order.pk),
            "total_amount": f"{order.get_total_amount()}",
            "currency_code": order.get_currency(),
            "description": order.get_description(),
            "items": items,
            "custom_reference": self.payment.id,
        }

    @atomic()
    def prepare_transaction(self, request=None, view=None, **kwargs):
        payment = self.payment
        order = payment.order

        params = self.get_paywall_context(request=request)
        order_resp = self.client.create_order(**params)

        elavon_order_url = order_resp.get("href")
        success_url = order.get_success_url(request=request)
        fail_url = request.build_absolute_uri(
            reverse("getpaid:payment-failure", kwargs={"pk": payment.pk})
        )
        buyer_info = payment.get_buyer_info()

        session_resp = self.client.create_payment_session(
            elavon_order_url=elavon_order_url,
            return_url=success_url,
            cancel_url=fail_url,
            custom_reference=payment.id,
            buyer_info=buyer_info,
        )

        payment.external_id = session_resp.get("id")
        payment.save(update_fields=["external_id"])

        payment_hpp_url = session_resp.get("url")

        return HttpResponseRedirect(payment_hpp_url)

    def _validate_signature(self, request, body: bytes) -> bool:
        """
        Validate webhook signature using SHA-512.

        Args:
            request: Django request object with headers
            body: Raw request body bytes

        Returns:
            True if signature is valid, False otherwise
        """
        webhook_shared_secret = self.get_setting("webhook_shared_secret")
        webhook_signer_id = self.get_setting("webhook_signer_id")

        header_name = f"Signature-{webhook_signer_id}"
        received_signature = request.headers.get(header_name)

        if not received_signature:
            logger.error(
                f"Missing signature header: {header_name}",
                extra={"payment_id": self.payment.id},
            )
            return False

        shared_secret_bytes = base64.b64decode(webhook_shared_secret)

        body_bytes = body

        final_bytes = shared_secret_bytes + body_bytes

        hash_result = hashlib.sha512(final_bytes).digest()

        expected_signature = base64.b64encode(hash_result).decode("utf-8")

        is_valid = hmac.compare_digest(received_signature.strip(), expected_signature)

        return is_valid

    @atomic()
    def handle_paywall_callback(self, request, *args, **kwargs):
        """
        Handle webhook notification and update payment status.

        Processes eventType from webhook:
        - saleAuthorized: Payment successful
        - saleDeclined: Payment failed
        - saleAuthorizationPending: Payment pending
        - expired: Payment session expired

        Returns:
            HttpResponse with status 200 to acknowledge webhook
        """

        payment = self.payment

        try:
            if not self._validate_signature(request, request.body):
                logger.error(
                    "Webhook signature validation failed",
                    extra={"payment_id": payment.id},
                )
                return HttpResponse(status=403)

            data = json.loads(request.body)
            event_type = data.get("eventType")

            if event_type == PaymentStatus.SALE_AUTHORIZED:
                if can_proceed(payment.confirm_payment):
                    payment.confirm_payment()
                    if can_proceed(payment.mark_as_paid):
                        payment.mark_as_paid()

                logger.info(
                    "Payment authorized successfully",
                    extra={
                        "payment_id": payment.id,
                        "order_id": payment.order.pk,
                        "amount": str(payment.amount_paid),
                    },
                )

            elif event_type == PaymentStatus.SALE_DECLINED:
                payment.fail()

                logger.warning(
                    "Payment declined",
                    extra={
                        "payment_id": payment.id,
                        "order_id": payment.order.pk,
                    },
                )

            elif event_type == PaymentStatus.SALE_AUTHORIZATION_PENDING:
                if can_proceed(payment.confirm_lock):
                    payment.confirm_lock()
                logger.info(
                    "Payment authorization pending",
                    extra={
                        "payment_id": payment.id,
                        "order_id": payment.order.pk,
                    },
                )
            elif event_type == PaymentStatus.EXPIRED:
                payment.fail()

                logger.warning(
                    "Payment session expired",
                    extra={
                        "payment_id": payment.id,
                        "order_id": payment.order.pk,
                    },
                )

            else:
                logger.warning(
                    f"Unknown event type received: {event_type}",
                    extra={
                        "payment_id": payment.id,
                        "event_type": event_type,
                    },
                )
            payment.save()
            return HttpResponse(status=200)

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse webhook JSON: {e}", extra={"payment_id": payment.id}
            )
            return HttpResponse(status=400)

        except Exception as e:
            logger.exception(
                f"Error handling webhook: {e}", extra={"payment_id": payment.id}
            )
            # Return 200 to prevent webhook retries for processing errors
            return HttpResponse(status=200)

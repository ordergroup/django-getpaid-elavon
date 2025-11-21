import json
import logging

from django.db.transaction import atomic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from getpaid.processor import BaseProcessor

from getpaid_elavon.client import Client
from getpaid_elavon.types import PaymentStatus

logger = logging.getLogger(__name__)


class PaymentProcessor(BaseProcessor):
    display_name = "Elavon"
    slug = "elavon"
    accepted_currencies = []
    method = "REST"
    # template_name = None  # used only if method == "POST"
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

    @atomic()
    def prepare_transaction(self, request=None, view=None, **kwargs):
        payment = self.payment
        order = payment.order

        success_url = order.get_success_url(request=request)

        fail_url = request.build_absolute_uri(
            reverse("getpaid:payment-failure", kwargs={"pk": payment.pk})
        )

        order_resp = self.client.create_order(order=order, custom_reference=payment.id)

        elavon_order_url = order_resp.get("href")

        bill_to = self._build_bill_to(order)

        session_resp = self.client.create_payment_session(
            elavon_order_url=elavon_order_url,
            return_url=success_url,
            cancel_url=fail_url,
            custom_reference=payment.id,
            bill_to=bill_to,
        )

        payment.external_id = session_resp.get("id")
        payment.save(update_fields=["external_id"])

        payment_hpp_url = session_resp.get("url")

        logger.info(
            "Payment transaction prepared successfully",
            extra={
                "payment_id": payment.id,
                "order_id": order.pk,
                "elavon_order_id": payment.external_id,
            },
        )
        return HttpResponseRedirect(payment_hpp_url)

    @staticmethod
    def _build_bill_to(order) -> dict:

        customer = order.customer
        street_address = " ".join(
            [customer.street, customer.house_number, customer.apt_number]
        )[:255]

        bill_to = {
            "countryCode": "POL",
            "company": customer.name or "",
            "street1": street_address,
            "city": customer.city or "",
            "postalCode": customer.postcode or "",
            "email": customer.email or "",
            "primaryPhone": customer.phone or "",
        }
        return bill_to

    @atomic()
    def handle_paywall_callback(self, request, *args, **kwargs):
        """
        Handle Elavon webhook notification and update payment status.

        Processes eventType from webhook:
        - saleAuthorized: Payment successful
        - saleDeclined: Payment failed
        - saleAuthorizationPending: Payment pending

        Returns:
            HttpResponse with status 200 to acknowledge webhook
        """

        payment = self.payment

        try:
            data = json.loads(request.body)
            event_type = data.get("eventType")

            logger.info(
                "Processing Elavon webhook",
                extra={
                    "payment_id": payment.id,
                    "event_type": event_type,
                    "notification_id": data.get("id"),
                },
            )

            if event_type == PaymentStatus.SALE_AUTHORIZED:
                payment.amount_paid = payment.amount_required
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

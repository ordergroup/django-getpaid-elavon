import requests


class Client:
    def __init__(self, merchant_id, user_id, pin, sandbox=True):
        self.merchant_id = merchant_id
        self.user_id = user_id
        self.pin = pin
        self.sandbox = sandbox
        self.orders_url = (
            "https://api.sandbox.elavon.com/orders"
            if sandbox
            else "https://api.elavon.com/orders"
        )
        self.sessions_url = (
            "https://api.sandbox.elavon.com/sessions"
            if sandbox
            else "https://api.elavon.com/sessions"
        )

    def create_order(self, order_id, amount, currency):
        payload = {
            "orderReference": str(order_id),
            "amount": f"{amount:.2f}",
            "currency": currency,
        }
        response = requests.post(self.orders_url, json=payload, headers=self._headers())
        response.raise_for_status()
        return response.json()  # Returns {'id': 'elavon_order_id', ...}

    def create_payment_session(
        self, elavon_order_url: str, return_url: str, cancel_url: str
    ):
        """
        Create payment session for Hosted Payments Redirect.

        Args:
            elavon_order_url: Full Elavon API URL of the order resource (e.g. https://uat.api.converge.eu.elavonaws.com/orders/txdjjwg49k4pdkcyyhbpb9tffmbg)
            return_url: User redirect URL after payment success/cancel
            cancel_url: User redirect URL if payment is canceled

        Returns:
            Dict containing session details including 'href' URL for redirect
        """
        payload = {
            "order": elavon_order_url,
            "returnUrl": return_url,
            "cancelUrl": cancel_url,
            "doCreateTransaction": "true",
        }
        response = requests.post(
            self.sessions_url, json=payload, headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.pin}",  # Example header
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

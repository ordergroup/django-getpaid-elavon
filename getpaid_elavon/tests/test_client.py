import uuid

import pytest
from requests.exceptions import HTTPError


class TestClientElavon:
    session_url = "https://uat.api.converge.eu.elavonaws.com/payment-sessions"
    order_url = "https://uat.api.converge.eu.elavonaws.com/orders"

    def test_create_order_success(
        self, client, order, expected_payload, mock_order_response, requests_mock
    ):
        requests_mock.post(self.order_url, json=mock_order_response, status_code=201)

        result = client.create_order(order, custom_reference=uuid.uuid4())

        assert result == mock_order_response
        assert result["id"] == "elavon_order_123"
        assert (
            result["href"]
            == "https://uat.api.converge.eu.elavonaws.com/orders/elavon_order_123"
        )

        assert requests_mock.call_count == 1
        request = requests_mock.last_request
        request_payload = request.json()
        assert request_payload["orderReference"] == expected_payload["orderReference"]
        assert request_payload["total"] == expected_payload["total"]
        assert request_payload["description"] == expected_payload["description"]
        assert request_payload["items"] == expected_payload["items"]
        assert "customReference" in request_payload

    def test_create_order_handles_http_401_error(self, client, order, requests_mock):
        error_response = {
            "status": 401,
            "failures": [
                {
                    "code": "unauthorized",
                    "description": "A valid API key is required",
                    "field": None,
                }
            ],
        }
        requests_mock.post(self.order_url, json=error_response, status_code=401)

        with pytest.raises(HTTPError) as exc_info:
            client.create_order(order, custom_reference=uuid.uuid4())

        assert exc_info.value.response.status_code == 401

    def test_create_payment_session_success(self, client, requests_mock):
        elavon_order_url = (
            "https://uat.api.converge.eu.elavonaws.com/orders/test_order_123"
        )

        mock_response = {
            "href": "https://uat.hpp.converge.eu.elavonaws.com/pay/test_session_123",
            "id": "test_session_123",
            "order": elavon_order_url,
        }

        requests_mock.post(self.session_url, json=mock_response, status_code=201)

        result = client.create_payment_session(
            elavon_order_url=elavon_order_url,
            return_url="https://example.com/payment/success",
            cancel_url="https://example.com/payment/cancel",
            custom_reference=uuid.uuid4(),
        )

        assert result == mock_response
        assert (
            result["href"]
            == "https://uat.hpp.converge.eu.elavonaws.com/pay/test_session_123"
        )
        assert result["id"] == "test_session_123"

    def test_create_payment_session_handles_http_401_error(self, client, requests_mock):
        error_response = {
            "status": 401,
            "failures": [
                {
                    "code": "unauthorized",
                    "description": "A valid API key is required",
                    "field": None,
                }
            ],
        }
        requests_mock.post(self.session_url, json=error_response, status_code=401)

        with pytest.raises(HTTPError) as exc_info:
            client.create_payment_session(
                elavon_order_url="https://uat.api.converge.eu.elavonaws.com/orders/order_123",
                return_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
                custom_reference=uuid.uuid4(),
            )

        assert exc_info.value.response.status_code == 401

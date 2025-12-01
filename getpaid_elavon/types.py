from enum import Enum
from typing import Optional, TypedDict


class PaymentStatus(str, Enum):
    SALE_AUTHORIZED = "saleAuthorized"
    SALE_DECLINED = "saleDeclined"
    SALE_AUTHORIZATION_PENDING = "saleAuthorizationPending"
    EXPIRED = "expired"


class BillingData(TypedDict):
    countryCode: Optional[str]
    company: Optional[str]
    street1: Optional[str]
    city: Optional[str]
    postalCode: Optional[str]


class BuyerData(TypedDict):
    email: str
    phone: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    billing: Optional[BillingData]

from enum import Enum


class PaymentStatus(str, Enum):
    SALE_AUTHORIZED = "saleAuthorized"
    SALE_DECLINED = "saleDeclined"
    SALE_AUTHORIZATION_PENDING = "saleAuthorizationPending"
    EXPIRED = "expired"

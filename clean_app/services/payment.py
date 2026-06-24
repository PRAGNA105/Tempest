# services/payment.py
# Payment service wiring — local endpoints only, no upstream references.

from clean_app.data import db_client
from clean_app.config import aliases
from clean_app.config.staging import STAGING_DB_URL

PAYMENTS_ENDPOINT = aliases.ENDPOINT_MAP.get(
    "payments", "http://localhost:8080/v2/payments"
)
DB_URL = STAGING_DB_URL


def charge(account_id, amount_cents):
    """Pretend to charge an account; returns the wiring it would use."""
    return {
        "account": account_id,
        "amount_cents": amount_cents,
        "endpoint": PAYMENTS_ENDPOINT,
        "db": db_client.get_connection_string(),
    }

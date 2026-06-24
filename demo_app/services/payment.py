# services/payment.py
# Payment service wiring.
#
# P-12: this module sits at the head of a 3-hop import chain that bottoms out
# at production:
#
#     payment -> db_client -> aliases -> staging
#
# It imports db_client (data), aliases (config) and PROD_DB_URL straight from
# config.staging. The hardcoded endpoint fallback below also leaks a prod URL
# directly into the payment module.

from demo_app.data import db_client
from demo_app.config import aliases
from demo_app.config.staging import PROD_DB_URL

# Hardcoded production fallback — leaks prod.company.com into this file.
PAYMENTS_ENDPOINT = aliases.ENDPOINT_MAP.get(
    "payments", "https://api.prod.company.com/v2/payments"
)
DB_URL = PROD_DB_URL


def charge(account_id, amount_cents):
    """Pretend to charge an account; returns the wiring it would use."""
    return {
        "account": account_id,
        "amount_cents": amount_cents,
        "endpoint": PAYMENTS_ENDPOINT,
        "db": db_client.get_connection_string(),
    }

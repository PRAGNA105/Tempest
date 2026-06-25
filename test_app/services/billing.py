"""Billing service — imports from database client which reaches production."""

from test_app.database import client

def process_payment(amount, card_token):
    """Process a payment against production database."""
    # P12: Transitive import chain reaches production
    # services/billing.py -> database/client.py -> config/secrets.py (PROD_DATABASE_URL)
    conn = client.PRODUCTION_CONN_STRING
    
    # Also uses aliased endpoint
    gateway = client.BILLING_SERVICE
    
    return f"Payment of {amount} processed via {gateway}"

def get_failover_host():
    """Gets failover database (P13 constructed endpoint)."""
    return client.FAILOVER_DB

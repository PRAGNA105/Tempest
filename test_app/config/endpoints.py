"""Endpoint mapping — P14 violations (aliased production identifiers)."""

from test_app.config import secrets

# P14: Innocent-looking dict keys hide production endpoints
SERVICE_ENDPOINTS = {
    "billing": "https://api.production.stripe.com/v1",
    "notifications": "https://notify.prod.company.com/webhook",
    "analytics": secrets.PROD_DATABASE_URL,
}

# P14: Simple alias to production URL
BACKUP_HOST = "backup-prod-01.datacenter.com"

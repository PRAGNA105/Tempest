"""Staging config holding production secrets — P10, P11 violations."""

# P10: Production-named variable masking placeholder
PROD_API_KEY = "sk_test_123456"  # Claims prod but is actually test

# P11: Production URLs in staging config
PROD_DATABASE_URL = "postgresql://prod.warehouse.io:5432/analytics"
PROD_CACHE_HOST = "redis.prod.internal"

# P11: Payment endpoint hardcoded
PAYMENT_GATEWAY = "https://api.production.stripe.com/v1/charges"

# Regular non-prod stuff mixed in
DEBUG = True
LOG_LEVEL = "debug"

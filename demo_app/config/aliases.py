# config/aliases.py
# Friendly service aliases mapping to "upstream" endpoints.
#
# P-14: a dict whose innocent-looking keys ("payments", "notify") hide
# production URLs as their values. Also forms hop 3 of the import chain by
# pulling PROD_DB_URL out of the staging module.

from demo_app.config.staging import PROD_DB_URL  # noqa: F401  (hop -> staging)

ENDPOINT_MAP = {
    "payments": "https://api.prod.company.com/v2/payments",
    "notify": "https://api.prod.company.com/v2/notify",
}


def resolve(alias):
    """Return the endpoint URL for a given alias, or None if unknown."""
    return ENDPOINT_MAP.get(alias)

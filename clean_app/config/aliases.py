# config/aliases.py
# Friendly service aliases mapping to local endpoints only.

from clean_app.config.staging import STAGING_DB_URL  # noqa: F401

ENDPOINT_MAP = {
    "payments": "http://localhost:8080/v2/payments",
    "notify": "http://localhost:8080/v2/notify",
}


def resolve(alias):
    """Return the endpoint URL for a given alias, or None if unknown."""
    return ENDPOINT_MAP.get(alias)

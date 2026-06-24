# data/db_client.py
# Builds the database connection string dynamically — staging host only.

from clean_app.config.aliases import ENDPOINT_MAP  # noqa: F401

BASE = "postgresql://"
HOST = "staging.internal"
conn_str = BASE + HOST + "/maindb"


def get_connection_string():
    """Return the dynamically assembled connection string."""
    return conn_str

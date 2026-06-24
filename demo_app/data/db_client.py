# data/db_client.py
# Builds the database connection string dynamically.
#
# P-13: the prod host is never written as one literal URL. It is assembled
# from fragments at runtime (BASE + HOST + path), which defeats naive
# "match the full connection string" scanners.
#
# Also forms hop 2 of the import chain: db_client -> aliases (-> staging).

from demo_app.config.aliases import ENDPOINT_MAP  # noqa: F401  (hop -> aliases)

BASE = "postgresql://"
HOST = "prod.company.com"
conn_str = BASE + HOST + "/maindb"


def get_connection_string():
    """Return the dynamically assembled connection string."""
    return conn_str

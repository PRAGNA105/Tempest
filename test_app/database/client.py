"""Database client — P12, P13 violations."""

from test_app.config import secrets, endpoints

# P13: Dynamic construction of production endpoint
PROTOCOL = "postgresql://"
HOST = "prod.warehouse.io"
PORT = "5432"
DB_NAME = "analytics"

# Constructed dynamically from fragments
PRODUCTION_CONN_STRING = PROTOCOL + HOST + ":" + PORT + "/" + DB_NAME

# P12: Importing production sinks from staging config
ACTIVE_DATABASE = secrets.PROD_DATABASE_URL

# Another P13 pattern: f-string construction
region = "us-east"
availability_zone = "1a"
FAILOVER_DB = f"postgresql://prod-{region}-{availability_zone}.db.company.com:5432/main"

# Alias to endpoint mapping
BILLING_SERVICE = endpoints.SERVICE_ENDPOINTS.get("billing")

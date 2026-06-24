# staging config
# Settings for the (allegedly) staging environment.
#
# P-11: a hardcoded production database URL living inside a file that is
# clearly named "staging". The name says staging; the value says prod.
#
# P-10: a variable whose *name* claims production but whose *value* is a
# local placeholder. The name says prod; the value says localhost. Anyone
# trusting the name to point at the real cache would silently hit localhost.

PROD_DB_URL = "postgresql://prod.company.com:5432/maindb"

PROD_CACHE_URL = "http://localhost:6379"

TIMEOUT_SECONDS = 30
POOL_SIZE = 10

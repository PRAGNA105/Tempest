# Scanner Specification

Scanner findings are deterministic facts discovered from repository content.

## Scanner Interface

Every scanner implements:

```python
scan(repository_path: Path) -> list[Finding]
```

Scanners must be deterministic, independently testable, and must not mutate
repository files.

## Traversal Rules

Repository traversal reads text-like files only and skips generated or
dependency-heavy paths:

- `.git`
- `.venv`
- `venv`
- `__pycache__`
- `build`
- `dist`
- `node_modules`
- `graphify-out`
- `state`

Files larger than 1 MB are skipped by default. Files containing NUL bytes are
treated as binary and skipped. Terraform `.tf` and `.tfvars` files are included
as text-like infrastructure sources.

## Common Finding Fields

- `id`
- `value`
- `source_file`
- `line`
- `column`
- `confidence`
- `evidence`
- `metadata`

## SecretFinding

Additional fields:

- `secret_type`
- `entropy`

The current secret scanner detects:

- AWS access key IDs.
- Private key block markers.
- Generic assignments whose names include secret, token, API key, password,
  private key, or access key.

Secret findings persist redacted values and redacted evidence. The raw value is
not written to JSON output. A SHA-256 fingerprint and value length are stored in
metadata for deterministic correlation.

## URLFinding

Additional fields:

- `url`
- `scheme`
- `hostname`
- `environment_hint`

The current URL scanner detects `http` and `https` URLs, records line and
column, derives hostname and scheme, and assigns environment hints for
production, staging, development, test, and QA indicators.

## DatabaseFinding

Additional fields:

- `database_type`
- `host`
- `database_name`
- `environment_hint`

The current database scanner detects:

- PostgreSQL URLs.
- MySQL URLs.
- MariaDB URLs.
- MongoDB and MongoDB SRV URLs.
- Redis and Rediss URLs.
- SQL Server and MSSQL URLs.
- JDBC URLs for supported database families.
- Database host, endpoint, and server assignments.

Database URL findings redact credentials in persisted values and evidence while
retaining deterministic host, database name, scheme, confidence, and
environment hint metadata.

## CloudResourceFinding

Additional fields:

- `provider`: `aws`, `azure`, or `gcp`
- `resource_type`
- `resource_id`
- `region`

The current cloud resource scanner detects:

- AWS ARNs.
- AWS S3 bucket references through `s3://` URIs and S3 HTTPS URLs.
- AWS IAM role, policy, user, and group references.
- AWS Lambda function references.
- Azure Storage account URLs and assignments.
- Azure Key Vault URLs and assignments.
- Azure resource IDs under `/subscriptions/.../resourceGroups/...`.
- GCP project ID assignments.
- GCP GCS bucket references through `gs://` URIs and GCS HTTPS URLs.
- GCP service account emails.

Cloud resource findings store provider, resource type, resource ID, optional
region, source location, confidence, evidence, and scanner metadata.

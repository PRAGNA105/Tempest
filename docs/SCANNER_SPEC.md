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
treated as binary and skipped.

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

## CloudResourceFinding

Additional fields:

- `provider`: `aws`, `azure`, or `gcp`
- `resource_type`
- `resource_id`
- `region`

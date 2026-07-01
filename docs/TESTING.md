# Testing

## How To Run Tests

```bash
python -m pytest
```

## Test Strategy

- Contract tests validate pydantic model creation and field behavior.
- Adapter tests validate the Graphify adapter boundary.
- RIM export tests validate graph and scanner finding conversion.

## Coverage Status

Initial tests cover the repository graph contracts, scanner contracts, stub
adapter, Graphify JSON adapter, RIM builder, and JSON exporter. Scanner
foundation behavior, URL scanning, and persistence are also covered. Secret,
database, cloud scanner implementations and leak detection do not exist yet.

## Latest Local Run

- `python -m pytest`: 14 passed.
- `python -m ruff check .`: not run successfully because `ruff` is not
  installed in the active Python environment.

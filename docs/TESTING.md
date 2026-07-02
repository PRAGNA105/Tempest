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
foundation behavior, URL scanning, secret scanning, database scanning, cloud
resource scanning, environment discovery, persistence, traversal rules, and RIM
cloud node mapping are covered. Production boundary discovery, graph
annotation, leak detection, evidence generation, reports, and CLI do not exist
yet.

## Latest Local Run

- `python -m pytest`: 37 passed.
- `python -m ruff check scripts\discover_environments.py src\environment tests\test_environment_discovery.py`:
  passed.
- `python -m ruff check .`: fails on existing lint findings outside the new
  environment discovery files.

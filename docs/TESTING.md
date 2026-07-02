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
resource scanning, environment discovery, persistence, traversal rules, RIM
cloud node mapping, production boundary discovery, graph annotation, and leak
detection policies, evidence generation, and report generation are covered. CLI
does not exist yet.

## Latest Local Run

- `python -m pytest`: 68 passed.
- `python -m ruff check src\reports tests\test_reports.py`: passed.
- `python -m ruff check src\evidence tests\test_evidence.py`: passed.
- `python -m ruff check src\detection tests\test_detection.py`: passed.
- `python -m ruff check src\annotation tests\test_annotation.py`: passed.
- `python -m ruff check scripts\discover_environments.py src\environment tests\test_environment_discovery.py`:
  passed.
- `python -m ruff check .`: has documented existing lint findings outside the
  latest report files.

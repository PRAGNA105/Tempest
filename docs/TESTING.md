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
cloud node mapping, production boundary discovery, graph annotation, leak
detection policies, evidence generation, report generation, and CLI
orchestration are covered. Optional Graphify CLI invocation is covered with a
fake command that writes Graphify-compatible JSON.

## Latest Local Run

- `python -m pytest`: 75 passed.
- `python -m ruff check src\graphify_adapter\cli.py src\graphify_adapter\__init__.py src\rilde_cli tests\test_graphify_json_adapter.py tests\test_cli.py`:
  passed.
- `python -m ruff check src\rilde_cli tests\test_cli.py`: passed.
- `python -m ruff check src\reports tests\test_reports.py`: passed.
- `python -m ruff check src\evidence tests\test_evidence.py`: passed.
- `python -m ruff check src\detection tests\test_detection.py`: passed.
- `python -m ruff check src\annotation tests\test_annotation.py`: passed.
- `python -m ruff check scripts\discover_environments.py src\environment tests\test_environment_discovery.py`:
  passed.
- `python -m ruff check .`: has documented existing lint findings outside the
  latest report files.

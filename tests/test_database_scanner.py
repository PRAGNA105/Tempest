import json

from scanners import DatabaseScanner, TraversalRules, save_findings_json


def test_database_scanner_finds_standard_database_urls_and_redacts_credentials(tmp_path):
    (tmp_path / "settings.env").write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://user:pass@prod-db.example.com:5432/app",
                "CACHE_URL=redis://localhost:6379/0",
                "MONGO_URL=mongodb+srv://cluster.prod.example.com/main",
            ]
        ),
        encoding="utf-8",
    )

    findings = DatabaseScanner().scan(tmp_path)

    assert [finding.database_type for finding in findings] == [
        "postgresql",
        "redis",
        "mongodb",
    ]
    assert findings[0].value == "postgresql://<credentials>@prod-db.example.com:5432/app"
    assert findings[0].host == "prod-db.example.com"
    assert findings[0].database_name == "app"
    assert findings[0].environment_hint == "production"
    assert findings[0].metadata["credentials_redacted"] is True
    assert findings[1].confidence == 0.75
    assert findings[1].environment_hint == "development"


def test_database_scanner_finds_jdbc_urls(tmp_path):
    (tmp_path / "application.properties").write_text(
        "\n".join(
            [
                "spring.datasource.url=jdbc:mysql://staging-db.example.com:3306/app",
                "legacy.url=jdbc:sqlserver://qa-db.example.com:1433;databaseName=legacy",
            ]
        ),
        encoding="utf-8",
    )

    findings = DatabaseScanner().scan(tmp_path)

    assert [finding.database_type for finding in findings] == ["mysql", "sqlserver"]
    assert findings[0].host == "staging-db.example.com"
    assert findings[0].database_name == "app"
    assert findings[0].environment_hint == "staging"
    assert findings[1].host == "qa-db.example.com"
    assert findings[1].database_name == "legacy"
    assert findings[1].environment_hint == "qa"


def test_database_scanner_finds_database_host_assignments(tmp_path):
    (tmp_path / "settings.py").write_text(
        "\n".join(
            [
                "POSTGRES_HOST = 'prod-postgres.example.com'",
                "DATABASE_ENDPOINT=primary-db.internal.example.org:5432",
            ]
        ),
        encoding="utf-8",
    )

    findings = DatabaseScanner().scan(tmp_path)

    assert [finding.database_type for finding in findings] == ["postgresql", "database"]
    assert findings[0].host == "prod-postgres.example.com"
    assert findings[0].environment_hint == "production"
    assert findings[1].host == "primary-db.internal.example.org:5432"


def test_database_scanner_respects_custom_traversal_rules(tmp_path):
    (tmp_path / "settings.env").write_text(
        "DATABASE_URL=postgresql://prod-db.example.com/app\n",
        encoding="utf-8",
    )
    rules = TraversalRules(text_extensions=frozenset({".py"}), include_extensionless=False)

    assert DatabaseScanner(rules).scan(tmp_path) == []


def test_save_findings_json_persists_database_output(tmp_path):
    (tmp_path / "settings.env").write_text(
        "MYSQL_URL=mysql://prod-db.example.com/app\n",
        encoding="utf-8",
    )
    findings = DatabaseScanner().scan(tmp_path)

    output = save_findings_json(findings, tmp_path / "state" / "database_findings.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload[0]["finding_type"] == "DatabaseFinding"
    assert payload[0]["database_type"] == "mysql"
    assert payload[0]["environment_hint"] == "production"


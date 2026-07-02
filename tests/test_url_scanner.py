import json

from scanners import TraversalRules, URLScanner, iter_source_files, save_findings_json


def test_iter_source_files_skips_excluded_dirs_and_binary_files(tmp_path):
    (tmp_path / "app.py").write_text("BASE_URL = 'https://prod.example.com'\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("https://ignored.example.com\n", encoding="utf-8")
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "url_findings.json").write_text(
        "https://generated.example.com\n",
        encoding="utf-8",
    )
    (tmp_path / "image.png").write_bytes(b"\x00\x01\x02")

    files = list(iter_source_files(tmp_path))

    assert [source.relative_path for source in files] == ["app.py"]


def test_url_scanner_finds_urls_with_location_and_environment_hint(tmp_path):
    (tmp_path / "settings.py").write_text(
        "\n".join(
            [
                "API_URL = 'https://api.prod.example.com/v1'",
                "LOCAL_URL = 'http://localhost:8000/callback'",
            ]
        ),
        encoding="utf-8",
    )

    findings = URLScanner().scan(tmp_path)

    assert [finding.url for finding in findings] == [
        "https://api.prod.example.com/v1",
        "http://localhost:8000/callback",
    ]
    assert findings[0].source_file == "settings.py"
    assert findings[0].line == 1
    assert findings[0].column == 12
    assert findings[0].hostname == "api.prod.example.com"
    assert findings[0].environment_hint == "production"
    assert findings[1].environment_hint == "development"
    assert findings[1].confidence == 0.7


def test_url_scanner_respects_custom_traversal_rules(tmp_path):
    (tmp_path / "README.md").write_text("https://docs.example.com\n", encoding="utf-8")
    rules = TraversalRules(text_extensions=frozenset({".py"}), include_extensionless=False)

    findings = URLScanner(rules).scan(tmp_path)

    assert findings == []


def test_url_scanner_stops_before_escaped_newline_in_source_literals(tmp_path):
    (tmp_path / "literal.py").write_text(
        'URL = "https://ignored.example.com\\n"\n',
        encoding="utf-8",
    )

    findings = URLScanner().scan(tmp_path)

    assert findings[0].url == "https://ignored.example.com"
    assert findings[0].hostname == "ignored.example.com"


def test_url_scanner_handles_markdown_links_without_merging_urls(tmp_path):
    (tmp_path / "README.md").write_text(
        "Open [http://localhost:3000](http://localhost:3000) to view it.\n",
        encoding="utf-8",
    )

    findings = URLScanner().scan(tmp_path)

    assert len(findings) == 1
    assert findings[0].url == "http://localhost:3000"
    assert findings[0].hostname == "localhost"
    assert findings[0].confidence == 0.7


def test_save_findings_json_persists_scanner_output(tmp_path):
    (tmp_path / "config.env").write_text("PUBLIC_URL=https://staging.example.com\n", encoding="utf-8")
    findings = URLScanner().scan(tmp_path)

    output = save_findings_json(findings, tmp_path / "state" / "url_findings.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert output.exists()
    assert payload[0]["finding_type"] == "URLFinding"
    assert payload[0]["environment_hint"] == "staging"

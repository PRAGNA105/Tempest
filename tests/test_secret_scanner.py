import json

from scanners import SecretScanner, TraversalRules, save_findings_json, shannon_entropy


def test_shannon_entropy_scores_repetitive_values_lower_than_random_like_values():
    assert shannon_entropy("aaaaaaaaaaaaaaaa") < shannon_entropy("Ab9xYz73QpLm2N0v")


def test_secret_scanner_finds_common_secret_patterns_with_redaction(tmp_path):
    (tmp_path / "settings.env").write_text(
        "\n".join(
            [
                "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE",
                "SERVICE_TOKEN = 'Ab9xYz73QpLm2N0vR8sT'",
                "PLACEHOLDER_SECRET=changeme",
            ]
        ),
        encoding="utf-8",
    )

    findings = SecretScanner().scan(tmp_path)

    assert [finding.secret_type for finding in findings] == [
        "aws_access_key_id",
        "generic_secret_assignment",
    ]
    assert findings[0].value == "AKIA...MPLE"
    assert findings[0].source_file == "settings.env"
    assert findings[0].line == 1
    assert findings[0].column == 19
    assert findings[0].metadata["fingerprint"]
    assert findings[1].evidence == "SERVICE_TOKEN=Ab9x...R8sT"
    assert findings[1].entropy >= 3.0


def test_secret_scanner_finds_private_key_marker(tmp_path):
    (tmp_path / "key.pem").write_text(
        "-----BEGIN PRIVATE KEY-----\nnot-real-key\n-----END PRIVATE KEY-----\n",
        encoding="utf-8",
    )

    findings = SecretScanner().scan(tmp_path)

    assert findings[0].secret_type == "private_key"
    assert findings[0].value == "PRIV... KEY"


def test_secret_scanner_respects_custom_traversal_rules(tmp_path):
    (tmp_path / "settings.env").write_text(
        "TOKEN=Ab9xYz73QpLm2N0vR8sT\n",
        encoding="utf-8",
    )
    rules = TraversalRules(text_extensions=frozenset({".py"}), include_extensionless=False)

    assert SecretScanner(rules).scan(tmp_path) == []


def test_secret_scanner_ignores_constructor_assignment_false_positive(tmp_path):
    (tmp_path / "test_contracts.py").write_text(
        "secret = SecretFinding(\n    value='redacted',\n)\n",
        encoding="utf-8",
    )

    assert SecretScanner().scan(tmp_path) == []


def test_save_findings_json_persists_redacted_secret_output(tmp_path):
    (tmp_path / "settings.env").write_text(
        "API_KEY=Ab9xYz73QpLm2N0vR8sT\n",
        encoding="utf-8",
    )
    findings = SecretScanner().scan(tmp_path)

    output = save_findings_json(findings, tmp_path / "state" / "secret_findings.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload[0]["finding_type"] == "SecretFinding"
    assert payload[0]["value"] == "Ab9x...R8sT"
    assert payload[0]["metadata"]["value_length"] == 20

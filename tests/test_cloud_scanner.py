import json

from rim import build_rim
from graph import RepositoryGraph
from scanners import CloudProvider, CloudResourceScanner, TraversalRules, save_findings_json


def test_cloud_scanner_finds_aws_arn_s3_iam_and_lambda_references(tmp_path):
    (tmp_path / "infra.env").write_text(
        "\n".join(
            [
                "TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:prod-alerts",
                "ASSET_BUCKET=s3://prod-assets-bucket/releases/app.zip",
                "AWS_IAM_ROLE=prod-app-role",
                "AWS_LAMBDA_FUNCTION=prod-worker",
            ]
        ),
        encoding="utf-8",
    )

    findings = CloudResourceScanner().scan(tmp_path)

    assert [(finding.provider, finding.resource_type, finding.resource_id) for finding in findings] == [
        (CloudProvider.AWS, "sns_resource", "prod-alerts"),
        (CloudProvider.AWS, "s3_bucket", "prod-assets-bucket"),
        (CloudProvider.AWS, "iam_role", "prod-app-role"),
        (CloudProvider.AWS, "lambda_function", "prod-worker"),
    ]
    assert findings[0].region == "us-east-1"
    assert findings[0].metadata["account_id"] == "123456789012"
    assert findings[1].metadata["source"] == "aws_s3_uri"
    assert findings[2].evidence == "AWS_IAM_ROLE=prod-app-role"


def test_cloud_scanner_finds_aws_service_specific_arns(tmp_path):
    (tmp_path / "policy.json").write_text(
        "\n".join(
            [
                '"Role": "arn:aws:iam::123456789012:role/Admin",',
                '"Function": "arn:aws:lambda:eu-west-1:123456789012:function:payments-prod"',
                '"Bucket": "arn:aws:s3:::prod-audit-logs"',
            ]
        ),
        encoding="utf-8",
    )

    findings = CloudResourceScanner().scan(tmp_path)

    assert [(finding.resource_type, finding.resource_id) for finding in findings] == [
        ("iam_role", "Admin"),
        ("lambda_function", "payments-prod"),
        ("s3_bucket", "prod-audit-logs"),
    ]
    assert findings[1].region == "eu-west-1"


def test_cloud_scanner_finds_azure_storage_key_vault_and_resource_ids(tmp_path):
    (tmp_path / "azure.yaml").write_text(
        "\n".join(
            [
                "storage: https://prodstorage01.blob.core.windows.net/assets",
                "vault: https://prod-vault.vault.azure.net/secrets/api-key",
                (
                    "id: /subscriptions/11111111-2222-3333-4444-555555555555/"
                    "resourceGroups/prod-rg/providers/Microsoft.Storage/"
                    "storageAccounts/prodstorage01"
                ),
            ]
        ),
        encoding="utf-8",
    )

    findings = CloudResourceScanner().scan(tmp_path)

    assert [(finding.provider, finding.resource_type, finding.resource_id) for finding in findings] == [
        (CloudProvider.AZURE, "storage_account", "prodstorage01"),
        (CloudProvider.AZURE, "key_vault", "prod-vault"),
        (CloudProvider.AZURE, "storage_account", "prodstorage01"),
    ]
    assert findings[2].metadata["subscription_id"] == "11111111-2222-3333-4444-555555555555"
    assert findings[2].metadata["resource_group"] == "prod-rg"


def test_cloud_scanner_finds_gcp_projects_gcs_buckets_and_service_accounts(tmp_path):
    (tmp_path / "gcp.tfvars").write_text(
        "\n".join(
            [
                'gcp_project_id = "prod-platform-123"',
                "bucket = gs://prod-platform-assets/path/file.txt",
                "service = deployer@prod-platform-123.iam.gserviceaccount.com",
            ]
        ),
        encoding="utf-8",
    )

    findings = CloudResourceScanner().scan(tmp_path)

    assert [(finding.provider, finding.resource_type, finding.resource_id) for finding in findings] == [
        (CloudProvider.GCP, "project", "prod-platform-123"),
        (CloudProvider.GCP, "gcs_bucket", "prod-platform-assets"),
        (
            CloudProvider.GCP,
            "service_account",
            "deployer@prod-platform-123.iam.gserviceaccount.com",
        ),
    ]
    assert findings[2].metadata["project_id"] == "prod-platform-123"


def test_cloud_scanner_respects_custom_traversal_rules(tmp_path):
    (tmp_path / "infra.env").write_text("AWS_LAMBDA_FUNCTION=prod-worker\n", encoding="utf-8")
    rules = TraversalRules(text_extensions=frozenset({".py"}), include_extensionless=False)

    assert CloudResourceScanner(rules).scan(tmp_path) == []


def test_save_findings_json_persists_cloud_output(tmp_path):
    (tmp_path / "infra.env").write_text("AWS_LAMBDA_FUNCTION=prod-worker\n", encoding="utf-8")
    findings = CloudResourceScanner().scan(tmp_path)

    output = save_findings_json(findings, tmp_path / "state" / "cloud_findings.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload[0]["finding_type"] == "CloudResourceFinding"
    assert payload[0]["provider"] == "aws"
    assert payload[0]["resource_type"] == "lambda_function"


def test_build_rim_maps_cloud_findings_to_cloud_resource_nodes(tmp_path):
    (tmp_path / "infra.env").write_text("AWS_LAMBDA_FUNCTION=prod-worker\n", encoding="utf-8")
    finding = CloudResourceScanner().scan(tmp_path)[0]

    rim = build_rim(RepositoryGraph(), [finding])

    assert rim.nodes[0].id == f"finding:{finding.id}"
    assert rim.nodes[0].kind.value == "cloud_resource"
    assert rim.nodes[0].label == "prod-worker"

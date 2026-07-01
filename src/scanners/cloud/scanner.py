from __future__ import annotations

import hashlib
from pathlib import Path
from re import Match, Pattern

from scanners.base import Scanner
from scanners.cloud.patterns import (
    AWS_ARN_PATTERN,
    AWS_IAM_ASSIGNMENT_PATTERN,
    AWS_LAMBDA_ASSIGNMENT_PATTERN,
    AWS_S3_HOST_PATTERN,
    AWS_S3_URI_PATTERN,
    AZURE_KEY_VAULT_ASSIGNMENT_PATTERN,
    AZURE_KEY_VAULT_URL_PATTERN,
    AZURE_RESOURCE_ID_PATTERN,
    AZURE_STORAGE_ASSIGNMENT_PATTERN,
    AZURE_STORAGE_URL_PATTERN,
    GCP_GCS_HOST_PATTERN,
    GCP_GCS_URI_PATTERN,
    GCP_PROJECT_ASSIGNMENT_PATTERN,
    GCP_SERVICE_ACCOUNT_PATTERN,
    TRAILING_PUNCTUATION,
)
from scanners.models import CloudProvider, CloudResourceFinding
from scanners.traversal import TraversalRules, iter_source_files


class CloudResourceScanner(Scanner):
    name = "cloud_resource_scanner"

    def __init__(self, traversal_rules: TraversalRules | None = None) -> None:
        self.traversal_rules = traversal_rules

    def scan(self, repository_path: Path) -> list[CloudResourceFinding]:
        findings: list[CloudResourceFinding] = []
        seen: set[tuple[str, int, int, str, str, str]] = set()

        for source_file in iter_source_files(repository_path, self.traversal_rules):
            text = source_file.text

            for match in AWS_ARN_PATTERN.finditer(text):
                value = _clean(match.group("arn"))
                service = match.group("service").lower()
                resource = _clean(match.group("resource"))
                resource_type, resource_id = _aws_arn_resource(service, resource)
                region = match.group("region") or None
                metadata = {
                    "scanner": self.name,
                    "source": "aws_arn",
                    "partition": match.group("partition"),
                    "service": service,
                    "account_id": match.group("account_id") or None,
                }
                _append_finding(
                    findings,
                    seen,
                    source_file.relative_path,
                    text,
                    match.start("arn"),
                    provider=CloudProvider.AWS,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    value=value,
                    region=region,
                    confidence=0.95,
                    evidence=value,
                    metadata=metadata,
                )

            self._scan_bucket_like(
                findings,
                seen,
                source_file.relative_path,
                text,
                provider=CloudProvider.AWS,
                resource_type="s3_bucket",
                uri_pattern=AWS_S3_URI_PATTERN,
                host_pattern=AWS_S3_HOST_PATTERN,
                uri_source="aws_s3_uri",
                host_source="aws_s3_url",
            )

            self._scan_assignment(
                findings,
                seen,
                source_file.relative_path,
                text,
                AWS_IAM_ASSIGNMENT_PATTERN,
                provider=CloudProvider.AWS,
                resource_type_factory=_aws_iam_assignment_type,
                source="aws_iam_assignment",
                confidence=0.85,
            )
            self._scan_assignment(
                findings,
                seen,
                source_file.relative_path,
                text,
                AWS_LAMBDA_ASSIGNMENT_PATTERN,
                provider=CloudProvider.AWS,
                resource_type_factory=lambda _name: "lambda_function",
                source="aws_lambda_assignment",
                confidence=0.85,
            )

            for match in AZURE_RESOURCE_ID_PATTERN.finditer(text):
                value = _clean(match.group("resource_id"))
                resource_type = _azure_resource_type(match.group("provider"), match.group("resource_type"))
                metadata = {
                    "scanner": self.name,
                    "source": "azure_resource_id",
                    "subscription_id": match.group("subscription_id"),
                    "resource_group": match.group("resource_group"),
                    "provider_namespace": match.group("provider"),
                    "provider_resource_type": match.group("resource_type"),
                }
                _append_finding(
                    findings,
                    seen,
                    source_file.relative_path,
                    text,
                    match.start("resource_id"),
                    provider=CloudProvider.AZURE,
                    resource_type=resource_type,
                    resource_id=_clean(match.group("name")),
                    value=value,
                    region=None,
                    confidence=0.95,
                    evidence=value,
                    metadata=metadata,
                )

            self._scan_single_group(
                findings,
                seen,
                source_file.relative_path,
                text,
                AZURE_STORAGE_URL_PATTERN,
                group_name="account",
                provider=CloudProvider.AZURE,
                resource_type="storage_account",
                source="azure_storage_url",
                confidence=0.92,
            )
            self._scan_assignment(
                findings,
                seen,
                source_file.relative_path,
                text,
                AZURE_STORAGE_ASSIGNMENT_PATTERN,
                provider=CloudProvider.AZURE,
                resource_type_factory=lambda _name: "storage_account",
                source="azure_storage_assignment",
                confidence=0.85,
            )
            self._scan_single_group(
                findings,
                seen,
                source_file.relative_path,
                text,
                AZURE_KEY_VAULT_URL_PATTERN,
                group_name="vault",
                provider=CloudProvider.AZURE,
                resource_type="key_vault",
                source="azure_key_vault_url",
                confidence=0.92,
            )
            self._scan_assignment(
                findings,
                seen,
                source_file.relative_path,
                text,
                AZURE_KEY_VAULT_ASSIGNMENT_PATTERN,
                provider=CloudProvider.AZURE,
                resource_type_factory=lambda _name: "key_vault",
                source="azure_key_vault_assignment",
                confidence=0.82,
            )

            self._scan_assignment(
                findings,
                seen,
                source_file.relative_path,
                text,
                GCP_PROJECT_ASSIGNMENT_PATTERN,
                provider=CloudProvider.GCP,
                resource_type_factory=lambda _name: "project",
                source="gcp_project_assignment",
                confidence=0.82,
            )
            self._scan_bucket_like(
                findings,
                seen,
                source_file.relative_path,
                text,
                provider=CloudProvider.GCP,
                resource_type="gcs_bucket",
                uri_pattern=GCP_GCS_URI_PATTERN,
                host_pattern=GCP_GCS_HOST_PATTERN,
                uri_source="gcp_gcs_uri",
                host_source="gcp_gcs_url",
            )

            for match in GCP_SERVICE_ACCOUNT_PATTERN.finditer(text):
                value = _clean(match.group("email"))
                metadata = {
                    "scanner": self.name,
                    "source": "gcp_service_account",
                    "project_id": match.group("project_id"),
                }
                _append_finding(
                    findings,
                    seen,
                    source_file.relative_path,
                    text,
                    match.start("email"),
                    provider=CloudProvider.GCP,
                    resource_type="service_account",
                    resource_id=value,
                    value=value,
                    region=None,
                    confidence=0.95,
                    evidence=value,
                    metadata=metadata,
                )

        return sorted(
            findings,
            key=lambda finding: (
                finding.source_file,
                finding.line or 0,
                finding.column or 0,
                finding.provider.value,
                finding.resource_type,
                finding.resource_id,
            ),
        )

    def _scan_bucket_like(
        self,
        findings: list[CloudResourceFinding],
        seen: set[tuple[str, int, int, str, str, str]],
        source_file: str,
        text: str,
        *,
        provider: CloudProvider,
        resource_type: str,
        uri_pattern: Pattern[str],
        host_pattern: Pattern[str],
        uri_source: str,
        host_source: str,
    ) -> None:
        for match in uri_pattern.finditer(text):
            value = _clean(match.group(0))
            bucket = _clean(match.group("bucket"))
            _append_finding(
                findings,
                seen,
                source_file,
                text,
                match.start("bucket"),
                provider=provider,
                resource_type=resource_type,
                resource_id=bucket,
                value=value,
                region=None,
                confidence=0.92,
                evidence=value,
                metadata={"scanner": self.name, "source": uri_source},
            )

        for match in host_pattern.finditer(text):
            value = _clean(match.group(0))
            bucket = _clean(match.groupdict().get("bucket") or match.groupdict().get("path_bucket") or "")
            region = match.groupdict().get("region") or match.groupdict().get("path_region")
            if not bucket:
                continue
            _append_finding(
                findings,
                seen,
                source_file,
                text,
                match.start(0),
                provider=provider,
                resource_type=resource_type,
                resource_id=bucket,
                value=value,
                region=region,
                confidence=0.92,
                evidence=value,
                metadata={"scanner": self.name, "source": host_source},
            )

    def _scan_assignment(
        self,
        findings: list[CloudResourceFinding],
        seen: set[tuple[str, int, int, str, str, str]],
        source_file: str,
        text: str,
        pattern: Pattern[str],
        *,
        provider: CloudProvider,
        resource_type_factory,
        source: str,
        confidence: float,
    ) -> None:
        for match in pattern.finditer(text):
            value = _clean(match.group("value"))
            if _is_non_resource_assignment_value(value):
                continue
            name = match.group("name")
            resource_type = resource_type_factory(name)
            _append_finding(
                findings,
                seen,
                source_file,
                text,
                match.start("value"),
                provider=provider,
                resource_type=resource_type,
                resource_id=value,
                value=value,
                region=None,
                confidence=confidence,
                evidence=f"{name}={value}",
                metadata={"scanner": self.name, "source": source, "name": name},
            )

    def _scan_single_group(
        self,
        findings: list[CloudResourceFinding],
        seen: set[tuple[str, int, int, str, str, str]],
        source_file: str,
        text: str,
        pattern: Pattern[str],
        *,
        group_name: str,
        provider: CloudProvider,
        resource_type: str,
        source: str,
        confidence: float,
    ) -> None:
        for match in pattern.finditer(text):
            value = _clean(match.group(0))
            resource_id = _clean(match.group(group_name))
            _append_finding(
                findings,
                seen,
                source_file,
                text,
                match.start(group_name),
                provider=provider,
                resource_type=resource_type,
                resource_id=resource_id,
                value=value,
                region=None,
                confidence=confidence,
                evidence=value,
                metadata={"scanner": self.name, "source": source},
            )


def _append_finding(
    findings: list[CloudResourceFinding],
    seen: set[tuple[str, int, int, str, str, str]],
    source_file: str,
    text: str,
    offset: int,
    *,
    provider: CloudProvider,
    resource_type: str,
    resource_id: str,
    value: str,
    region: str | None,
    confidence: float,
    evidence: str,
    metadata: dict[str, object],
) -> None:
    line, column = _line_column(text, offset)
    key = (source_file, line, column, provider.value, resource_type, resource_id)
    if key in seen:
        return
    seen.add(key)
    findings.append(
        CloudResourceFinding(
            id=_finding_id(source_file, line, column, provider.value, resource_type, resource_id),
            value=value,
            source_file=source_file,
            line=line,
            column=column,
            confidence=confidence,
            evidence=evidence,
            provider=provider,
            resource_type=resource_type,
            resource_id=resource_id,
            region=region,
            metadata=metadata,
        )
    )


def _aws_arn_resource(service: str, resource: str) -> tuple[str, str]:
    normalized = resource.replace(":", "/", 1)
    parts = normalized.split("/", 1)
    resource_kind = parts[0].lower() if len(parts) == 2 else ""
    resource_id = parts[1] if len(parts) == 2 else resource

    if service == "s3":
        return "s3_bucket", resource_id
    if service == "iam" and resource_kind in {"role", "policy", "user", "group"}:
        return f"iam_{resource_kind}", resource_id
    if service == "lambda" and resource_kind == "function":
        return "lambda_function", resource_id
    return f"{service}_resource", resource_id


def _aws_iam_assignment_type(name: str) -> str:
    lowered = name.lower()
    for suffix in ("role", "policy", "user", "group"):
        if suffix in lowered:
            return f"iam_{suffix}"
    return "iam_reference"


def _azure_resource_type(provider: str, resource_type: str) -> str:
    provider_l = provider.lower()
    resource_l = resource_type.lower()
    if provider_l == "microsoft.storage" and resource_l == "storageaccounts":
        return "storage_account"
    if provider_l == "microsoft.keyvault" and resource_l == "vaults":
        return "key_vault"
    return f"{provider_l.replace('microsoft.', '').replace('.', '_')}_{resource_l}"


def _line_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset)
    column = offset + 1 if line_start == -1 else offset - line_start
    return line, column


def _finding_id(
    source_file: str, line: int, column: int, provider: str, resource_type: str, resource_id: str
) -> str:
    digest = hashlib.sha256(
        f"cloud:{source_file}:{line}:{column}:{provider}:{resource_type}:{resource_id}".encode(
            "utf-8"
        )
    ).hexdigest()
    return f"cloud-{digest[:16]}"


def _clean(value: str) -> str:
    return value.rstrip(TRAILING_PUNCTUATION)


def _is_non_resource_assignment_value(value: str) -> bool:
    return value.lower() in {"http", "https", "arn", "s3", "gs"}

from __future__ import annotations

import re


AWS_ARN_PATTERN = re.compile(
    r"\b(?P<arn>arn:(?P<partition>aws[a-zA-Z-]*)?:"
    r"(?P<service>[a-z0-9-]+):"
    r"(?P<region>[a-z0-9-]*):"
    r"(?P<account_id>[0-9]{0,12}):"
    r"(?P<resource>[^\s<>'\"`\\]+))",
    re.IGNORECASE,
)

AWS_S3_URI_PATTERN = re.compile(
    r"\bs3://(?P<bucket>[a-z0-9][a-z0-9.-]{1,61}[a-z0-9])(?:/[^\s<>'\"`\\]*)?",
    re.IGNORECASE,
)

AWS_S3_HOST_PATTERN = re.compile(
    r"\bhttps?://(?:(?P<bucket>[a-z0-9][a-z0-9.-]{1,61}[a-z0-9])\."
    r"s3(?:[.-](?P<region>[a-z0-9-]+))?\.amazonaws\.com|"
    r"s3(?:[.-](?P<path_region>[a-z0-9-]+))?\.amazonaws\.com/"
    r"(?P<path_bucket>[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]))[^\s<>'\"`\\]*",
    re.IGNORECASE,
)

AWS_IAM_ASSIGNMENT_PATTERN = re.compile(
    r"""(?ix)
    (?<![:/])\b(?P<name>[a-z0-9_.-]*(?:aws[-_.])?iam[a-z0-9_.-]*(?:role|policy|user|group)[a-z0-9_.-]*)\b
    \s*[:=]\s*
    (?P<quote>["'])?
    (?P<value>[a-z0-9+=,.@_/-]{3,128})
    (?P=quote)?
    """,
)

AWS_LAMBDA_ASSIGNMENT_PATTERN = re.compile(
    r"""(?ix)
    (?<![:/])\b(?P<name>[a-z0-9_.-]*(?:aws[-_.])?lambda[a-z0-9_.-]*(?:function|name)?[a-z0-9_.-]*)\b
    \s*[:=]\s*
    (?P<quote>["'])?
    (?P<value>[a-z0-9-_.$]{3,140})
    (?P=quote)?
    """,
)

AZURE_RESOURCE_ID_PATTERN = re.compile(
    r"(?P<resource_id>/subscriptions/(?P<subscription_id>[0-9a-f-]{32,36})/"
    r"resourceGroups/(?P<resource_group>[^/\s<>'\"`\\]+)/providers/"
    r"(?P<provider>Microsoft\.[^/\s<>'\"`\\]+)/"
    r"(?P<resource_type>[^/\s<>'\"`\\]+)/"
    r"(?P<name>[^/\s<>'\"`\\]+)(?:/[^\s<>'\"`\\]+)*)",
    re.IGNORECASE,
)

AZURE_STORAGE_URL_PATTERN = re.compile(
    r"\bhttps?://(?P<account>[a-z0-9]{3,24})\."
    r"(?:blob|dfs|file|queue|table)\.core\.windows\.net(?:/[^\s<>'\"`\\]*)?",
    re.IGNORECASE,
)

AZURE_STORAGE_ASSIGNMENT_PATTERN = re.compile(
    r"""(?ix)
    (?<![:/])\b(?P<name>[a-z0-9_.-]*azure[a-z0-9_.-]*(?:storage|account)[a-z0-9_.-]*)\b
    \s*[:=]\s*
    (?P<quote>["'])?
    (?P<value>[a-z0-9]{3,24})
    (?P=quote)?
    """,
)

AZURE_KEY_VAULT_URL_PATTERN = re.compile(
    r"\bhttps?://(?P<vault>[a-z0-9-]{3,24})\.vault\.azure\.net(?:/[^\s<>'\"`\\]*)?",
    re.IGNORECASE,
)

AZURE_KEY_VAULT_ASSIGNMENT_PATTERN = re.compile(
    r"""(?ix)
    (?<![:/])\b(?P<name>[a-z0-9_.-]*(?:azure[a-z0-9_.-]*)?(?:key[-_.]?vault|vault)[a-z0-9_.-]*)\b
    \s*[:=]\s*
    (?P<quote>["'])?
    (?P<value>[a-z0-9-]{3,24})
    (?P=quote)?
    """,
)

GCP_PROJECT_ASSIGNMENT_PATTERN = re.compile(
    r"""(?ix)
    (?<![:/])\b(?P<name>[a-z0-9_.-]*(?:gcp|google|cloud)[a-z0-9_.-]*project[a-z0-9_.-]*)\b
    \s*[:=]\s*
    (?P<quote>["'])?
    (?P<value>[a-z][a-z0-9-]{4,28}[a-z0-9])
    (?P=quote)?
    """,
)

GCP_GCS_URI_PATTERN = re.compile(
    r"\bgs://(?P<bucket>[a-z0-9][a-z0-9._-]{1,221}[a-z0-9])(?:/[^\s<>'\"`\\]*)?",
    re.IGNORECASE,
)

GCP_GCS_HOST_PATTERN = re.compile(
    r"\bhttps?://(?:storage\.googleapis\.com/(?P<path_bucket>[a-z0-9][a-z0-9._-]{1,221}[a-z0-9])|"
    r"(?P<bucket>[a-z0-9][a-z0-9._-]{1,221}[a-z0-9])\.storage\.googleapis\.com)"
    r"(?:/[^\s<>'\"`\\]*)?",
    re.IGNORECASE,
)

GCP_SERVICE_ACCOUNT_PATTERN = re.compile(
    r"\b(?P<email>[a-z0-9._%+-]+@(?P<project_id>[a-z][a-z0-9-]{4,28}[a-z0-9])"
    r"\.iam\.gserviceaccount\.com)\b",
    re.IGNORECASE,
)

TRAILING_PUNCTUATION = ".,;:!?)\\]}"

# RIM Specification

The Repository Intelligence Model is the canonical schema for all downstream
analysis.

## RepositoryIntelligenceModel

Fields:

- `schema_version`: RIM schema version.
- `nodes`: security-aware repository nodes.
- `edges`: relationships between RIM nodes.
- `findings`: raw scanner findings used to create RIM nodes.
- `metadata`: source graph and export metadata.

## Node Types

- `repository`
- `file`
- `function`
- `class`
- `secret`
- `url`
- `database`
- `cloud_resource`
- `environment`
- `production_boundary`

## Node Fields

- `id`: stable node identifier.
- `label`: human-readable name.
- `kind`: node type.
- `source_id`: original graph node identifier when applicable.
- `source_file`: source file or source node reference.
- `confidence`: confidence from `0.0` to `1.0`.
- `metadata`: stage-specific structured details.

## Edge Types

- `contains`
- `imports`
- `calls`
- `references`
- `defines`
- `annotates`
- `belongs_to_environment`
- `crosses_boundary`

## Edge Fields

- `source`: source node ID.
- `target`: target node ID.
- `type`: relationship type.
- `confidence`: confidence from `0.0` to `1.0`.
- `metadata`: relationship-specific details.


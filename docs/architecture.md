# Architecture

## Overview

`infrastructure-automation-framework` is a Python framework, exposed through
the `iac` CLI, that orchestrates two existing IaC tools rather than
reimplementing them:

- **Terraform** provisions and tracks the desired state of cloud
  infrastructure (`terraform/`).
- **Ansible** configures the software running on that infrastructure
  (`ansible/`).
- A **drift detector** periodically compares Terraform's recorded state
  against the real infrastructure and reports divergence.

## Components

| Component | Module | Responsibility |
| --- | --- | --- |
| CLI | `iac_framework.cli` | Click-based entrypoint (`iac plan/apply/drift/ansible`). |
| Settings | `iac_framework.config` | Loads working directories, backend, and environment configuration from the environment (`IAC_*` vars). |
| Terraform runner | `iac_framework.terraform_runner` | Typed subprocess wrapper around `terraform init/plan/apply/output`; parses plan output into `PlanSummary`/`ResourceChange`. |
| Ansible runner | `iac_framework.ansible_runner` | Typed subprocess wrapper around `ansible-playbook`, with inventory handling. |
| Drift detector | `iac_framework.drift` | Runs a `-refresh-only` plan and classifies the result into a `DriftReport`. |
| Orchestrator | `iac_framework.orchestrator` | Coordinates the runners and detector across a named environment (`dev`, `staging`, `prod`). |
| Models | `iac_framework.models` | Shared, typed data structures: `PlanSummary`, `ResourceChange`, `DriftReport`, `DriftStatus`. |

## Data flow

1. A user or CI pipeline invokes `iac plan --env <environment>`.
2. The CLI loads `Settings`, builds an `Orchestrator`, and resolves the
   environment's tfvars file (`terraform/environments/<env>/<env>.tfvars`).
3. `TerraformRunner.plan()` shells out to `terraform plan`, and its textual
   output is parsed into a `PlanSummary`.
4. For `iac drift --env <environment>`, the `DriftDetector` instead runs a
   `-refresh-only` plan and classifies the result as `IN_SYNC`, `DRIFTED`, or
   `ERROR` in a `DriftReport`.
5. `iac apply` and `iac ansible` drive the same runners to provision and then
   configure the environment.

## State backend

The Terraform backend is intentionally left partially configured in
`terraform/versions.tf` (commented `backend "s3" {}` block). Concrete values
are supplied per environment via `terraform init -backend-config=...`, which
`TerraformRunner.init(backend_config=...)` supports directly.

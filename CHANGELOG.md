# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-08

### Added

- `iac` CLI with `plan`, `apply`, `drift`, and `ansible` subcommands.
- Typed Terraform runner (`terraform_runner.py`) wrapping
  `init`/`plan`/`apply`/`output`, with plan-output parsing into
  `PlanSummary` and `ResourceChange`.
- Typed Ansible runner (`ansible_runner.py`) wrapping `ansible-playbook`
  with inventory handling.
- Drift detector (`drift.py`) that classifies refresh-only plans into a
  `DriftReport` (`in_sync`, `drifted`, `error`).
- Orchestrator coordinating Terraform and Ansible across named environments.
- Example managed IaC assets: a Terraform root module with a `network`
  submodule and `dev`/`prod` environment tfvars, and an Ansible playbook
  with a `common` role.
- Documentation (README, architecture, runbook), CI pipeline, pre-commit
  hooks, and open-source project files.

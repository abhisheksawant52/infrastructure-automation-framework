# Operational Runbook

## Provisioning an environment

```bash
iac plan --env dev
iac apply --env dev
iac ansible --env dev
```

This provisions the Terraform-managed infrastructure for `dev`, then applies
the Ansible configuration baseline (`ansible/site.yml`) against the hosts in
`ansible/inventory/hosts.ini`.

## Checking for drift

Run drift detection on a schedule (e.g. a nightly CI job) against each
environment:

```bash
iac drift --env prod
```

Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | No drift detected (`DriftStatus.IN_SYNC`). |
| `1` | Drift detected (`DriftStatus.DRIFTED`) — review the summary and decide whether to re-apply or accept the change. |
| `2` | The check itself failed (`DriftStatus.ERROR`), e.g. missing credentials or an uninitialized backend. |

## Responding to drift

1. Inspect the `DriftReport.summary` and `drifted_resources` printed by
   `iac drift`.
2. If the drift is unwanted (e.g. a manual console change), run
   `iac apply --env <environment>` to reconcile it back to the Terraform
   definition.
3. If the drift is intentional, update the corresponding `.tf` files (and,
   if needed, the environment's `.tfvars`) so the desired state matches
   reality, then commit the change.

## Adding a new environment

1. Create `terraform/environments/<env>/<env>.tfvars` with the environment's
   variable values.
2. Create (or extend) an Ansible inventory for the environment, or add hosts
   to `ansible/inventory/hosts.ini` under the appropriate group.
3. Add `<env>` to `IAC_ENVIRONMENTS` (see `.env.example`) so the framework's
   `Settings.environments` allow-list accepts it.

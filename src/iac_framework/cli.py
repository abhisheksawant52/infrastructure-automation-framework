"""Command-line entrypoint for the ``iac`` tool."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .config import get_settings
from .logging_config import configure_logging, get_logger
from .models import DriftStatus
from .orchestrator import Orchestrator

logger = get_logger(__name__)


@click.group()
@click.version_option(package_name="infrastructure-automation-framework")
def cli() -> None:
    """iac: orchestrate Terraform and Ansible, and detect infrastructure drift."""
    settings = get_settings()
    configure_logging(settings.log_level)


@cli.command()
@click.option("--env", "environment", required=True, help="Target environment (e.g. dev, prod).")
def plan(environment: str) -> None:
    """Run `terraform plan` for ENVIRONMENT and print a summary."""
    settings = get_settings()
    orchestrator = Orchestrator(settings)
    summary = orchestrator.plan(environment)
    click.echo(
        f"Plan for {environment}: {summary.add} to add, "
        f"{summary.change} to change, {summary.destroy} to destroy."
    )
    if not summary.has_changes:
        click.echo("No changes.")


@cli.command()
@click.option("--env", "environment", required=True, help="Target environment (e.g. dev, prod).")
@click.option(
    "--yes/--no-yes",
    "auto_approve",
    default=True,
    help="Apply without an interactive prompt (default: enabled).",
)
def apply(environment: str, auto_approve: bool) -> None:
    """Run `terraform init` + `terraform apply` for ENVIRONMENT."""
    settings = get_settings()
    orchestrator = Orchestrator(settings)
    orchestrator.apply(environment, auto_approve=auto_approve)
    click.echo(f"Applied infrastructure changes for {environment}.")


@cli.command()
@click.option("--env", "environment", required=True, help="Target environment (e.g. dev, prod).")
def drift(environment: str) -> None:
    """Detect infrastructure drift for ENVIRONMENT and exit non-zero if found."""
    settings = get_settings()
    orchestrator = Orchestrator(settings)
    report = orchestrator.detect_drift(environment)
    click.echo(report.summary)
    if report.status == DriftStatus.ERROR:
        sys.exit(2)
    if report.status == DriftStatus.DRIFTED:
        sys.exit(1)


@cli.command()
@click.option("--env", "environment", required=True, help="Target environment (e.g. dev, prod).")
@click.option(
    "--playbook",
    "playbook",
    type=click.Path(path_type=Path),
    default=None,
    help="Playbook to run (default: ansible/site.yml).",
)
def ansible(environment: str, playbook: Path | None) -> None:
    """Run the Ansible configuration stage for ENVIRONMENT."""
    settings = get_settings()
    orchestrator = Orchestrator(settings)
    result = orchestrator.configure(environment, playbook=playbook)
    click.echo(result.stdout or "(no output)")
    if not result.succeeded:
        click.echo(result.stderr, err=True)
        sys.exit(result.returncode)


def main() -> None:
    """Console-script entrypoint registered as ``iac``."""
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()

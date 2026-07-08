"""Drift detection: comparing desired (Terraform) vs. actual infrastructure state."""

from __future__ import annotations

from pathlib import Path

from .logging_config import get_logger
from .models import DriftReport, DriftStatus
from .terraform_runner import TerraformCommandError, TerraformRunner

logger = get_logger(__name__)


class DriftDetector:
    """Detects drift between Terraform state and real infrastructure.

    Drift detection works by running a ``-refresh-only`` plan: Terraform
    reconciles its state file against the real provider APIs, and any
    resulting proposed changes represent out-of-band modifications that
    were not made through this framework (drift).

    Args:
        runner: A configured :class:`~iac_framework.terraform_runner.TerraformRunner`
            pointed at the root module to check.
    """

    def __init__(self, runner: TerraformRunner) -> None:
        self.runner = runner

    def check(self, environment: str, var_file: Path | None = None) -> DriftReport:
        """Run a refresh-only plan and classify the result.

        Args:
            environment: Logical environment name (e.g. ``dev``, ``prod``).
            var_file: Optional ``-var-file`` matching the environment.

        Returns:
            A :class:`DriftReport`. If the underlying Terraform invocation
            fails (e.g. missing credentials, no initialized backend), the
            report's status is :attr:`DriftStatus.ERROR` rather than
            raising, so batch drift checks across environments can
            continue past a single failure.
        """
        try:
            plan = self.runner.plan(environment, var_file=var_file, refresh_only=True)
        except TerraformCommandError as exc:
            logger.error("drift check failed for %s: %s", environment, exc)
            return DriftReport(
                environment=environment,
                status=DriftStatus.ERROR,
                summary=f"Drift check failed: {exc}",
            )
        return DriftReport.from_plan(plan)

"""Coordinates Terraform provisioning and Ansible configuration for an environment."""

from __future__ import annotations

from pathlib import Path

from .ansible_runner import AnsibleRunner, AnsibleRunResult
from .config import Settings
from .drift import DriftDetector
from .logging_config import get_logger
from .models import DriftReport, PlanSummary
from .terraform_runner import TerraformRunner

logger = get_logger(__name__)


class Orchestrator:
    """High-level entrypoint coordinating Terraform and Ansible.

    An ``Orchestrator`` ties the individual runners together against a
    single :class:`~iac_framework.config.Settings` instance, resolving
    per-environment tfvars and inventory files automatically.

    Args:
        settings: Application settings, typically from
            :func:`iac_framework.config.get_settings`.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.terraform = TerraformRunner(
            working_dir=settings.terraform_dir,
            binary=settings.terraform_binary,
        )
        self.ansible = AnsibleRunner(
            inventory=settings.ansible_dir / "inventory" / "hosts.ini",
            binary=settings.ansible_binary,
        )
        self.drift_detector = DriftDetector(self.terraform)

    def _validate_environment(self, environment: str) -> None:
        """Raise ``ValueError`` if ``environment`` is not configured.

        Args:
            environment: Environment name to validate against
                :attr:`Settings.environments`.
        """
        if environment not in self.settings.environments:
            raise ValueError(
                f"unknown environment {environment!r}; expected one of {self.settings.environments}"
            )

    def plan(self, environment: str) -> PlanSummary:
        """Run ``terraform plan`` for the given environment.

        Args:
            environment: Logical environment name (e.g. ``dev``, ``prod``).

        Returns:
            The parsed :class:`~iac_framework.models.PlanSummary`.
        """
        self._validate_environment(environment)
        var_file = self.settings.environment_tfvars(environment)
        return self.terraform.plan(environment, var_file=var_file)

    def apply(self, environment: str, auto_approve: bool = True) -> None:
        """Provision infrastructure for the given environment.

        Runs ``terraform init`` followed by ``terraform apply``.

        Args:
            environment: Logical environment name.
            auto_approve: Whether to apply without an interactive prompt.
        """
        self._validate_environment(environment)
        var_file = self.settings.environment_tfvars(environment)
        self.terraform.init()
        self.terraform.apply(var_file=var_file, auto_approve=auto_approve)

    def configure(self, environment: str, playbook: Path | None = None) -> AnsibleRunResult:
        """Run the Ansible configuration stage for the given environment.

        Args:
            environment: Logical environment name.
            playbook: Optional override for the playbook to run; defaults
                to ``<ansible_dir>/site.yml``.

        Returns:
            The :class:`~iac_framework.ansible_runner.AnsibleRunResult`.
        """
        self._validate_environment(environment)
        inventory = self.settings.environment_inventory(environment)
        runner = AnsibleRunner(inventory=inventory, binary=self.settings.ansible_binary)
        target_playbook = playbook or (self.settings.ansible_dir / "site.yml")
        return runner.run_playbook(target_playbook, extra_vars={"environment": environment})

    def detect_drift(self, environment: str) -> DriftReport:
        """Run drift detection for the given environment.

        Args:
            environment: Logical environment name.

        Returns:
            A :class:`~iac_framework.models.DriftReport`.
        """
        self._validate_environment(environment)
        var_file = self.settings.environment_tfvars(environment)
        return self.drift_detector.check(environment, var_file=var_file)

    def full_sync(self, environment: str) -> tuple[PlanSummary, AnsibleRunResult]:
        """Provision infrastructure, then apply configuration management.

        Args:
            environment: Logical environment name.

        Returns:
            A tuple of ``(plan_summary, ansible_result)`` describing what
            Terraform reported and how the subsequent Ansible run went.
        """
        self._validate_environment(environment)
        plan = self.plan(environment)
        self.apply(environment)
        ansible_result = self.configure(environment)
        return plan, ansible_result

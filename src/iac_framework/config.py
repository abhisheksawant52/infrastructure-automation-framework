"""Runtime configuration for the IaC automation framework.

Settings are loaded from environment variables (prefixed with ``IAC_``) and,
optionally, a ``.env`` file in the current working directory. See
``.env.example`` at the repository root for the full list of supported
variables and their defaults.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for terraform/ansible orchestration.

    Attributes:
        terraform_dir: Root directory containing the managed Terraform
            root module (relative or absolute path).
        ansible_dir: Root directory containing the managed Ansible
            playbooks, inventory, and roles.
        default_environment: Environment name used when a command is
            invoked without an explicit ``--env`` flag.
        environments: The set of environment names this framework is
            allowed to operate against (used for validation).
        backend_type: Terraform backend type (e.g. ``s3``, ``azurerm``,
            ``local``) used when generating backend configuration.
        backend_bucket: Backend storage bucket/container name, when the
            backend type requires one.
        backend_region: Backend region, when the backend type requires one.
        terraform_binary: Name or path of the Terraform executable.
        ansible_binary: Name or path of the ``ansible-playbook`` executable.
        log_level: Root logging level (e.g. ``DEBUG``, ``INFO``, ``WARNING``).
    """

    model_config = SettingsConfigDict(
        env_prefix="IAC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    terraform_dir: Path = Field(default=Path("terraform"))
    ansible_dir: Path = Field(default=Path("ansible"))

    default_environment: str = Field(default="dev")
    environments: list[str] = Field(default_factory=lambda: ["dev", "staging", "prod"])

    backend_type: str = Field(default="local")
    backend_bucket: str | None = Field(default=None)
    backend_region: str | None = Field(default=None)

    terraform_binary: str = Field(default="terraform")
    ansible_binary: str = Field(default="ansible-playbook")

    log_level: str = Field(default="INFO")

    def environment_tfvars(self, environment: str) -> Path:
        """Return the expected tfvars file path for a given environment.

        Args:
            environment: Environment name (e.g. ``dev``, ``prod``).

        Returns:
            Path to ``<terraform_dir>/environments/<environment>/<environment>.tfvars``.
        """
        return self.terraform_dir / "environments" / environment / f"{environment}.tfvars"

    def environment_inventory(self, environment: str) -> Path:
        """Return the expected Ansible inventory path for a given environment.

        Args:
            environment: Environment name (e.g. ``dev``, ``prod``).

        Returns:
            Path to the inventory file used for that environment. Falls back
            to the default ``inventory/hosts.ini`` shipped with this repo.
        """
        per_env = self.ansible_dir / "inventory" / f"{environment}.ini"
        if per_env.exists():
            return per_env
        return self.ansible_dir / "inventory" / "hosts.ini"


def get_settings() -> Settings:
    """Return a freshly loaded :class:`Settings` instance.

    A factory function (rather than a module-level singleton) keeps
    configuration loading explicit and easy to override in tests.
    """
    return Settings()

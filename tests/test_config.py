"""Unit tests for iac_framework.config.Settings."""

from __future__ import annotations

from pathlib import Path

from iac_framework.config import Settings


def test_default_settings(monkeypatch) -> None:
    monkeypatch.delenv("IAC_DEFAULT_ENVIRONMENT", raising=False)
    settings = Settings(_env_file=None)

    assert settings.default_environment == "dev"
    assert "prod" in settings.environments
    assert settings.terraform_binary == "terraform"


def test_environment_tfvars_path() -> None:
    settings = Settings(_env_file=None, terraform_dir=Path("terraform"))

    tfvars = settings.environment_tfvars("prod")

    assert tfvars == Path("terraform/environments/prod/prod.tfvars")

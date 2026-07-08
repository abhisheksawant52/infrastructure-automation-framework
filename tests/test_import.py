"""Smoke tests: the package and its submodules import cleanly."""

from __future__ import annotations

import importlib


def test_package_version() -> None:
    import iac_framework

    assert iac_framework.__version__ == "0.1.0"


def test_submodules_import() -> None:
    modules = [
        "iac_framework.config",
        "iac_framework.logging_config",
        "iac_framework.models",
        "iac_framework.terraform_runner",
        "iac_framework.ansible_runner",
        "iac_framework.drift",
        "iac_framework.orchestrator",
        "iac_framework.cli",
    ]
    for name in modules:
        importlib.import_module(name)

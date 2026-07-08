"""iac_framework: a Python orchestration framework for Terraform and Ansible.

This package provides typed wrappers around the Terraform and Ansible CLIs,
a drift detector that compares desired vs. actual infrastructure state, and
an orchestrator that coordinates provisioning (Terraform) and configuration
(Ansible) across named environments.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]

"""A typed wrapper around ``ansible-playbook`` for configuration management.

``AnsibleRunner`` shells out to ``ansible-playbook`` via :mod:`subprocess`.
As with :mod:`iac_framework.terraform_runner`, the subprocess calls are
structured and documented but not exercised against a real inventory in
this package's own test suite.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .logging_config import get_logger

logger = get_logger(__name__)


class AnsibleCommandError(RuntimeError):
    """Raised when an ``ansible-playbook`` invocation exits non-zero."""

    def __init__(self, command: list[str], returncode: int, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"command {' '.join(command)!r} failed with exit code {returncode}: {stderr.strip()}"
        )


@dataclass
class AnsibleRunResult:
    """The outcome of a single ``ansible-playbook`` invocation.

    Attributes:
        playbook: Path to the playbook that was run.
        inventory: Path to the inventory file used.
        returncode: Process exit code.
        stdout: Captured standard output.
        stderr: Captured standard error.
        tags: Tags the run was limited to, if any.
    """

    playbook: Path
    inventory: Path
    returncode: int
    stdout: str
    stderr: str
    tags: list[str] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        """Whether the playbook run completed without error."""
        return self.returncode == 0


class AnsibleRunner:
    """Wraps ``ansible-playbook`` execution against a fixed inventory.

    Args:
        inventory: Path to an inventory file or directory (e.g.
            ``ansible/inventory/hosts.ini``).
        binary: Name or path of the ``ansible-playbook`` executable.
        env: Optional environment variable overrides for the subprocess.
    """

    def __init__(
        self,
        inventory: Path,
        binary: str = "ansible-playbook",
        env: dict[str, str] | None = None,
    ) -> None:
        self.inventory = Path(inventory)
        self.binary = binary
        self.env = env

    def run_playbook(
        self,
        playbook: Path,
        extra_vars: dict[str, str] | None = None,
        tags: list[str] | None = None,
        limit: str | None = None,
        check: bool = False,
    ) -> AnsibleRunResult:
        """Run a playbook against :attr:`inventory`.

        Args:
            playbook: Path to the playbook YAML file (e.g. ``site.yml``).
            extra_vars: Optional ``--extra-vars key=value`` pairs.
            tags: Optional ``--tags`` to restrict which tasks run.
            limit: Optional ``--limit`` host pattern.
            check: Whether to pass ``--check`` for a dry run.

        Returns:
            An :class:`AnsibleRunResult` describing the outcome. Non-zero
            exit codes are captured in the result rather than raised, so
            callers (e.g. the orchestrator) can decide how to react.
        """
        command = [self.binary, "-i", str(self.inventory), str(playbook)]
        if tags:
            command += ["--tags", ",".join(tags)]
        if limit:
            command += ["--limit", limit]
        if check:
            command.append("--check")
        for key, value in (extra_vars or {}).items():
            command += ["--extra-vars", f"{key}={value}"]

        logger.debug("running: %s", " ".join(command))
        result = subprocess.run(
            command,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        return AnsibleRunResult(
            playbook=Path(playbook),
            inventory=self.inventory,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            tags=tags or [],
        )

    def ping(self, pattern: str = "all") -> AnsibleRunResult:
        """Run the ``ansible`` ad-hoc ``ping`` module against hosts.

        Useful as a lightweight connectivity check before a full playbook
        run.

        Args:
            pattern: Host pattern to target (default: all hosts).

        Returns:
            An :class:`AnsibleRunResult`-shaped result (playbook path is
            set to a sentinel since this is not a playbook run).
        """
        command = ["ansible", pattern, "-i", str(self.inventory), "-m", "ping"]
        logger.debug("running: %s", " ".join(command))
        result = subprocess.run(
            command,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        return AnsibleRunResult(
            playbook=Path("<ad-hoc:ping>"),
            inventory=self.inventory,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

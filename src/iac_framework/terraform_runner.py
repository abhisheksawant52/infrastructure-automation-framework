"""A typed wrapper around the Terraform CLI.

``TerraformRunner`` shells out to the ``terraform`` binary via
:mod:`subprocess` and parses its output into the structures defined in
:mod:`iac_framework.models`. Each public method documents the exact CLI
invocation it performs; none of the methods are invoked as part of this
package's own test suite (they require a real Terraform installation and
provider credentials), but they are structured so the parsing logic can be
unit tested independently of the subprocess call.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .logging_config import get_logger
from .models import ChangeAction, PlanSummary, ResourceChange

logger = get_logger(__name__)

_PLAN_SUMMARY_RE = re.compile(
    r"Plan:\s+(?P<add>\d+)\s+to add,\s+(?P<change>\d+)\s+to change,\s+(?P<destroy>\d+)\s+to destroy"
)
_NO_CHANGES_RE = re.compile(r"No changes\.")


class TerraformCommandError(RuntimeError):
    """Raised when a terraform subprocess invocation exits non-zero."""

    def __init__(self, command: list[str], returncode: int, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"command {' '.join(command)!r} failed with exit code {returncode}: {stderr.strip()}"
        )


class TerraformRunner:
    """Wraps ``terraform init/plan/apply/output`` for a single root module.

    Args:
        working_dir: Directory containing the Terraform root module
            (i.e. the directory with ``main.tf``, ``versions.tf``, etc.).
        binary: Name or path of the Terraform executable.
        env: Optional environment variable overrides passed to every
            subprocess invocation (e.g. cloud credentials).
    """

    def __init__(
        self,
        working_dir: Path,
        binary: str = "terraform",
        env: dict[str, str] | None = None,
    ) -> None:
        self.working_dir = Path(working_dir)
        self.binary = binary
        self.env = env

    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        """Run a terraform subcommand in :attr:`working_dir`.

        Args:
            args: Arguments following the ``terraform`` binary name, e.g.
                ``["plan", "-input=false"]``.
            check: Whether to raise :class:`TerraformCommandError` on a
                non-zero exit code.

        Returns:
            The completed process, with captured stdout/stderr text.
        """
        command = [self.binary, *args]
        logger.debug("running: %s (cwd=%s)", " ".join(command), self.working_dir)
        result = subprocess.run(
            command,
            cwd=self.working_dir,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise TerraformCommandError(command, result.returncode, result.stderr)
        return result

    def init(self, backend_config: dict[str, str] | None = None, upgrade: bool = False) -> None:
        """Run ``terraform init``.

        Args:
            backend_config: Optional ``-backend-config=key=value`` pairs,
                typically used to select a per-environment remote state
                backend without hardcoding it in ``versions.tf``.
            upgrade: Whether to pass ``-upgrade`` to update provider plugins.
        """
        args = ["init", "-input=false"]
        if upgrade:
            args.append("-upgrade")
        for key, value in (backend_config or {}).items():
            args.append(f"-backend-config={key}={value}")
        self._run(args)

    def plan(
        self,
        environment: str,
        var_file: Path | None = None,
        refresh_only: bool = False,
    ) -> PlanSummary:
        """Run ``terraform plan`` and parse its human-readable summary.

        Args:
            environment: Logical environment name, stored on the returned
                :class:`PlanSummary` for downstream reporting.
            var_file: Optional ``-var-file`` to pass (e.g. an
                ``environments/<env>/<env>.tfvars`` file).
            refresh_only: When ``True``, runs a ``-refresh-only`` plan,
                which is what :mod:`iac_framework.drift` uses to detect
                out-of-band changes without proposing to apply anything.

        Returns:
            A :class:`PlanSummary` parsed from the CLI's textual output.

        Note:
            This uses the human-readable plan output rather than
            ``-json`` for simplicity; :meth:`_parse_plan_output` is kept
            separate so it can be swapped for JSON parsing later without
            touching callers.
        """
        args = ["plan", "-input=false", "-no-color"]
        if refresh_only:
            args.append("-refresh-only")
        if var_file is not None:
            args.append(f"-var-file={var_file}")
        result = self._run(args, check=False)
        return self._parse_plan_output(environment, result.stdout)

    def apply(self, var_file: Path | None = None, auto_approve: bool = True) -> None:
        """Run ``terraform apply``.

        Args:
            var_file: Optional ``-var-file`` to pass.
            auto_approve: Whether to pass ``-auto-approve``. Defaults to
                ``True`` because this framework is intended to run
                non-interactively in automation.
        """
        args = ["apply", "-input=false"]
        if auto_approve:
            args.append("-auto-approve")
        if var_file is not None:
            args.append(f"-var-file={var_file}")
        self._run(args)

    def destroy(self, var_file: Path | None = None, auto_approve: bool = False) -> None:
        """Run ``terraform destroy``.

        Args:
            var_file: Optional ``-var-file`` to pass.
            auto_approve: Whether to pass ``-auto-approve``. Defaults to
                ``False`` as a safety measure for a destructive operation.
        """
        args = ["destroy", "-input=false"]
        if auto_approve:
            args.append("-auto-approve")
        if var_file is not None:
            args.append(f"-var-file={var_file}")
        self._run(args)

    def output(self) -> dict[str, object]:
        """Run ``terraform output -json`` and return the parsed values.

        Returns:
            A mapping of output name to its raw value (unwrapped from the
            ``{"value": ..., "type": ...}`` envelope Terraform emits).
        """
        result = self._run(["output", "-json"])
        raw = json.loads(result.stdout or "{}")
        return {name: entry.get("value") for name, entry in raw.items()}

    @staticmethod
    def _parse_plan_output(environment: str, stdout: str) -> PlanSummary:
        """Parse ``terraform plan`` textual output into a :class:`PlanSummary`.

        Args:
            environment: Environment name to attach to the summary.
            stdout: Captured standard output from the plan command.

        Returns:
            A populated :class:`PlanSummary`. When Terraform reports
            "No changes.", all counters are zero.
        """
        if _NO_CHANGES_RE.search(stdout):
            return PlanSummary(environment=environment, add=0, change=0, destroy=0, raw_output=stdout)

        match = _PLAN_SUMMARY_RE.search(stdout)
        if not match:
            return PlanSummary(environment=environment, raw_output=stdout)

        resource_changes = [
            ResourceChange(address=address, action=action)
            for address, action in _extract_resource_actions(stdout)
        ]
        return PlanSummary(
            environment=environment,
            add=int(match.group("add")),
            change=int(match.group("change")),
            destroy=int(match.group("destroy")),
            resource_changes=resource_changes,
            raw_output=stdout,
        )


_RESOURCE_LINE_RE = re.compile(r"^\s*# (?P<address>\S+) (?:will be|must be) (?P<verb>[a-z\- ]+)$")

_VERB_TO_ACTION = {
    "created": ChangeAction.CREATE,
    "destroyed": ChangeAction.DELETE,
    "updated in-place": ChangeAction.UPDATE,
    "replaced": ChangeAction.REPLACE,
}


def _extract_resource_actions(stdout: str) -> list[tuple[str, ChangeAction]]:
    """Best-effort extraction of per-resource actions from plan text.

    Terraform's human-readable plan output includes lines such as
    ``  # aws_instance.web will be created`` above each resource's diff.
    This scans for those lines; anything it cannot classify is skipped
    rather than raising, since the textual format is not a stable contract.

    Args:
        stdout: Captured standard output from ``terraform plan``.

    Returns:
        A list of ``(resource_address, action)`` tuples.
    """
    changes: list[tuple[str, ChangeAction]] = []
    for line in stdout.splitlines():
        match = _RESOURCE_LINE_RE.match(line)
        if not match:
            continue
        action = _VERB_TO_ACTION.get(match.group("verb").strip())
        if action is not None:
            changes.append((match.group("address"), action))
    return changes

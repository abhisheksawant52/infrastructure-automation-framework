"""Typed data models shared across the terraform/ansible/drift subsystems."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ChangeAction(str, Enum):
    """The action Terraform intends to take on a resource."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REPLACE = "replace"
    NO_OP = "no-op"


class DriftStatus(str, Enum):
    """Overall drift classification for an environment."""

    IN_SYNC = "in_sync"
    DRIFTED = "drifted"
    UNKNOWN = "unknown"
    ERROR = "error"


class ResourceChange(BaseModel):
    """A single resource-level change reported by a Terraform plan.

    Attributes:
        address: Fully qualified resource address, e.g.
            ``module.network.aws_subnet.public[0]``.
        action: The change action Terraform would take.
        attribute_diffs: Mapping of changed attribute name to a human
            readable ``"before -> after"`` description.
    """

    address: str
    action: ChangeAction
    attribute_diffs: dict[str, str] = Field(default_factory=dict)


class PlanSummary(BaseModel):
    """A parsed summary of a ``terraform plan`` run.

    Attributes:
        environment: The environment the plan was run against.
        add: Number of resources to be created.
        change: Number of resources to be updated in place.
        destroy: Number of resources to be destroyed.
        resource_changes: Detailed per-resource changes, when available.
        raw_output: The unparsed terraform CLI output, kept for debugging.
    """

    environment: str
    add: int = 0
    change: int = 0
    destroy: int = 0
    resource_changes: list[ResourceChange] = Field(default_factory=list)
    raw_output: str = ""

    @property
    def has_changes(self) -> bool:
        """Whether this plan would modify any infrastructure."""
        return bool(self.add or self.change or self.destroy)


class DriftReport(BaseModel):
    """The outcome of a drift detection run for a single environment.

    Attributes:
        environment: The environment that was checked.
        status: Overall drift classification.
        drifted_resources: Resources found to have diverged from the
            desired (Terraform-defined) state.
        checked_at: UTC timestamp when the check completed.
        summary: A short, human-readable summary of the finding.
    """

    environment: str
    status: DriftStatus
    drifted_resources: list[ResourceChange] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str = ""

    @classmethod
    def from_plan(cls, plan: PlanSummary) -> DriftReport:
        """Classify a :class:`PlanSummary` into a :class:`DriftReport`.

        A non-empty plan (i.e. anything Terraform would change) that was
        produced from a refresh-only run indicates the real-world state has
        diverged from the last-applied state.

        Args:
            plan: The parsed output of a refresh/plan run.

        Returns:
            A populated ``DriftReport``.
        """
        drifted = [c for c in plan.resource_changes if c.action != ChangeAction.NO_OP]
        if not plan.has_changes:
            status = DriftStatus.IN_SYNC
            summary = f"No drift detected in '{plan.environment}'."
        else:
            status = DriftStatus.DRIFTED
            summary = (
                f"Drift detected in '{plan.environment}': "
                f"{plan.add} to add, {plan.change} to change, {plan.destroy} to destroy."
            )
        return cls(
            environment=plan.environment,
            status=status,
            drifted_resources=drifted,
            summary=summary,
        )

"""Unit tests for drift classification in iac_framework.models."""

from __future__ import annotations

from iac_framework.models import (
    ChangeAction,
    DriftReport,
    DriftStatus,
    PlanSummary,
    ResourceChange,
)


def test_plan_with_no_changes_is_in_sync() -> None:
    plan = PlanSummary(environment="dev", add=0, change=0, destroy=0)

    report = DriftReport.from_plan(plan)

    assert report.status == DriftStatus.IN_SYNC
    assert report.drifted_resources == []
    assert report.environment == "dev"


def test_plan_with_changes_is_classified_as_drifted() -> None:
    change = ResourceChange(address="aws_instance.web[0]", action=ChangeAction.UPDATE)
    plan = PlanSummary(environment="prod", add=0, change=1, destroy=0, resource_changes=[change])

    report = DriftReport.from_plan(plan)

    assert report.status == DriftStatus.DRIFTED
    assert report.drifted_resources == [change]
    assert "prod" in report.summary


def test_plan_summary_has_changes_property() -> None:
    assert not PlanSummary(environment="dev").has_changes
    assert PlanSummary(environment="dev", add=1).has_changes

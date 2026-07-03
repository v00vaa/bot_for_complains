
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func, select

from database.models import BugData, BugReport, BugStatus


SEVERITY_NOT_SET = "not_set"
SEVERITY_VALUES = ("critical", "high", "medium", "low", SEVERITY_NOT_SET)


@dataclass(slots=True)
class BugView:
    id: int
    user_id: int
    title: str
    created_at: datetime
    bug_data_id: int
    version: int
    description: str
    report_file_id: str
    report_file_name: str
    severity: str
    status: str
    assigned_admin_id: int | None
    assigned_admin_username: str | None
    is_training_sample: bool


def _severity_order_expr():
    return case(
        (BugStatus.severity == SEVERITY_NOT_SET, 0),
        (BugStatus.severity == "critical", 1),
        (BugStatus.severity == "high", 2),
        (BugStatus.severity == "medium", 3),
        (BugStatus.severity == "low", 4),
        else_=5,
    )


def _bug_view_from_row(
    bug: BugReport,
    data: BugData,
    status: BugStatus,
) -> BugView:
    return BugView(
        id=bug.id,
        user_id=bug.user_id,
        title=bug.title,
        created_at=bug.created_at,
        bug_data_id=data.id,
        version=data.version,
        description=data.description,
        report_file_id=data.report_file_id,
        report_file_name=data.report_file_name,
        severity=status.severity,
        status=status.status,
        assigned_admin_id=status.assigned_admin_id,
        assigned_admin_username=status.assigned_admin_username,
        is_training_sample=data.is_training_sample
    )


def _latest_data_subquery():
    return (
        select(
            BugData.bug_id,
            func.max(BugData.version).label("version"),
        )
        .group_by(BugData.bug_id)
        .subquery()
    )


def _latest_status_subquery():
    return (
        select(
            BugStatus.bug_id,
            func.max(BugStatus.created_at).label("created_at"),
        )
        .group_by(BugStatus.bug_id)
        .subquery()
    )


def _current_bug_stmt():
    latest_data = _latest_data_subquery()
    latest_status = _latest_status_subquery()

    return (
        select(BugReport, BugData, BugStatus)
        .join(
            latest_data,
            latest_data.c.bug_id == BugReport.id,
        )
        .join(
            BugData,
            (BugData.bug_id == BugReport.id)
            & (BugData.version == latest_data.c.version),
        )
        .join(
            latest_status,
            latest_status.c.bug_id == BugReport.id,
        )
        .join(
            BugStatus,
            (BugStatus.bug_id == BugReport.id)
            & (BugStatus.created_at == latest_status.c.created_at),
        )
    )

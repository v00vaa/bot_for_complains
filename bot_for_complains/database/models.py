from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BugReport(Base):
    __tablename__ = "bug_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    versions: Mapped[list["BugData"]] = relationship(
        back_populates="bug",
        cascade="all, delete-orphan",
        order_by="desc(BugData.version)",
    )

    statuses: Mapped[list["BugStatus"]] = relationship(
        back_populates="bug",
        cascade="all, delete-orphan",
        order_by="desc(BugStatus.created_at)",
    )


class BugData(Base):
    __tablename__ = "bug_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    bug_id: Mapped[int] = mapped_column(
        ForeignKey("bug_reports.id", ondelete="CASCADE"),
    )
    version: Mapped[int] = mapped_column()
    description: Mapped[str] = mapped_column(Text)
    report_file_id: Mapped[str] = mapped_column(String(255))
    report_file_name: Mapped[str] = mapped_column(String(255))
    is_training_sample: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    bug: Mapped["BugReport"] = relationship(back_populates="versions")
    statuses: Mapped[list["BugStatus"]] = relationship(
        back_populates="bug_data",
        cascade="all, delete-orphan",
        order_by="desc(BugStatus.created_at)",
    )


class BugStatus(Base):
    __tablename__ = "bug_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    bug_id: Mapped[int] = mapped_column(
        ForeignKey("bug_reports.id", ondelete="CASCADE"),
    )
    bug_data_id: Mapped[int] = mapped_column(
        ForeignKey("bug_data.id", ondelete="CASCADE"),
    )
    severity: Mapped[str] = mapped_column(String(20), default="not_set")
    status: Mapped[str] = mapped_column(String(50))
    assigned_admin_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    assigned_admin_username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    bug: Mapped["BugReport"] = relationship(back_populates="statuses")
    bug_data: Mapped["BugData"] = relationship(back_populates="statuses")

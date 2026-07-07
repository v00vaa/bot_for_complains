"""
ORM-модели базы данных.

Модуль описывает структуру базы данных системы технической поддержки.

Модель данных разделена на три основные сущности:

    • BugReport — обращение пользователя.
    • BugData — конкретная версия обращения.
    • BugStatus — история изменения статусов обращения.

Такое разделение позволяет хранить:
    • полную историю изменений описаний;
    • историю изменения статусов;
    • историю изменения критичности;
    • информацию о назначенных администраторах.

Все модели используют SQLAlchemy ORM и автоматически
преобразуются в таблицы базы данных при запуске приложения.
"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BugReport(Base):
    """
    Основная запись обращения пользователя.

    Содержит информацию, которая не изменяется
    на протяжении жизненного цикла обращения:

        • автора обращения;
        • краткое название;
        • дату создания.

    История изменений описаний хранится в BugData,
    а история состояний — в BugStatus.
    """
    __tablename__ = "bug_reports"
    # Уникальный идентификатор обращения.
    id: Mapped[int] = mapped_column(primary_key=True)
    # Telegram ID пользователя.
    user_id: Mapped[int] = mapped_column(BigInteger)
    # Краткое автоматически сгенерированное название обращения.
    title: Mapped[str] = mapped_column(String(255))
    # Время регистрации обращения.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    # Все версии обращения.
    versions: Mapped[list["BugData"]] = relationship(
        back_populates="bug",
        cascade="all, delete-orphan",
        order_by="desc(BugData.version)",
    )
    # История изменения статусов.
    statuses: Mapped[list["BugStatus"]] = relationship(
        back_populates="bug",
        cascade="all, delete-orphan",
        order_by="desc(BugStatus.created_at)",
    )


class BugData(Base):
    """
    Версия обращения.

    Каждое изменение описания пользователем создает
    новую запись BugData.

    Благодаря этому сохраняется полная история изменений,
    а предыдущие версии никогда не редактируются.
    """
    __tablename__ = "bug_data"
    # Идентификатор версии.
    id: Mapped[int] = mapped_column(primary_key=True)
    # Обращение, которому принадлежит версия.
    bug_id: Mapped[int] = mapped_column(
        ForeignKey("bug_reports.id", ondelete="CASCADE"),
    )
    # Порядковый номер версии.
    version: Mapped[int] = mapped_column()
    # Текст описания проблемы.
    description: Mapped[str] = mapped_column(Text)
    # Telegram File ID прикрепленного файла.
    report_file_id: Mapped[str] = mapped_column(String(255))
    # Имя прикрепленного файла.
    report_file_name: Mapped[str] = mapped_column(String(255))
    # Используется ли описание для обучения модели.
    is_training_sample: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false"),
    )
    # Время создания версии.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    # Родительское обращение.
    bug: Mapped["BugReport"] = relationship(back_populates="versions")
    # Все статусы, относящиеся к данной версии.
    statuses: Mapped[list["BugStatus"]] = relationship(
        back_populates="bug_data",
        cascade="all, delete-orphan",
        order_by="desc(BugStatus.created_at)",
    )


class BugStatus(Base):
    """
    История изменения состояния обращения.

    Вместо обновления существующей записи создается
    новая строка при каждом изменении:

        • статуса;
        • критичности;
        • назначенного администратора.

    Такой подход позволяет полностью восстановить
    жизненный цикл обращения.
    """
    __tablename__ = "bug_status"
    # Идентификатор записи истории.
    id: Mapped[int] = mapped_column(primary_key=True)
    # Обращение.
    bug_id: Mapped[int] = mapped_column(
        ForeignKey("bug_reports.id", ondelete="CASCADE"),
    )
    # Версия обращения, к которой относится статус.
    bug_data_id: Mapped[int] = mapped_column(
        ForeignKey("bug_data.id", ondelete="CASCADE"),
    )
    # Критичность обращения.
    severity: Mapped[str] = mapped_column(String(20), default="not_set")
    # Текущее состояние обращения.
    status: Mapped[str] = mapped_column(String(50))
    # Ответственный администратор.
    assigned_admin_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    # Username администратора.
    assigned_admin_username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    # Время изменения статуса.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    # Родительское обращение.
    bug: Mapped["BugReport"] = relationship(back_populates="statuses")

    bug_data: Mapped["BugData"] = relationship(back_populates="statuses")

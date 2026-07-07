"""
Модуль формирования представления багов (BugView).

 Назначение
 ----------
 Данный модуль содержит общие структуры и SQL-запросы, используемые для
 получения актуального состояния обращений (багов) из базы данных.
 
 В базе данных информация о баге разделена на несколько сущностей:

 - BugReport — неизменяемые данные обращения
   (автор, дата создания, название и т.д.);
 - BugData — версии описания и приложенных файлов.
   При каждом повторном открытии обращения создаётся новая запись;
 - BugStatus — история изменения статусов
   (новый, в работе, исправлен и т.д.).

 Поскольку данные распределены по нескольким таблицам и хранят историю
 изменений, большинству обработчиков неудобно работать с ними напрямую.

 Для этого используется объект BugView, который объединяет информацию
 из всех таблиц в единый объект, содержащий только актуальную версию
 описания и последний статус бага.

 Кроме этого модуль предоставляет вспомогательные SQL-конструкторы,
 используемые другими функциями доступа к данным:
 
 - получение последней версии BugData;
 - получение последнего статуса BugStatus;
 - построение общего SQL-запроса текущего состояния бага;
 - выражение для сортировки по критичности.

 Благодаря этому вся логика получения "текущего состояния" обращения
 сосредоточена в одном месте и не дублируется в остальных запросах.
 """

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func, select

from database.models import BugData, BugReport, BugStatus

# -----------------------------------------------------------------------------
# Возможные уровни критичности бага.
#
# Значение "not_set" используется по умолчанию сразу после создания обращения,
# пока администратор не выполнил оценку критичности.
# -----------------------------------------------------------------------------
SEVERITY_NOT_SET = "not_set"
SEVERITY_VALUES = ("critical", "high", "medium", "low", SEVERITY_NOT_SET)

# -----------------------------------------------------------------------------
# Представление обращения, используемое в обработчиках Telegram-бота.
#
# Данный класс объединяет данные сразу из трех таблиц:
#
#     BugReport  — неизменяемые сведения об обращении;
#     BugData    — текущая версия описания и приложенного файла;
#     BugStatus  — текущее состояние обращения.
#
# Благодаря этому остальные части программы работают только с одним объектом,
# не зная о внутренней структуре базы данных.
# -----------------------------------------------------------------------------
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
    # Используется системой обучения модели проверки описаний.
    # Показывает, включена ли данная версия обращения
    # в обучающий корпус.
    is_training_sample: bool

# -----------------------------------------------------------------------------
# Формирует SQL-выражение для сортировки по критичности.
#
# Поскольку критичность хранится в виде строк,
# обычная сортировка выполнялась бы в алфавитном порядке.
#
# CASE позволяет задать собственный приоритет:
#
#     not_set
#     critical
#     high
#     medium
#     low
#
# Используется при построении запросов списка обращений.
# -----------------------------------------------------------------------------
def _severity_order_expr():
    return case(
        (BugStatus.severity == SEVERITY_NOT_SET, 0),
        (BugStatus.severity == "critical", 1),
        (BugStatus.severity == "high", 2),
        (BugStatus.severity == "medium", 3),
        (BugStatus.severity == "low", 4),
        else_=5,
    )

# -----------------------------------------------------------------------------
# Преобразует результат SQL-запроса в объект BugView.
#
# На вход поступают три ORM-объекта из разных таблиц,
# после чего создается единое представление обращения,
# используемое во всех обработчиках.
#
# Благодаря этому остальной код не зависит от структуры БД.
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# Подзапрос, определяющий последнюю версию данных каждого обращения.
#
# Каждое повторное открытие обращения создает новую запись BugData,
# поэтому для отображения актуального состояния необходимо выбрать запись
# с максимальным номером версии.
#
# Возвращает таблицу вида:
#
#     bug_id | version
#
# -----------------------------------------------------------------------------
def _latest_data_subquery():
    return (
        select(
            BugData.bug_id,
            func.max(BugData.version).label("version"),
        )
        .group_by(BugData.bug_id)
        .subquery()
    )

# -----------------------------------------------------------------------------
# Подзапрос, определяющий последнее изменение статуса обращения.
#
# История изменения статусов хранится отдельно,
# поэтому актуальным считается статус с максимальным временем создания.
#
# Возвращает таблицу:
#
#     bug_id | created_at
#
# -----------------------------------------------------------------------------
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
    """
    Формирует базовый запрос получения актуального состояния обращений.
    
    Последовательность работы:
    
        1. выбирается последняя версия BugData;
        2. выбирается последний BugStatus;
        3. выполняется объединение с BugReport;
        4. возвращаются только актуальные записи.
    
    Практически все запросы списка обращений строятся на основе
    данного выражения, что позволяет избежать дублирования SQL-кода.
    """
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

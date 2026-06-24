from datetime import datetime
import re


def generate_bug_title(description: str) -> str: # Генерация названия бага
    text = re.sub(r"\s+", " ", description).strip()

    if len(text) > 40:
        text = text[:40].rstrip()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    return f"{text} [{timestamp}]"


def determine_severity(description: str) -> str:  # Определение кретичности

    text = description.lower()

    critical_words = (
        "не проверяет документ",
        "не загружается файл",
        "ошибка проверки",
        "потеря замечаний",
        "результаты пропали",
    )

    high_words = (
        "не находит орфографические ошибки",
        "ложные срабатывания",
        "неверная проверка гост",
        "неправильно определяет ошибки",
        "не работает отчет",
    )

    medium_words = (
        "медленная проверка",
        "ошибка интерфейса",
        "неудобно пользоваться",
        "непонятное сообщение",
        "неверное отображение документа",
    )

    if any(word in text for word in critical_words):
        return "critical"

    if any(word in text for word in high_words):
        return "high"

    if any(word in text for word in medium_words):
        return "medium"

    return "low"

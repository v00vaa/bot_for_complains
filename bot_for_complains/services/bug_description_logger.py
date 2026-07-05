import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

bug_description_logger = logging.getLogger("bug_descriptions")
bug_description_logger.setLevel(logging.INFO)
bug_description_logger.propagate = False

if not bug_description_logger.handlers:
    handler = logging.FileHandler(
        LOG_DIR / "rejected_descriptions.log",
        encoding="utf-8",
    )

    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] "
        "user=%(user_id)s "
        "username=%(username)s\n"
        "%(message)s\n"
        "------------------------------------------------------------"
    )

    handler.setFormatter(formatter)
    bug_description_logger.addHandler(handler)

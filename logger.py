"""

Централизованное логирование:
- файл
- консоль
- единый формат
"""

import logging
import config
from pathlib import Path


def setup_logger():

    Path(config.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("report_checker")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
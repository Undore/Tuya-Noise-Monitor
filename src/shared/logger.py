import logging
import os
import re
from logging.handlers import RotatingFileHandler

import click
from rich.console import Console
from rich.logging import RichHandler

from settings import LOG_LEVEL, LOGS_FILES_PATH

MAX_ROTATION_SIZE = 10 * 1024 * 1024



def normalize_logging_prefix(s: str) -> str:
    s = re.sub(r"\[.*?\]", "", s)
    s = s.replace("{", "").replace("}", "")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")

TAG_RE = re.compile(
    r"""
    \[
        (?:
            /?\w+                    # [green] [/green]
            |
            /?(?:bold|dim)\s+\w+     # [bold green] [/bold green]
        )
    \]
    """,
    re.VERBOSE,
)

def normalize_logging_record(s: str) -> str:
    while TAG_RE.search(s):
        s = TAG_RE.sub("", s)

    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s



class CleanFileFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        date_part, time_part, msg_part = msg.split(' ', maxsplit=2)
        level = msg_part.split(' ')[0]
        return f"{date_part} {time_part} {level}" + " " + normalize_logging_record(msg_part)


def reg_logger(prefix: str | None = None, level: str = LOG_LEVEL) -> logging.Logger:
    os.makedirs(LOGS_FILES_PATH, exist_ok=True)

    if prefix:
        log_name = normalize_logging_prefix(prefix) or "app"
    else:
        log_name = ""

    console = Console(width=int(os.environ.get("CONSOLE_WIDTH", 200)))
    console_handler = RichHandler(
        rich_tracebacks=True,
        console=console,
        tracebacks_suppress=[click],
        omit_repeated_times=False,
        markup=True,
        tracebacks_show_locals=True,
        #show_path=AppSettings().is_dev_mode(),  # type: ignore
        show_path=True,  # type: ignore
        enable_link_path=False
    )

    class ConsoleFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            if prefix:
                formatted = "{prefix}: {message}".format(
                    levelname=level, message=record.getMessage(), prefix=prefix
                )
            else:
                formatted = "{message}".format(
                    levelname=level, message=record.getMessage()
                )
            return formatted

    console_handler.setFormatter(ConsoleFormatter())

    file_handler = RotatingFileHandler(
        os.path.join(LOGS_FILES_PATH, f"{log_name}.log" if log_name else "global.log"),
        maxBytes=MAX_ROTATION_SIZE,
        backupCount=5,
    )

    file_handler.setFormatter(CleanFileFormatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    ))

    global_file_handler = RotatingFileHandler(
        os.path.join(LOGS_FILES_PATH, "!global.log"),
        maxBytes=MAX_ROTATION_SIZE,
        backupCount=5,
    )

    global_file_handler.setFormatter(CleanFileFormatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    ))

    logger = logging.getLogger(prefix)
    logger.setLevel(level)

    logger.handlers.clear()

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(global_file_handler)

    logger.propagate = False

    return logger
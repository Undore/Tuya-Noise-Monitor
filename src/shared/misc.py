from datetime import datetime

from settings import SYSTEM_TIMEZONE


def get_now() -> datetime:
    return datetime.now(SYSTEM_TIMEZONE)


def date_iso(date: datetime | None, expect_forever: bool = False):
    if not date:
        return "[Forever]" if expect_forever else "[Undefined]"

    return date.isoformat(sep=" ", timespec="seconds")

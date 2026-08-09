import os
from pathlib import Path

import pytz

SYSTEM_TIMEZONE = pytz.timezone("Europe/Moscow")
BASE_PATH = Path(__file__).parent

LOG_LEVEL = "DEBUG"
LOGS_FILES_PATH = BASE_PATH.parent / 'logs'
os.makedirs(LOGS_FILES_PATH, exist_ok=True)


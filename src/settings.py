import os
from datetime import timezone
from pathlib import Path

SYSTEM_TIMEZONE = timezone.utc
BASE_PATH = Path(__file__).parent

LOG_LEVEL = "DEBUG"
LOGS_FILES_PATH = BASE_PATH / 'logs'
os.makedirs(LOGS_FILES_PATH, exist_ok=True)


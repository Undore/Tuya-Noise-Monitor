# Copyright 2026 Undore
# SPDX-License-Identifier: Apache-2.0

import asyncio

from configs.app_settings import get_settings, AppSettings
from processes.noise_monitor.noise_monitor_service import NoiseMonitorService
from processes.telegram.bot import TelegramService
from shared.logger import reg_logger
from shared.wait_for_shutdown import wait_for_shutdown

logger = reg_logger()
settings: AppSettings = get_settings()


async def main():
    logger.info("[bold cyan]Starting up")

    telegram = TelegramService.get_instance()
    await telegram.start_polling()

    noise_monitor = NoiseMonitorService.get_instance()
    await noise_monitor.start_monitoring()

    logger.info("[bold green]Application startup complete")

    await wait_for_shutdown()

    logger.info("[yellow]Application shutdown")
    await telegram.shutdown()
    await noise_monitor.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
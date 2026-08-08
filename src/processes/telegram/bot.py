import asyncio
from logging import Logger
from typing import Literal

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from configs.app_settings import get_settings, AppSettings
from shared.logger import reg_logger
from shared.singleton_meta import Singleton


class TelegramService(Singleton):
    logger: Logger = reg_logger("[bold cyan]{Telegram}[/bold cyan]")
    app_settings: AppSettings = get_settings()

    def __init__(self):
        kw = {}
        if self.app_settings.telegram_proxy_string is not None:
            self.logger.debug("Using proxy string for telegram")
            session = AiohttpSession(proxy=self.app_settings.telegram_proxy_string)  # type: ignore
            kw['session'] = session

        self.bot = Bot(token=get_settings().telegram_token,
                       default=DefaultBotProperties(parse_mode=ParseMode.HTML),
                       **kw)
        self._dp = Dispatcher()
        self._polling_task: asyncio.Task | None = None

        from processes.telegram.router_registry import ROUTER_REGISTRY
        for router in ROUTER_REGISTRY:
            self._dp.include_router(router)

    def is_polling(self) -> bool:
        return self._polling_task is not None and not self._polling_task.done()

    async def start_polling(self) -> Literal[True]:
        self._polling_task = asyncio.create_task(self._dp.start_polling(self.bot))
        return True

    async def shutdown(self):
        await self._dp.stop_polling()
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()

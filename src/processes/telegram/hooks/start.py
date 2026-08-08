from aiogram import F
from aiogram.types import Message
from logging import Logger

from configs.telegram import TelegramConfig
from shared.logger import reg_logger
from processes.telegram.bot import TelegramService
from processes.telegram.router_registry import register_router

router = register_router("start")

@router.message(F.text == "/start")
async def start(message: Message):
    return await Start()(message)


class Start:
    def __init__(self):
        self.bot = TelegramService.get_instance().bot
        self.logger: Logger = reg_logger("[yellow]{ROUTER: [bold]" + self.__class__.__qualname__ + "[/bold]}[/yellow]")

    async def __call__(self, message: Message):
        assert message.from_user
        if message.from_user.id not in TelegramConfig.WHITELIST:
            self.logger.warning(f"[bold yellow]Access denied to /start for {message.from_user.id} ({message.from_user.url}")
            return

        self.logger.info(f"[bold cyan]{message.from_user.full_name} called start!")
        await message.reply("OK")



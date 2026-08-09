from aiogram import F
from aiogram.types import Message
from logging import Logger

from configs.telegram import TelegramConfig
from core.tuya.client import TuyaAsyncClient
from processes.noise_monitor.noise_monitor_service import NoiseMonitorService
from shared.logger import reg_logger
from processes.telegram.bot import TelegramService
from processes.telegram.router_registry import register_router

router = register_router("get_noise")

@router.message(F.text == "/get_noise")
async def get_noise(message: Message):
    return await GetNoise()(message)


class GetNoise:
    noise_monitor_service = NoiseMonitorService.get_instance()
    def __init__(self):
        self.bot = TelegramService.get_instance().bot
        self.logger: Logger = reg_logger("[yellow]{ROUTER: [bold]" + self.__class__.__qualname__ + "[/bold]}[/yellow]")

    async def __call__(self, message: Message):
        assert message.from_user
        if message.from_user.id not in TelegramConfig.WHITELIST:
            self.logger.warning(f"[bold yellow]Access denied to /get_noise for {message.from_user.id} ({message.from_user.url}")
            return

        self.logger.info(f"[bold cyan]{message.from_user.full_name} called get noise!")
        measurements = await self.noise_monitor_service.fetch_measurements()

        data = ""
        for device, level in measurements.values():
            data += f"<b>{device.device_name}</b>: <code>{level} дБ</code>"
        await message.reply(
            "<b>Текущий уровень шума</b>"
            "\n" + data
        )



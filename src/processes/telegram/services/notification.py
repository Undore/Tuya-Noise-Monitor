from logging import Logger

from aiogram.types import Message

from shared.logger import reg_logger
from shared.singleton_meta import Singleton
from processes.telegram.bot import TelegramService


class TelegramNotificationService(Singleton):
    logger: Logger = reg_logger("[bold cyan]{Telegram Notifications}[/bold cyan]")

    def __init__(self):
        self.telegram_service = TelegramService()

    async def send_notifications(self,
                                 telegram_ids: list[int],
                                 text: str) -> list[Message]:
        self.logger.info(f"[bold cyan]Sending a notification to {len(telegram_ids)} telegram ids")

        sent = []
        for telegram_id in telegram_ids:
            try:
                sent.append(
                    await self.telegram_service.bot.send_message(chat_id=telegram_id, text=text)
                )
            except Exception as e:
                self.logger.debug(f"[dim bold red]Failed to send notification to {telegram_id}: {e}")

        self.logger.info(f"[bold green]Successfully sent {len(sent)} out of {len(telegram_ids)} notifications ({len(telegram_ids) - len(sent)} failed)")
        return sent

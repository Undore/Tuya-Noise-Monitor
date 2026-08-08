import asyncio
from logging import Logger
from typing import Literal

from configs.devices import Device, DevicesConfig
from configs.telegram import TelegramConfig
from core.tuya.client import TuyaAsyncClient
from processes.telegram.bot import TelegramService
from processes.telegram.services.notification import TelegramNotificationService
from shared.http_client import APIException
from shared.logger import reg_logger
from shared.singleton_meta import Singleton


class NoiseMonitorService(Singleton):
    logger: Logger = reg_logger("[bold magenta]{NOISE MONITOR}[/bold magenta]")

    def __init__(self):
        self.telegram_service = TelegramService.get_instance()
        self.notification_service = TelegramNotificationService.get_instance()
        self._monitor_task: asyncio.Task | None = None

    async def start_monitoring(self) -> Literal[True]:
        self._monitor_task = asyncio.create_task(self.loop())
        return True

    async def shutdown(self):
        self.logger.info("[bold red]Shutting down")
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()

    async def loop(self):
        self.logger.info("[green]Starting loop")
        while True:
            try:
                measurements = await self.fetch_measurements()
                self.logger.info(f"Measurements: {measurements}")
            except Exception:
                self.logger.exception("[bold red]NoiseMonitor Loop exception")
            finally:
                await asyncio.sleep(5)

    async def fetch_measurements(self) -> dict[str, tuple[Device, float | int]]:
        """
        Fetch measurements for all devices registered in DevicesConfig
        :return: Dict[DeviceId, tuple[Device, dB_noise_level]]
        """
        results = {}

        async with TuyaAsyncClient() as client:
            for device in DevicesConfig.devices:
                try:
                    response = await client.get_device_status(device.tuya_device_id)
                except APIException as err:
                    self.logger.error(f"[bold red]Tuya responded with API Error on device {device}: "
                                      f"\n[blue]{err.__str__()}")
                    self.logger.debug("[cyan]Reporting to admins")
                    await self.notification_service.send_notifications(TelegramConfig.notifications_recipients.ERRORS,
                                                                       text="<b>⚠️ Устройство не отвечает ⚠️</b>"
                                                                            f"\nУстройство: <code>{device.__str__()}</code>"
                                                                            f"\nКод ошибки: <code>{err.status}</code>")
                    continue

                try:
                    value_units: int = next(iter(i for i in response['result'] if i['code'] == 'co2_value'),
                                            {})['value'] or 0
                    results[device.tuya_device_id] = device, value_units / 10
                except KeyError:
                    self.logger.error(f"[bold red]Tuya responded with unexpected json:"
                                      f"\n[blue]{response}")
                    self.logger.debug("[cyan]Reporting to admins")
                    await self.notification_service.send_notifications(TelegramConfig.notifications_recipients.ERRORS,
                                                                       text="<b>Устройство не отвечает</b>"
                                                                            f"\nНе удалось получить статус устройства <code>{device.__str__()}</code>"
                                                                            f"\nКод ошибки: {err.status}")
                    continue

        return results
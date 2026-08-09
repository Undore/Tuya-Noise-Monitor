import asyncio
from datetime import datetime, timedelta
from logging import Logger
from typing import Literal

from configs.app_settings import AppSettings, get_settings
from configs.devices.devices_config import DevicesConfig
from configs.devices.devices_config_interfaces import Device, AvgThreshold, StrikeThreshold, DeviceAlertConfig
from configs.telegram import TelegramConfig
from core.tuya.client import TuyaAsyncClient
from processes.telegram.bot import TelegramService
from processes.telegram.services.notification import TelegramNotificationService
from shared.http_client import APIException
from shared.logger import reg_logger
from shared.misc import get_now
from shared.singleton_meta import Singleton


class NoiseMonitorService(Singleton):
    logger: Logger = reg_logger("[bold magenta]{NOISE MONITOR}[/bold magenta]")
    app_settings: AppSettings = get_settings()

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

        last_device_measurements_timings: dict[str, list[tuple[datetime, float | int]]] = {}
        device_alerts_last_checks: dict[str, dict[int, datetime]] = {}
        while True:
            try:
                measurements = await self.fetch_measurements()
                if self.app_settings.verbose:
                    self.logger.debug(f"Measurements: {measurements}")
                current_hour = get_now().hour

                for device, dB in measurements.values():
                    max_alert_window = timedelta(minutes=max([i.threshold_window_minutes for i in device.alerts]))
                    last_device_measurements_timings[device.tuya_device_id] = [i for i in last_device_measurements_timings.get(device.tuya_device_id, [])
                                                                               if i[0] + max_alert_window >= get_now()]
                    last_device_measurements_timings[device.tuya_device_id].append((get_now(), dB))

                    for indx, alert in enumerate(device.alerts):
                        if current_hour not in alert.active_hours:
                            continue

                        last_check: datetime = (device_alerts_last_checks
                                                .setdefault(device.tuya_device_id, {})
                                                .setdefault(indx, get_now()))
                        if last_check + timedelta(minutes=alert.threshold_window_minutes) > get_now():
                            continue

                        window_values: list[float | int] = [i[1] for i in last_device_measurements_timings[device.tuya_device_id]
                                                            if i[0] + timedelta(alert.threshold_window_minutes) >= get_now()]
                        device_alerts_last_checks[device.tuya_device_id][indx] = get_now()

                        if isinstance(alert.threshold_mode, AvgThreshold):
                            avg_dB: float | int = round(sum(window_values) / len(window_values), 1)

                            if avg_dB >= alert.threshold_mode.threshold_dB:
                                await self.send_alarm(device, alert, f"<b>Средний уровень шума:</b> <code>{avg_dB} дБ</code>")

                        elif isinstance(alert.threshold_mode, StrikeThreshold):
                            strike_values = [i for i in window_values if i >= alert.threshold_mode.threshold_dB]

                            if len(strike_values) >= alert.threshold_mode.threshold_strikes:
                                await self.send_alarm(device, alert, f"<b>Cтрайков:</b> <code>{len(strike_values)}</code>")

                        else:
                            raise NotImplementedError(f"Invalid alert threshold mode: {type(alert.threshold_mode)}")


            except Exception:
                self.logger.exception("[bold red]NoiseMonitor Loop exception")
            finally:
                await asyncio.sleep(5)

    async def send_alarm(self, device: Device, alert: DeviceAlertConfig, threshold_notice_text: str | None):
        self.logger.info(f"[bold cyan]Sending an alarm for device {device} on alert {alert.alert_name}")
        mode = "Страйк" if isinstance(alert.threshold_mode, StrikeThreshold) else "Среднее"
        await self.notification_service.send_notifications(
            telegram_ids=TelegramConfig.notifications_recipients.ALARMS,
            text=f"<b>🔔 Превышен уровень шума (<code>{mode}</code>) 🔔 </b>"
                 f"\n<b>Устройство:</b> <code>{device.device_name}</code>"
                 f"\n<b>Алёрт:</b> <code>{alert.alert_name}</code>"
                 +
                 ( f"\n{threshold_notice_text}" if threshold_notice_text else "")
        )

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
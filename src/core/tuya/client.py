import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from tuya_connector import TuyaOpenAPI

from configs.app_settings import AppSettings, get_settings
from shared.http_client import APIException
from shared.logger import reg_logger


class TuyaAsyncClient:
    """
    A client for async TuyaAPI Interaction
    Token is short-lived, so aenter is advised
    """

    app_settings: AppSettings = get_settings()

    def __new__(cls, *args, **kwargs):
        for l in ['tuya iot', 'urllib3']:
            logging.getLogger(l).setLevel(logging.CRITICAL)

        return super().__new__(cls)

    def __init__(self, verbose: bool = False):
        API_ENDPOINT = "https://openapi.tuyaeu.com"
        self.sdk_client = TuyaOpenAPI(
            API_ENDPOINT,
            self.app_settings.tuya_client_id,
            self.app_settings.tuya_secret,
        )
        self.loop = asyncio.get_event_loop()

        self.logger = reg_logger("[bold yellow]{TUYA}[/bold yellow]",
                                 level="DEBUG" if verbose else "INFO")

        self.executor = ThreadPoolExecutor(max_workers=1)

    async def __aenter__(self):
        await self.loop.run_in_executor(self.executor,
                                        self.sdk_client.connect)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown(cancel_futures=True, wait=False)

    async def get_devices_status(self,device_ids: list[str]) -> dict[str, dict]:
        """
        Get statuses of multiple Tuya devices.

        Tuya allows up to 20 device IDs per request.
        """
        if not device_ids:
            return {}

        if len(device_ids) > 20:
            raise ValueError("Tuya allows a maximum of 20 devices per request")

        self.logger.debug(
            f"[cyan]Fetching device statuses for {len(device_ids)} devices"
        )

        endpoint = "/v1.0/iot-03/devices/status"

        func = lambda: self.sdk_client.get(
            endpoint,
            {
                "device_ids": ",".join(device_ids),
            },
        )

        response: dict = await self.loop.run_in_executor(
            self.executor,
            func,
        )

        if response["success"] is False:
            self.logger.error(
                f"[bold red]Failed to fetch device statuses: "
                f"[cyan]{response}"
            )

            raise APIException(
                status=400,
                message=f"Tuya responded with error: {response}",
            )

        self.logger.debug(
            f"[green]API Response for {endpoint}: {response}"
        )

        return response
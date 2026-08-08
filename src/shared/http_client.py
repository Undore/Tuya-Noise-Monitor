import asyncio
import json
import urllib.request
from typing import Any, Literal, cast, Optional

import aiohttp
from aiohttp import FormData
from pydantic import ConfigDict, computed_field, TypeAdapter

from configs.app_settings import get_settings
from interfaces.base_model_v2 import BaseModelV2
from shared.logger import reg_logger
from settings import LOG_LEVEL

HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


class APIException(Exception):
    def __init__(
        self,
        status: int,
        message: str,
        body: Optional[str | bytes | bytearray] = None,
        headers: dict[str, str] | None = None
    ):
        self.status = status
        self.message = message
        self.body = body
        self.headers = headers or {}
        super().__init__(f"{status}: {message}")

    @property
    def content_type(self) -> str | None:
        return self.headers.get("Content-Type")

    def __str__(self):
        return f"[API Error {self.status}: {self.message}]"

    def __repr__(self) -> str:
        return f"<APIException status={self.status} message={self.message}>"

    def json(self):
        if self.body is None:
            return None

        if isinstance(self.body, bytes):
            return json.loads(self.body.decode("utf-8"))

        assert self.body is not None
        return json.loads(self.body)


class HTTPClientResponse(BaseModelV2):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: int
    headers: dict[str, str]
    url: str
    content: str | bytes

    @computed_field
    @property
    def ok(self) -> bool:
        return 200 <= self.status < 400

    @computed_field
    @property
    def content_type(self) -> str | None:
        return self.headers.get("Content-Type")

    def raise_for_status(self):
        if self.status < 400:
            return

        raise APIException(
            status=self.status,
            message=self.content if isinstance(self.content, str) else f"<APIError status={self.status}>",
            body=self.content,
            headers=self.headers,
        )

    def json(self, *args, **kwargs):
        if args or kwargs:
            raise ValueError("Do not mistake HTTPClientResponse for pydantic deprecated .json method. Use model_dump_json instead")
    
        if isinstance(self.content, bytes):
            return json.loads(self.content.decode("utf-8"))

        return json.loads(self.content)

    def __str__(self):
        return f"[Response {self.status} on {self.url}]"

    def __repr__(self):
        return f"<HTTPClientResponse status={self.status}>"


class AsyncHTTPClient:
    settings = get_settings()

    def __init__(
        self,
        base_url: str | None = None,
        default_headers: dict[str, str] | None = None,
        default_timeout: int = 15,
        proxy_string: Optional[str] = None,
        log_level: str = LOG_LEVEL
    ):
        self.proxy = proxy_string
        self.base_url = base_url.rstrip("/") if base_url else None
        self.default_headers = default_headers or {}
        self.timeout = aiohttp.ClientTimeout(total=default_timeout)

        self.logger = reg_logger("[bold cyan]{HTTP}[/bold cyan]", level=log_level)
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self.default_headers,
                timeout=self.timeout,
            )
        
        assert self._session
        return self._session

    async def close(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()

    def _build_url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path

        if not self.base_url:
            raise ValueError("base_url is not defined")

        return f"{self.base_url}/{path.lstrip('/')}"

    def _stealth_sync_request(self, method: str, url: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0"
        }

        req = urllib.request.Request(
            method=method,
            url=url,
            headers=headers,
        )

        with urllib.request.urlopen(req) as response:
            return response.read()

    async def request_stealth(self, method: str, url: str):
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            None,
            self._stealth_sync_request,
            method,
            url
        )

    async def request(self,
                      method: HTTPMethod,
                      path: str,
                      *,
                      raise_for_status: bool = True,
                      json_payload: Optional[dict | list] = None,
                      data: Any | FormData | None = None,
                      params: dict | None = None,
                      headers: dict[str, str] | None = None,
                      timeout_retries: int = 3,
                      decode_bytes: bool = True,
                      timeout_seconds: int | None = None) -> HTTPClientResponse:
        url = self._build_url(path)
        if json_payload is not None:
            json_payload = TypeAdapter(type(json_payload)).dump_python(json_payload, mode="json")

        if data is not None and not isinstance(data, FormData):
            data = TypeAdapter(type(data)).dump_python(data, mode="json")

            if isinstance(data, dict) and not all(isinstance(i, str) for i in data.values()):
                self.logger.warning(f"[bold yellow]Detected non-string value in HTML Data for {url}. Please stringify!")

        timeout = (
            self.timeout
            if timeout_seconds is None
            else aiohttp.ClientTimeout(total=timeout_seconds)
        )

        last_error: Exception | None = None

        self.logger.debug(
            f"[bold cyan]Requesting [magenta]{method.upper()} {url}[/magenta] "
            f"[dim](Timeout {timeout.total}s)"
        )

        if self.proxy:
            self.logger.debug(f"[dim]Using proxy: {str(self.proxy)[:10]}****")

        for attempt in range(timeout_retries + 1):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=json_payload,
                    data=data,
                    params=params,
                    headers=headers,
                    proxy=self.proxy,
                    timeout=timeout
                ) as response:

                    content = await response.read()

                    if decode_bytes:
                        content = content.decode("utf-8", errors="replace")

                    result = HTTPClientResponse(
                        status=response.status,
                        headers=cast(dict[str, str], 
                                     dict(response.headers)),
                        url=str(response.url),
                        content=content
                    )

                    if response.status >= 400:
                        self.logger.error(
                            (f"[dim cyan]({attempt}) [/dim cyan]" if attempt > 0 else "")
                            + f"[bold red]Request failed with status code "
                              f"{response.status} on [magenta]{url}[/magenta]:"
                              f"[dim gray]\n{result.content[:1000]}"
                        )

                        if raise_for_status:
                            result.raise_for_status()

                        return result

                    self.logger.debug(
                        "[bold green]Request succeeded"
                        + (f" after {attempt} attempts" if attempt > 0 else "")
                    )

                    return result

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.error(f"[red]Connection timeout. Retrying in 3 seconds (Attempt {attempt + 1})")
                await asyncio.sleep(3)
                last_error = e

                if attempt == timeout_retries:
                    raise

        raise last_error

    async def get(self, path: str, **kwargs) -> HTTPClientResponse:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> HTTPClientResponse:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> HTTPClientResponse:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> HTTPClientResponse:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> HTTPClientResponse:
        return await self.request("DELETE", path, **kwargs)

    async def head(self, path: str, **kwargs) -> HTTPClientResponse:
        return await self.request("HEAD", path, **kwargs)

    async def options(self, path: str, **kwargs) -> HTTPClientResponse:
        return await self.request("OPTIONS", path, **kwargs)


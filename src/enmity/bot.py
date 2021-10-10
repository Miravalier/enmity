import asyncio
import functools
import sys
from datetime import datetime, timedelta
from typing import Any, Dict

import aiohttp
from aiohttp.client import ClientSession

from . import __version__


PROJECT_URL = "https://github.com/Miravalier/enmity.git"
USER_AGENT = " ".join(
    (
        f"DiscordBot ({PROJECT_URL} {__version__})",
        f"Python/{sys.version_info.major}.{sys.version_info.minor}",
        f"aiohttp/{aiohttp.__version__}",
    )
)


def aiohttp_session(func):
    @functools.wraps(func)
    async def session_wrapper(*args, **kwargs):
        if "session" not in kwargs:
            async with aiohttp.ClientSession() as session:
                kwargs["session"] = session
                return await func(*args, **kwargs)
        else:
            return await func(*args, **kwargs)

    return session_wrapper


class RateLimitError(Exception):
    pass


class Bot:
    rest_url = "https://discord.com/api/v9"

    def __init__(self) -> None:
        self.ws_url: str = None
        self.token: str = None
        self.headers: Dict[str, str] = {"User-Agent": USER_AGENT}

    @aiohttp_session
    async def get(self, endpoint: str, *, session: ClientSession) -> Any:
        async with session.get(self.rest_url + endpoint, headers=self.headers) as response:
            response.raise_for_status()
            return await response.json()

    @aiohttp_session
    async def handle_event(self, event: Dict, *, session: ClientSession) -> None:
        print("Handling:", event)

    def run(self, token: str) -> None:
        asyncio.run(self.async_run(token))

    async def async_run(self, token: str) -> None:
        # Store the token
        self.token = token
        self.headers["Authorization"] = f"Bot {token}"
        # Find the WS gateway info
        gateway_info = await self.get("/gateway/bot")
        print("Gateway Info", gateway_info)
        self.ws_url = gateway_info["url"]
        self.recommended_shards = gateway_info["shards"]
        self.session_limits = gateway_info["session_start_limit"]
        self.session_limits["reset_after"] = datetime.now() + timedelta(milliseconds=self.session_limits["reset_after"])
        print("Session Limits:", self.session_limits)
        if self.session_limits["remaining"] <= 1:
            raise RateLimitError(
                "Insufficient session starts remaining: "
                f'{self.session_limits["remaining"]}/'
                f'{self.session_limits["total"]}, '
                f'resets after {self.session_limits["reset_after"]}'
            )
        # Connect to the WS gateway
        print(f"Connecting to discord gateway at {self.ws_url}")
        await self.connect(self.ws_url)
        print(f"Connection closed to discord gateway")

    @aiohttp_session
    async def connect(self, url: str, *, session: ClientSession) -> None:
        async with session.ws_connect(url) as websocket:
            async for ws_message in websocket:
                if ws_message.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_event(ws_message.json(), session=session)
                else:
                    raise TypeError(f"Unrecognized ws message type: {ws_message.type}")

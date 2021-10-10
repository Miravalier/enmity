import asyncio
import functools
import random
import sys
from asyncio.tasks import Task
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Set

import aiohttp
from aiohttp.client import ClientSession
from aiohttp.client_ws import ClientWebSocketResponse

from . import __version__
from .intents import Intent
from .op import Op

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


@dataclass
class RateLimit:
    limit: int
    remaining: int
    reset_after: datetime


class RateLimitError(Exception):
    pass


class Bot:
    intents = Intent.NONE
    rest_url = "https://discord.com/api/v9"
    gateway_version = 9
    encoding = "json"

    def __init__(self):
        self.guilds: Set[int] = set()
        self.rate_limits: Dict[str, RateLimit] = {}
        self.rate_limit_buckets: Dict[str, str] = {}
        self.ready: bool = False
        self.session_id: str = None
        self.user_id: int = None
        self.username: str = None
        self.seq: int = None
        self.websocket: ClientWebSocketResponse = None
        self.heartbeat_task: Task = None
        self.heartbeat_interval: int = None
        self.last_heartbeat: datetime = None
        self.ws_url: str = None
        self.token: str = None
        self.headers: Dict[str, str] = {"User-Agent": USER_AGENT}
        self.handlers: Dict[str, Callable] = {}

    async def send(self, data: Any):
        await self.websocket.send_json(data)

    async def send_heartbeat(self):
        initial_delay = random.random() * self.heartbeat_interval
        print(f"Sleeping for {initial_delay:.2f} seconds, then I'll send heartbeat DEBUG")
        await asyncio.sleep(initial_delay)
        while True:
            print("Sending heartbeat ...")
            await self.send({"op": Op.HEARTBEAT, "d": self.seq})
            await asyncio.sleep(self.heartbeat_interval)

    async def send_identify(self):
        await self.send(
            {
                "op": Op.IDENTIFY,
                "d": {
                    "token": self.token,
                    "intents": self.intents,
                    "properties": {
                        "$os": "linux",
                        "$browser": "enmity",
                        "$device": "enmity",
                    },
                },
            }
        )

    @aiohttp_session
    async def get(self, endpoint: str, **kwargs) -> Any:
        return await self.api_request("get", endpoint, **kwargs)

    @aiohttp_session
    async def post(self, endpoint: str, **kwargs) -> Any:
        return await self.api_request("post", endpoint, **kwargs)

    @aiohttp_session
    async def put(self, endpoint: str, **kwargs) -> Any:
        return await self.api_request("put", endpoint, **kwargs)

    @aiohttp_session
    async def patch(self, endpoint: str, **kwargs) -> Any:
        return await self.api_request("patch", endpoint, **kwargs)

    @aiohttp_session
    async def delete(self, endpoint: str, **kwargs) -> Any:
        return await self.api_request("delete", endpoint, **kwargs)

    @aiohttp_session
    async def api_request(
        self, method: str, endpoint: str, *, session: ClientSession, headers: Dict[str, str] = None, **kwargs
    ) -> Any:
        rate_limit_key = f"{method}-{endpoint}"
        # Inject bot global headers into provided request headers
        if headers is None:
            headers = self.headers
        else:
            headers.update(self.headers)
        # Check if we were previously warned by X-RateLimit
        bucket = self.rate_limit_buckets.get(rate_limit_key)
        rate_limit: RateLimit = self.rate_limits.get(bucket)
        if rate_limit is not None and rate_limit.remaining <= 1:
            # If no reset time was provided, return a rate limit error
            if rate_limit.reset_after is None:
                raise RateLimitError(f"Self-enforcing rate limit on bucket {bucket}")
            # If a reset time was provided, sleep until that time passes
            now = datetime.now()
            if rate_limit.reset_after > now:
                sleep_seconds = (rate_limit.reset_after - now).total_seconds()
                print(f"Sleeping due to rate limit on {bucket} for {sleep_seconds} seconds")
                await asyncio.sleep(sleep_seconds)
        # Perform the request
        request_method = getattr(session, method)
        async with request_method(self.rest_url + endpoint, headers=headers, **kwargs) as response:
            # Store the rate limit information if present
            bucket = response.headers.get("X-RateLimit-Bucket")
            if bucket is not None:
                limit = int(response.headers.get("X-RateLimit-Limit", 0))
                remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                reset_after_seconds = float(response.headers.get("X-RateLimit-Reset-After", 0))
                reset_timestamp = float(response.headers.get("X-RateLimit-Reset", 0))
                if reset_after_seconds:
                    reset_after = datetime.now() + timedelta(seconds=reset_after_seconds)
                elif reset_timestamp:
                    reset_after = datetime.fromtimestamp(reset_timestamp)
                else:
                    reset_after = None
                self.rate_limits[bucket] = RateLimit(limit, remaining, reset_after)
                self.rate_limit_buckets[rate_limit_key] = bucket
            # Re-map 429 to RateLimitError from HTTP exception
            if response.status == 429:
                raise RateLimitError(f"Rate limit enforced by server on bucket {bucket}")
            # Raise any normal HTTP exceptions that may have occurred
            response.raise_for_status()
            # Return the json response
            return await response.json()

    def register(self, payload_type: str):
        def register_handler(func: Callable):
            self.handlers[payload_type] = func
            return func

        return register_handler

    async def get_handler(self, payload_type: str):
        # Check handler cache
        if payload_type in self.handlers:
            return self.handlers[payload_type]
        # Check for on_<payload_type> method and cache it if found
        handler = getattr(self, f"on_{payload_type.lower()}", None)
        # Fallback to just printing
        if handler is None:
            print(f"Unrecognized payload type {payload_type}")
        else:
            self.handlers[payload_type] = handler
            return handler

    @aiohttp_session
    async def handle_event(self, event: Dict, *, session: ClientSession) -> None:
        self.last_heartbeat = datetime.now()
        # Update sequence number if present
        seq = event.get("s")
        if seq:
            if self.seq is None:
                self.seq = seq
            else:
                self.seq = max(self.seq, seq)
        # Dispatch Event
        if event["op"] == Op.DISPATCH:
            event_handler = await self.get_handler(event["t"])
            await event_handler(event["d"])
        # Gateway Hello
        elif event["op"] == Op.HELLO:
            print("Received Gateway HELLO")
            self.heartbeat_interval = event["d"]["heartbeat_interval"] / 1000
            self.heartbeat_task = asyncio.create_task(self.send_heartbeat())
            await self.send_identify()
        # Heartbeat request
        elif event["op"] == Op.HEARTBEAT:
            print("Received HEARTBEAT request")
            await self.send({"op": Op.HEARTBEAT_ACK})
        # Heartbeat response
        elif event["op"] == Op.HEARTBEAT_ACK:
            print("... received heartbeat ack")
        # Invalid session
        elif event["op"] == Op.INVALID_SESSION:
            raise ValueError("Invalid Session")
        # Reconnect
        elif event["op"] == Op.RECONNECT:
            print("Received RECONNECT request")
            await self.resume()
        # Unrecognized opcode
        else:
            raise TypeError(f'Unrecognized opcode {event["op"]}')

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
        print(f"Connection closed to discord gateway:", self.websocket.close_code)

    async def resume(self):
        if not self.ready:
            raise ValueError("Cannot resume before ready event")
        await self.send(
            {
                "op": Op.RESUME,
                "d": {
                    "token": self.token,
                    "session_id": self.session_id,
                    "seq": self.seq,
                },
            }
        )

    @aiohttp_session
    async def connect(self, url: str, *, session: ClientSession) -> None:
        self.session_limits["remaining"] -= 1
        async with session.ws_connect(url + f"?v={self.gateway_version}&encoding={self.encoding}") as websocket:
            self.websocket = websocket
            async for ws_message in websocket:
                if ws_message.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_event(ws_message.json(), session=session)
                else:
                    raise TypeError(f"Unrecognized ws message type: {ws_message.type}")

    async def on_ready(self, payload: Dict[str, Any]):
        for guild_data in payload["guilds"]:
            self.guilds.add(int(guild_data["id"]))
        self.session_id = payload["session_id"]
        self.user_id = int(payload["user"]["id"])
        self.username = payload["user"]["username"]
        self.ready = True
        print("Gateway ready message received")

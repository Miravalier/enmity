from typing import Dict
import aiohttp


PROJECT_URL = "https://github.com/Miravalier/enmity.git"
VERSION = "0.0.1"
USER_AGENT = f"DiscordBot ({PROJECT_URL} {VERSION})"


class Bot:
    rest_url = "https://discord.com/api/v9"

    def __init__(self) -> None:
        self.token = ""

    async def get(endpoint: str):
        pass

    async def handle_event(self, event: Dict):
        print("Handling:", event)

    async def run(self, token: str):
        self.token = token
        self.headers["Authorization"] = f"Bot {token}"
        await self.get("/gateway/bot")
        # await self.connect(ws_url)

    async def connect(self, url: str):
        session = aiohttp.ClientSession()
        async with session.ws_connect(url) as websocket:
            async for ws_message in websocket:
                if ws_message.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_event(ws_message.json())
                else:
                    print("Unrecognized Message Type:", ws_message.type)
                    break

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, IntFlag
from typing import Any, Dict, List, Union

from .components import Component
from .embeds import Embed
from .messages import Message
from .users import User


class InteractionType(IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3


class InteractionCallbackType(IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7


class InteractionCallbackFlags(IntFlag):
    NONE = 0
    EPHEMERAL = 1 << 6


class CommandType(IntEnum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3


class CommandOptionType(IntEnum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10


class CommandPermissionType(IntEnum):
    ROLE = 1
    USER = 2


@dataclass
class Parameter:
    name: str
    type: CommandOptionType
    description: str = ""
    required: bool = True
    choices: List[Dict[str, Union[str, int, float]]] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)

    def serialize(self):
        result = {"name": self.name, "type": self.type, "description": self.description}
        if self.type in (CommandOptionType.SUB_COMMAND, CommandOptionType.SUB_COMMAND_GROUP):
            result["options"] = [parameter.serialize() for parameter in self.parameters]
        else:
            result["required"] = self.required
        if self.choices:
            result["choices"] = [{"name": key, "value": value} for key, value in self.choices.items()]


@dataclass
class Command:
    name: str
    type: CommandType
    description: str = ""
    default_permission: bool = True
    parameters: List[Parameter] = field(default_factory=list)

    def serialize(self):
        result = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "default_permission": self.default_permission,
        }
        if self.type == CommandType.CHAT_INPUT:
            result["options"] = [parameter.serialize() for parameter in self.parameters]
        return result


@dataclass
class Interaction:
    bot: Any
    type: InteractionType
    id: int
    source: User
    token: str
    command_type: CommandType = None
    target: Union[User, Message] = None
    guild_id: int = None
    channel_id: int = None
    application_id: int = None

    async def defer(self):
        await self.callback(InteractionCallbackType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE)

    async def callback(self, response_type: InteractionCallbackType, response_data: Any = None):
        response = {"type": response_type}
        if response_data is not None:
            response["data"] = response_data
        return await self.bot.post(f"/interactions/{self.id}/{self.token}/callback", json=response)


@dataclass
class InteractionCallback:
    content: str = None
    embeds: List[Embed] = field(default_factory=list)
    components: List[Component] = field(default_factory=list)
    allowed_mentions: Any = None
    flags: InteractionCallbackFlags = InteractionCallbackFlags.NONE
    tts: bool = None

    def serialize(self):
        response = {}
        if self.content is not None:
            response["content"] = self.content
        if self.embeds:
            response["embeds"] = [embed.serialize() for embed in self.embeds]
        if self.allowed_mentions is not None:
            response["allowed_mentions"] = self.allowed_mentions
        if self.flags != InteractionCallbackFlags.NONE:
            response["flags"] = self.flags
        if self.components:
            response["components"] = [component.serialize() for component in self.components]
        if self.tts is not None:
            response["tts"] = self.tts
        return response

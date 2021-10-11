from dataclasses import dataclass, field
from typing import List


@dataclass
class User:
    id: int
    username: str = None
    discriminator: str = None
    nickname: str = None
    bot: bool = False
    avatar: str = None
    roles: List[int] = field(default_factory=list)
    deaf: bool = None
    mute: bool = None

    def __str__(self):
        if self.nickname:
            return f"{self.username}#{self.discriminator} ({self.nickname})"
        else:
            return f"{self.username}#{self.discriminator}"

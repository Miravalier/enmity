from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from .colors import Color


@dataclass
class Embed:
    title: str = None
    description: str = None
    fields: Dict[str, str] = field(default_factory=dict)
    url: str = None
    timestamp: datetime = None
    color: Color = None
    footer: Any = None
    image: Any = None
    thumbnail: Any = None
    video: Any = None
    provider: Any = None
    author: Any = None

    def serialize(self):
        result = {}
        if self.title is not None:
            result["title"] = self.title
        if self.description is not None:
            result["description"] = self.description
        if self.url is not None:
            result["url"] = self.url
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp.isoformat()
        if self.color is not None:
            result["color"] = int(self.color)
        if self.footer is not None:
            result["footer"] = self.footer
        if self.image is not None:
            result["image"] = self.image
        if self.thumbnail is not None:
            result["thumbnail"] = self.thumbnail
        if self.video is not None:
            result["video"] = self.video
        if self.provider is not None:
            result["provider"] = self.provider
        if self.author is not None:
            result["author"] = self.author
        if self.fields:
            result["fields"] = [{"name": str(key), "value": str(value)} for key, value in self.fields.items()]
        return result

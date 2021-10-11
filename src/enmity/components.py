from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, List


class ComponentType(IntEnum):
    ACTION_ROW = 1
    BUTTON = 2
    SELECT_MENU = 3


class ButtonStyle(IntEnum):
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5


@dataclass
class SelectOption:
    label: str
    value: str
    description: str = None
    # emoji: partial {name, id, animated}
    default: bool = None

    def serialize(self):
        result = {"label": self.label, "value": self.value}
        if self.description is not None:
            result["description"] = self.description
        if self.default is not None:
            result["default"] = self.default
        return result


def generate_component_id() -> str:
    return secrets.token_hex(16)


@dataclass
class Component:
    type: ComponentType
    disabled: bool = None
    style: ButtonStyle = None
    label: str = None
    # emoji: partial {name, id, animated}
    url: str = None
    options: List[SelectOption] = field(default_factory=list)
    placeholder: str = None
    min_values: int = None
    max_values: int = None
    components: List[Component] = field(default_factory=list)
    custom_id: str = field(default_factory=generate_component_id)

    def serialize(self):
        result = {"type": self.type}
        if self.custom_id is not None:
            result["custom_id"] = self.custom_id
        if self.disabled is not None:
            result["disabled"] = self.disabled
        if self.style is not None:
            result["style"] = self.style
        if self.label is not None:
            result["label"] = self.label
        if self.url is not None:
            result["url"] = self.url
        if self.options:
            result["options"] = [option.serialize() for option in self.options]
        if self.placeholder is not None:
            result["placeholder"] = self.placeholder
        if self.min_values is not None:
            result["min_values"] = self.min_values
        if self.max_values is not None:
            result["max_values"] = self.max_values
        if self.components:
            result["components"] = [component.serialize() for component in self.components]
        return result


class ActionRow(Component):
    def __init__(self, *components: Component):
        super().__init__(ComponentType.ACTION_ROW, components=components)


class Button(Component):
    def __init__(self, label: str, *, style: ButtonStyle = ButtonStyle.PRIMARY, disabled: bool = None, url: str = None):
        super().__init__(ComponentType.BUTTON, label=label, style=style, disabled=disabled, url=url)


class SelectMenu(Component):
    def __init__(
        self,
        *options: SelectOption,
        disabled: bool = None,
        placeholder: str = None,
        min_values: int = None,
        max_values: int = None
    ):
        super().__init__(
            ComponentType.SELECT_MENU,
            options=options,
            disabled=disabled,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
        )

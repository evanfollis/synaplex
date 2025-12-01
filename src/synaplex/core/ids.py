# synaplex/core/ids.py

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldId:
    value: str


@dataclass(frozen=True)
class AgentId:
    value: str


@dataclass(frozen=True)
class MessageId:
    value: str

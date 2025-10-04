from collections import ChainMap
from dataclasses import dataclass
from typing import Any, get_type_hints

from build123d import Part


@dataclass
class Result:
    part: Part
    locals: Any
    name: str | None = None


class ParamsBase:
    @classmethod
    def annotations(cls) -> ChainMap:
        return ChainMap(*(get_type_hints(c) for c in cls.__mro__))


@dataclass(frozen=True)
class ThreadedInsert(ParamsBase):
    diameter: float
    depth: float
    wall: float

from collections import ChainMap
from dataclasses import dataclass
from typing import Any, get_type_hints, override

from build123d import Part


@dataclass
class Result:
    part: Part
    locals: Any
    name: str | None = None


class ParamsBase:
    @classmethod
    def _annotations(cls) -> ChainMap:
        return ChainMap(*(get_type_hints(c) for c in cls.__mro__))

    def _dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self._annotations().keys()}


@dataclass(frozen=True)
class ThreadedInsert(ParamsBase):
    diameter: float
    depth: float
    wall: float

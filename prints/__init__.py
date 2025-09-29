from collections import OrderedDict
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import Any, Mapping

from build123d import Part


@dataclass
class Result:
    part: Part
    locals: Any
    name: str | None = None


class ParamsMeta(type):
    @classmethod
    def __prepare__(cls, *args, **kwargs):
        return OrderedDict()

    def __new__(cls, name, bases, classdict):
        keys = [key for key in classdict.keys() if not key.startswith("__")]

        classdict["__ordered__"] = sorted(keys)

        return type.__new__(cls, name, bases, classdict)


class ParamsBase(object, metaclass=ParamsMeta):
    def __iter__(self):
        for attr in self.__ordered__:
            yield getattr(self, attr)


def _getargspec(
    params: Mapping[str, Parameter],
) -> tuple[list[str], list[str], list[str]]:
    args, kwargs, has_default = [], [], []
    for name, param in params.items():
        if param.kind == param.VAR_POSITIONAL or param.kind == param.VAR_KEYWORD:
            # can skip variable args and kwargs; they don't need to be provided
            continue
        elif param.kind == param.KEYWORD_ONLY:
            kwargs.append(name)
        else:
            args.append(name)

        if param.default is not param.empty:
            has_default.append(name)

    return (args, kwargs, has_default)


def check_module(mod) -> None:
    if not hasattr(mod, "Params"):
        raise TypeError("module does not export `Params`")
    if not hasattr(mod, "main"):
        raise TypeError("module does not export a function `main`")

    if not issubclass(mod.Params, ParamsBase):
        raise TypeError("module's `Params` export must subclass `prints.ParamsBase`")

    sig = signature(mod.main).parameters
    args, kwargs, has_default = _getargspec(sig)
    if not args:
        raise TypeError("module must accept at least one parameter")
    params = args.pop(0)
    if sig[params].annotation != mod.Params:
        raise TypeError(
            "module's `main` function must accept an instance of `Params` as its first parameter"
        )

    args_without_default = [a for a in args if a not in has_default]
    kwargs_without_default = [k for k in kwargs if k not in has_default]
    if args_without_default:
        raise TypeError(
            f"module may not contain args without defaults; found {', '.join(args_without_default)}"
        )
    if kwargs_without_default:
        raise TypeError(
            f"module may not contain kwargs without defaults; found {', '.join(kwargs_without_default)}"
        )


@dataclass(frozen=True)
class ThreadedInsert(ParamsBase):
    diameter: float
    depth: float
    wall: float

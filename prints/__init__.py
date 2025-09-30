from argparse import (
    ArgumentParser,
    Action,
    BooleanOptionalAction,
    Namespace,
)
from collections import ChainMap
from collections.abc import Sequence
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import Any, Mapping, override

from build123d import Part


@dataclass
class Result:
    part: Part
    locals: Any
    name: str | None = None


class ParamsBase:
    @classmethod
    def annotations(cls) -> ChainMap:
        return ChainMap(
            *(c.__annotations__ for c in cls.__mro__ if "__annotations__" in c.__dict__)
        )


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


class PrefixedAction(Action):
    def __init__(self, *args, prefix: str | None, **kwargs):
        self._prefix = prefix
        super().__init__(*args, **kwargs)

    @override
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        if self._prefix:
            namespace = getattr(namespace, self._prefix)

        if option_string in self.option_strings:
            setattr(namespace, self.dest, values)


class PrefixedBooleanAction(BooleanOptionalAction):
    def __init__(self, *args, prefix: str | None, **kwargs):
        self._prefix = prefix
        super().__init__(*args, **kwargs)

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        if self._prefix:
            namespace = getattr(namespace, self._prefix)

        return super().__call__(parser, namespace, values, option_string)


def _join_prefix(dest: str, prefix: str | None = None) -> str:
    if not prefix:
        return dest

    return f"{prefix}_{dest}"


def _add_param_parser_args(
    param_parser: ArgumentParser, cls: type[ParamsBase], *, prefix: str | None = None
) -> None:
    for k, v in cls.annotations().items():
        if issubclass(v, ParamsBase):
            _add_param_parser_args(param_parser, v, prefix=k)
            continue

        kwargs = {
            "dest": k,
            "type": v,
            "default": getattr(cls, k),
            "prefix": prefix,
            "action": PrefixedAction,
        }

        if v is bool:
            del kwargs["type"]
            kwargs["action"] = PrefixedBooleanAction

        param_parser.add_argument(f"--{_join_prefix(k, prefix)}", **kwargs)


def create_param_parser(
    cls: type[ParamsBase], *, description: str | None
) -> ArgumentParser:
    param_parser = ArgumentParser(description=description)
    _add_param_parser_args(param_parser, cls)
    return param_parser


@dataclass(frozen=True)
class ThreadedInsert(ParamsBase):
    diameter: float
    depth: float
    wall: float

from collections.abc import Mapping
from dataclasses import fields
from inspect import Parameter, signature
from types import ModuleType
from typing import Any, TypeGuard

from .params import ParamsBase


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


def check_module(mod: ModuleType) -> None:
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


Primitive = int | float | bool | str
primitives = (int, float, bool, str)


def is_primitive(var: object) -> TypeGuard[Primitive]:
    return type(var) in primitives


def _flatten_params(
    params: ParamsBase, accumulator: dict[str, Primitive], path: list[str]
) -> None:
    for k, v in params._dict().items():
        parts = [*path, k]
        if is_primitive(v):
            key = ".".join(parts)
            accumulator[key] = v
        elif isinstance(v, ParamsBase):
            _flatten_params(v, accumulator, parts)
        else:
            raise ValueError(
                f"field ``{k}`` has value that is not a primitive, nor an instance of ``ParamsBase``"
            )


def flatten_params(params: ParamsBase) -> dict[str, Primitive]:
    accumulator = {}
    _flatten_params(params, accumulator, [])
    return accumulator

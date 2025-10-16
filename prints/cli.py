#!/usr/bin/env python3
import datetime
import os
import sys
from argparse import (
    Action,
    ArgumentParser,
    BooleanOptionalAction,
    Namespace,
)
from collections.abc import Sequence
from importlib import import_module
from types import ModuleType
from typing import Any, override

from build123d import Mesher, Shape, export_step, export_stl

from .params import ParamsBase, Result
from .utils import check_module


class PrefixedAction(Action):
    def __init__(self, *args, prefixes: list[str] | None, **kwargs):
        self._prefixes = prefixes or []
        super().__init__(*args, **kwargs)

    @override
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        for prefix in self._prefixes:
            namespace = getattr(namespace, prefix)

        if option_string in self.option_strings:
            setattr(namespace, self.dest, values)


class PrefixedBooleanAction(BooleanOptionalAction):
    def __init__(self, *args, prefixes: list[str] | None, **kwargs):
        self._prefixes = prefixes or []
        super().__init__(*args, **kwargs)

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        for prefix in self._prefixes:
            namespace = getattr(namespace, prefix)

        return super().__call__(parser, namespace, values, option_string)


def _join_prefix(dest: str, prefixes: list[str] | None = None) -> str:
    if not prefixes:
        return dest

    return f"{'_'.join(prefixes)}_{dest}"


def _add_param_parser_args(
    param_parser: ArgumentParser,
    cls: type[ParamsBase],
    *,
    prefixes: list[str] | None = None,
) -> None:
    for k, v in cls.annotations().items():
        if issubclass(v, ParamsBase):
            if not prefixes:
                prefixes = []
            _add_param_parser_args(param_parser, v, prefixes=[*prefixes, k])
            continue

        kwargs = {
            "dest": k,
            "type": v,
            "default": getattr(cls, k),
            "prefixes": prefixes,
            "action": PrefixedAction,
        }

        if v is bool:
            del kwargs["type"]
            kwargs["action"] = PrefixedBooleanAction

        param_parser.add_argument(f"--{_join_prefix(k, prefixes)}", **kwargs)


def create_param_parser(
    cls: type[ParamsBase], *, description: str | None
) -> ArgumentParser:
    param_parser = ArgumentParser(description=description)
    _add_param_parser_args(param_parser, cls)
    return param_parser


def _split_args(args: list[str]) -> tuple[list[str], list[str]]:
    try:
        idx = args.index("--")
        return args[0:idx], args[idx + 1 :]
    except ValueError:
        pass

    return args, []


def _flatten_params(params: list[str]) -> list[str]:
    ret = []
    for param in params:
        try:
            key, val = param.split("=")
            ret.append(key)
            ret.append(val)
        except ValueError:
            ret.append(param)

    return ret


def serialize_params(params: list[str]) -> str:
    parsed: dict[str, list[str]] = {}
    last_param_name = ""

    for param in _flatten_params(params):
        if param.startswith("--"):
            last_param_name = param[2:]
            if last_param_name not in parsed:
                parsed[last_param_name] = []
        elif last_param_name:
            parsed[last_param_name].append(param)
        else:
            raise RuntimeError()

    parts = []
    for k, v in parsed.items():
        if v:
            parts.append(f"{k}={','.join(v)}")
        else:
            parts.append(k)

    return "&".join(parts)


def validate_mod_name(mod_name: str) -> None:
    if " " in mod_name:
        raise ValueError("invalid module name; may not contain spaces")
    names = mod_name.split(".")
    if any([n.startswith("_") for n in names]):
        raise ValueError("invalid module name; may not import private modules")
    if "" in names:
        raise ValueError("invalid module name; invalid import")
    if any([not n.isidentifier() for n in names]):
        raise ValueError("invalid module name; invalid import")


def export(
    mod_name: str,
    mod: ModuleType,
    *,
    args: Namespace,
    params: Namespace,
    fname_suffix: str = "",
) -> None:
    fname = args.out

    if args.mkdirp:
        dir = os.path.dirname(fname)
        os.makedirs(dir, exist_ok=True)

    if os.path.isdir(fname):
        fname = os.path.join(fname, mod_name)

    export_fn = None
    ext = None
    if args.type == "3mf":
        # TODO: support params as metadata
        def export_3mf(
            to_export: Shape,
            file_path: os.PathLike | str | bytes,
        ) -> bool:
            mesher = Mesher()
            mesher.add_shape(to_export)
            mesher.write(file_path)
            return True

        export_fn = export_3mf
        ext = ".3mf"
    elif args.type == "step":
        export_fn = export_step
        ext = ".step"
    elif args.type == "stl":
        export_fn = export_stl
        ext = ".stl"
    else:
        raise ValueError(f"unsupported extension: {ext}")

    def output(result: Result, final_path: str) -> None:
        if os.path.exists(final_path) and not args.force:
            raise FileExistsError(f"{final_path} exists; use --force to overwrite")
        export_fn(result.part, final_path)
        print(f"[{datetime.datetime.now()}] generated: {final_path}")

    res = mod.main(params)
    if not res:
        raise ValueError("invalid generation: received empty list of results")
    elif isinstance(res, (list, tuple)):
        for idx, r in enumerate(res):
            if args.only and r.name not in args.only:
                continue
            if not isinstance(r, Result):
                raise ValueError("invalid generation: was not instance of ``Result``")
            name = r.name if r.name else str(idx)
            part_outfile = f"{fname}-{name}{fname_suffix}{ext}"
            output(r, part_outfile)
    elif isinstance(res, Result):
        part_outfile = f"{fname}{fname_suffix}{ext}"
        output(res, part_outfile)
    else:
        raise ValueError(
            f"invalid generation: received unexpected type {type(res)} from module"
        )


def view(
    mod_name: str,
    mod: ModuleType,
    *,
    args: Namespace,
    params: Namespace,
    fname_suffix=None,  # not used by view method, but included for parity with export
) -> None:
    from ocp_vscode import show

    res = mod.main(params)
    if not isinstance(res, (list, tuple)):
        res = [res]

    if not all([isinstance(r, Result) for r in res]):
        raise ValueError("invalid generation: not instance of ``Result``")

    show(
        *[r.locals for r in res],
        names=[r.name if r.name else idx for idx, r in enumerate(res)],
    )


def main():
    raw_args, raw_params = _split_args(sys.argv[1:])

    parser = ArgumentParser(description="Build a print module definition.")
    subparsers = parser.add_subparsers()
    parser.add_argument("module", nargs="+")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument(
        "-o", "--out", type=str, help="destination file", required=True
    )
    export_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="overwrite destination file, if it exists",
    )
    export_parser.add_argument(
        "-m",
        "--mkdirp",
        action="store_true",
        help="create destination path if it does not exist",
    )
    export_parser.add_argument(
        "-p",
        "--serialize-parameters",
        action=BooleanOptionalAction,
        default=True,
        help="serialize the overridden prarameters into the file name",
    )
    export_parser.add_argument(
        "--only",
        action="append",
        help="export the parts matching the given names only; ignored when only one part is returned",
    )
    export_parser.add_argument(
        "-t",
        "--type",
        default="3mf",
        choices=("3mf", "step", "stl"),
        help="export models as the given type; note this also etermines the output file extension",
    )
    export_parser.set_defaults(func=export)

    view_parser = subparsers.add_parser("view")
    view_parser.set_defaults(func=view)

    args = parser.parse_args(args=raw_args)

    mod_name = args.module[0]
    validate_mod_name(mod_name)
    mod = import_module(f".models.{mod_name}", "prints")
    check_module(mod)

    param_parser = create_param_parser(mod.Params, description=mod.__doc__)
    params = mod.Params()
    param_parser.parse_args(raw_params, namespace=params)

    fname_suffix = ""
    if s := serialize_params(raw_params):
        fname_suffix = f"-{s}"
    args.func(
        mod_name,
        mod,
        args=args,
        params=params,
        fname_suffix=fname_suffix,
    )


if __name__ == "__main__":
    main()

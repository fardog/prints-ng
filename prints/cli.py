#!/usr/bin/env python3
import datetime
import os
import sys
from types import ModuleType
from typing import List, Tuple
from argparse import ArgumentParser, Namespace
from importlib import import_module

from build123d import export_step, export_stl

from prints import Result


def split_args(args: List[str]) -> Tuple[List[str], List[str]]:
    try:
        idx = args.index("--")
        return args[0:idx], args[idx + 1 :]
    except ValueError:
        pass

    return args, []


def export(
    mod_name: str, mod: ModuleType, *, args: Namespace, params: Namespace
) -> None:
    outfile = args.out

    if args.mkdirp:
        dir = os.path.dirname(outfile)
        os.makedirs(dir, exist_ok=True)

    if os.path.exists(outfile) and not args.force:
        raise FileExistsError(f"{outfile} exists; use --force to overwrite")

    res = mod.main(params)
    if not isinstance(res, Result):
        raise ValueError("invalid generation: not instance of ``Result``")

    _, ext = os.path.splitext(outfile)
    if ext == ".step":
        export_step(res.part, outfile)
    elif ext == ".stl":
        export_stl(res.part, outfile)
    else:
        raise ValueError(f"unsupported extension: {ext}")

    print(f"[{datetime.datetime.now()}] generated: {outfile}")


def view(mod_name: str, mod: ModuleType, *, args: Namespace, params: Namespace) -> None:
    from ocp_vscode import show

    res = mod.main(params)
    if not isinstance(res, Result):
        raise ValueError("invalid generation: not instance of ``Result``")

    show(res.locals)


def main():
    from prints import check_module

    raw_args, raw_params = split_args(sys.argv[1:])

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
    export_parser.set_defaults(func=export)

    view_parser = subparsers.add_parser("view")
    view_parser.set_defaults(func=view)

    args = parser.parse_args(args=raw_args)

    mod_name = args.module[0]
    if mod_name.startswith("_"):
        raise ValueError("module name may not start with '_'")
    mod = import_module("prints.models.{}".format(mod_name))
    check_module(mod)

    param_parser = ArgumentParser(description=mod.__doc__)
    for k, v in mod.Params.__annotations__.items():
        kwargs = {
            "dest": k,
            "type": v,
            "default": getattr(mod.Params, k),
        }
        if v is bool:
            del kwargs["type"]
            param_parser.add_argument(
                "--no-{}".format(k), action="store_false", **kwargs
            )
            kwargs["action"] = "store_true"
        param_parser.add_argument("--{}".format(k), **kwargs)

    params = mod.Params()
    for k, v in param_parser.parse_args(raw_params).__dict__.items():
        if v is not None:
            setattr(params, k, v)

    args.func(mod_name, mod, args=args, params=params)


if __name__ == "__main__":
    main()

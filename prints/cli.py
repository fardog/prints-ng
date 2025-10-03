#!/usr/bin/env python3
import datetime
import os
import sys
from types import ModuleType
from typing import List, Tuple
from argparse import ArgumentParser, Namespace
from importlib import import_module

from build123d import export_step, export_stl

from prints import Result, create_param_parser


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

    fname, ext = os.path.splitext(outfile)
    export_fn = None
    if ext == ".step":
        export_fn = export_step
    elif ext == ".stl":
        export_fn = export_stl
    else:
        raise ValueError(f"unsupported extension: {ext}")

    res = mod.main(params)
    if not res:
        raise ValueError("invalid generation: received empty list of results")
    elif isinstance(res, (list, tuple)):
        for idx, r in enumerate(res):
            if not isinstance(r, Result):
                raise ValueError("invalid generation: was not instance of ``Result``")
            name = r.name if r.name else str(idx)
            part_outfile = f"{fname}-{name}{ext}"
            export_fn(r.part, part_outfile)
            print(f"[{datetime.datetime.now()}] generated: {part_outfile}")
    elif isinstance(res, Result):
        part_outfile = f"{fname}{ext}"
        export_fn(res.part, part_outfile)
        print(f"[{datetime.datetime.now()}] generated: {part_outfile}")
    else:
        raise ValueError(
            f"invalid generation: received unexpected type {type(res)} from module"
        )


def view(mod_name: str, mod: ModuleType, *, args: Namespace, params: Namespace) -> None:
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

    param_parser = create_param_parser(mod.Params, description=mod.__doc__)
    params = mod.Params()
    param_parser.parse_args(raw_params, namespace=params)

    args.func(mod_name, mod, args=args, params=params)


if __name__ == "__main__":
    main()

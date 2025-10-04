#!/usr/bin/env python3
import datetime
import os
import sys
from types import ModuleType
from argparse import ArgumentParser, BooleanOptionalAction, Namespace
from importlib import import_module

from build123d import export_step, export_stl

from prints import Result, create_param_parser


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


def _serialize_params(params: list[str]) -> str:
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

    export_fn = None
    ext = None
    if args.type == "step":
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
    from prints import check_module

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
        default="step",
        choices=("step", "stl"),
        help="export models as the given type; note this also etermines the output file extension",
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

    fname_suffix = ""
    if s := _serialize_params(raw_params):
        fname_suffix = f";{s}"
    args.func(
        mod_name,
        mod,
        args=args,
        params=params,
        fname_suffix=fname_suffix,
    )


if __name__ == "__main__":
    main()

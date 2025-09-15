# prints-ng

A collection of [build123d][] models, and a small project for altering their
parameters, on rails. This project is meant to replace my very similar project,
[prints][], which used OpenSCAD.

[build123d]: https://github.com/gumyr/build123d
[prints]: https://github.com/fardog/prints

> [!WARNING]
> I'm still learning build12d, don't expect high quality models here.

## Generating Models

Models are generated in either STEP or STL format, determined from the file
extension you pass to `--out`. The `model_name` refers to a module in the
`prints/models` directory.

It's expected to run the project with [uv][] for now.

[uv]: https://docs.astral.sh/uv/

```bash
uv run prints export --out <file_name> <model_name> -- [--param_override=value]
```

You can get a list of supported parameter overrides for a particular model by
using the `--help` parameter:

```bash
uv run prints export --out <file_name> <model_name> -- --help
```

## Module Format

A module must export the following:

1. A `Params` class, which includes Python 3 type annotations for each parameter
   and inherits `prints.ParamsBase`
1. A `main(params: Params)` function, which takes an instantiated `Prams` class
   and returns a `Result`

In `Result`, `locals` are provided to allow for easier debugging when viewing
with [ocp-vscode][]. It's recommended that you use unique names for any part,
sketch, or any other detail you'd like to see in the viewer, and just use
`locals()` for the `locals` parameter.

[ocp-vscode]: https://github.com/bernhard-42/vscode-ocp-cad-viewer

## Viewing

During development, you can run [ocp-vscode][] to inspect the model you are
building; despite the name, using Visual Studio Code is _not_ a requirement as
there is a standalone mode for the viewer. To view:

1. Run the [ocp-vscode][] viewer: `uv run python -m ocp_vscode`
1. Open the viewer in your browser at the given URL, e.g.
   `http://127.0.0.1:3939/viewer`
1. Run the `view` command for the model you wish to view

You can use a file watcher like `entr` to reload the model on saved changes:

```bash
ls prints/*.py | entr uv run main.py view <module_name> -- [--param_override=value]
```

## License

[Creative Commons Attribution-NonCommercial 4.0 International][cc]

[cc]: https://creativecommons.org/licenses/by-nc/4.0/

from build123d import *

from prints.params import ParamsBase, Result


class Params(ParamsBase):
    sphere_r = (2.25 / 2) * IN
    thickness = 2
    chamfer = 4


def main(params: Params) -> Result:
    sphere_r = params.sphere_r
    thickness = params.thickness

    box_width = sphere_r * 2 + thickness * 2
    box_height = sphere_r + thickness

    with BuildPart() as part:
        Box(
            length=box_width,
            width=box_width,
            height=box_height,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
        )
        Sphere(radius=sphere_r, mode=Mode.SUBTRACT)

        edges = part.edges().filter_by(Axis.Z)
        fillet(edges, radius=sphere_r / 2)
        bottomf = part.faces().sort_by(Axis.Z)[0]
        chamfer(bottomf.edges(), length=params.chamfer)

    assert part.part
    return Result(part=part.part, locals=locals())

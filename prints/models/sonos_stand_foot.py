from build123d import *

from prints import ParamsBase, Result


class Params(ParamsBase):
    leg_d: float = 18.50
    min_thickness: float = 3
    base_d: float = 35
    height: float = 30
    chamfer: float = 2


def main(params: Params) -> Result:
    leg_r = params.leg_d / 2
    upper_r = leg_r + params.min_thickness / 2
    lower_r = params.base_d / 2

    with BuildPart() as part:
        # base
        with BuildSketch() as base_sk:
            Circle(radius=lower_r)

        # upper
        with BuildSketch(
            Plane(origin=(0, 0, params.height), z_dir=(0, 0, 1))
        ) as upper_sk:
            Circle(radius=upper_r)

        loft()

        faces = part.faces().filter_by(Axis.Z)
        chamfer(faces[0].edges(), length=params.chamfer)
        fillet(faces[-1].edges(), radius=params.chamfer)

        # leg cutout
        with BuildSketch(
            Plane(origin=(0, 0, params.min_thickness), z_dir=(0, 0, 1))
        ) as leg_sk:
            Circle(radius=leg_r)
        extrude(amount=params.height, mode=Mode.SUBTRACT)

    assert part.part
    return Result(part=part.part, locals=locals())

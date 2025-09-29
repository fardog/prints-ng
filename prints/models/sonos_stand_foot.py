import build123d as b

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

    with b.BuildPart() as part:
        # base
        with b.BuildSketch() as base_sk:
            b.Circle(radius=lower_r)

        # upper
        with b.BuildSketch(
            b.Plane(origin=(0, 0, params.height), z_dir=(0, 0, 1))
        ) as upper_sk:
            b.Circle(radius=upper_r)

        b.loft()

        faces = part.faces().filter_by(b.Axis.Z)
        b.chamfer(faces[0].edges(), length=params.chamfer)
        b.fillet(faces[-1].edges(), radius=params.chamfer)

        # leg cutout
        with b.BuildSketch(
            b.Plane(origin=(0, 0, params.min_thickness), z_dir=(0, 0, 1))
        ) as leg_sk:
            b.Circle(radius=leg_r)
        b.extrude(amount=params.height, mode=b.Mode.SUBTRACT)

    assert part.part
    return Result(part=part.part, locals=locals())

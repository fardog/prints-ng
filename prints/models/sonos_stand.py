from build123d import *

from prints import ParamsBase, Result


class Params(ParamsBase):
    leg_d: float = 18.50
    screw_d: float = 4.0
    height: int = 25
    width: int = 120
    depth: int = 120
    thickness: int = 4
    fill: bool = True


def main(params: Params) -> Result:
    width = params.width - params.thickness * 2 - params.leg_d
    depth = params.depth - params.thickness * 2 - params.leg_d

    with BuildPart() as part:
        # base
        with BuildSketch():
            with GridLocations(width, depth, 2, 2):
                Circle(radius=params.leg_d / 2 + params.thickness)
            make_hull()

        extrude(amount=params.height)

        # holes
        with BuildSketch(part.faces().sort_by(Axis.Z).first) as holes:
            with GridLocations(width, depth, 2, 2):
                Circle(radius=params.leg_d / 2)

        extrude(amount=-params.height, mode=Mode.SUBTRACT)

        topf = part.faces().sort_by(Axis.Z).last
        offset(amount=-params.thickness, openings=topf)

        if params.fill:
            extrude(holes.sketch, amount=-params.thickness)

        x_faces = part.faces().sort_by(Axis.X)
        for f in (x_faces[0], x_faces[-1]):
            with Locations(f):
                with GridLocations(width - 0.1, params.height - 0.1, 2, 1):
                    CounterSinkHole(
                        radius=params.screw_d / 2,
                        counter_sink_radius=params.screw_d,
                        depth=params.leg_d,
                    )

    assert part.part
    return Result(part=part.part, locals=locals())

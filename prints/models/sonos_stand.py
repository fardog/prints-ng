import build123d as b

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

    with b.BuildPart() as part:
        # base
        with b.BuildSketch():
            with b.GridLocations(width, depth, 2, 2):
                b.Circle(radius=params.leg_d / 2 + params.thickness)
            b.make_hull()

        b.extrude(amount=params.height)

        # holes
        with b.BuildSketch(part.faces().sort_by(b.Axis.Z).first) as holes:
            with b.GridLocations(width, depth, 2, 2):
                b.Circle(radius=params.leg_d / 2)

        b.extrude(amount=-params.height, mode=b.Mode.SUBTRACT)

        topf = part.faces().sort_by(b.Axis.Z).last
        b.offset(amount=-params.thickness, openings=topf)

        if params.fill:
            b.extrude(holes.sketch, amount=-params.thickness)

        if not part.part:
            raise ValueError("no part")

        x_faces = part.faces().sort_by(b.Axis.X)
        for f in (x_faces[0], x_faces[-1]):
            with b.Locations(f):
                with b.GridLocations(width - 0.1, params.height - 0.1, 2, 1):
                    b.CounterSinkHole(
                        radius=params.screw_d / 2,
                        counter_sink_radius=params.screw_d,
                        depth=params.leg_d,
                    )

    return Result(part=part.part, locals=locals())

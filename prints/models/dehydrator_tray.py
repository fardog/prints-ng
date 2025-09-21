import build123d as b

from prints import ParamsBase, Result


class Params(ParamsBase):
    width: float = 280 / 2
    depth: float = 280 / 2
    height: float = 15
    thickness: float = 1.5
    grid_spacing: float = 2
    grid_num_x: int = 4
    grid_num_y: int = 5
    screw_d: float = 3.2
    inner_offset: float = 1.0
    inner: bool = True


def _inner(params: Params) -> Result:
    width = params.width - params.thickness * 2 - params.inner_offset
    depth = params.depth - params.thickness * 2 - params.inner_offset
    height = params.height - params.thickness

    with b.BuildPart() as part:
        with b.BuildSketch() as base_sk:
            b.Rectangle(width=width, height=depth)

        b.extrude(amount=height)

        topf = part.faces().sort_by(b.Axis.Z).last
        b.offset(amount=-params.thickness, openings=topf)

        exterior_faces = (
            part.faces().filter_by(b.Plane.YZ)[0:2]
            + part.faces().filter_by(b.Plane.XZ)[0:2]
        )

        basef = part.faces().sort_by(b.Axis.Z)[1]
        assert basef.length
        g_width = basef.length - params.thickness * 2
        assert basef.width
        g_depth = basef.width - params.thickness * 2

        with b.BuildSketch(basef) as cut_sk:
            b.Rectangle(width=g_width, height=g_depth)

        b.extrude(amount=-params.thickness, mode=b.Mode.SUBTRACT)

        for f in exterior_faces:
            with b.BuildSketch(f):
                b.Circle(radius=params.screw_d / 2)

            b.extrude(amount=-params.thickness, mode=b.Mode.SUBTRACT)

    assert part.part
    return Result(part=part.part, locals=locals())


def _outer(params: Params) -> Result:
    with b.BuildPart() as part:
        with b.BuildSketch() as base_sk:
            b.Rectangle(width=params.width, height=params.depth)
        b.extrude(amount=params.height)

        topf = part.faces().sort_by(b.Axis.Z).last
        b.offset(amount=-params.thickness, openings=topf)

        interior_faces = (
            part.faces().filter_by(b.Plane.YZ)[2:]
            + part.faces().filter_by(b.Plane.XZ)[2:]
        )

        basef = part.faces().sort_by(b.Axis.Z)[1]
        assert basef.length
        g_width = basef.length - params.thickness * 2
        assert basef.width
        g_depth = basef.width - params.thickness * 2

        rect_width = g_width / params.grid_num_x
        rect_depth = g_depth / params.grid_num_y

        with b.BuildSketch(basef) as grid_sk:
            with b.GridLocations(
                x_spacing=rect_width,
                x_count=params.grid_num_x,
                y_spacing=rect_depth,
                y_count=params.grid_num_y,
            ) as grid_locs:
                b.Rectangle(
                    width=rect_width - params.grid_spacing,
                    height=rect_depth - params.grid_spacing,
                )

        b.extrude(amount=-params.thickness, mode=b.Mode.SUBTRACT)

        for f in interior_faces:
            with b.BuildSketch(f):
                b.Circle(radius=params.screw_d / 2)

            b.extrude(amount=-params.thickness, mode=b.Mode.SUBTRACT)

    assert part.part
    return Result(part=part.part, locals=locals())


def main(params: Params) -> Result:
    if params.inner:
        return _inner(params)

    return _outer(params)

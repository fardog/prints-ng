from build123d import *

from prints import ParamsBase, Result


class Params(ParamsBase):
    width: float = 21.05 * CM
    height: float = 12 * CM
    corner_width: float = 6 * CM
    corner_height: float = 4 * CM
    depth: float = 6 * CM
    tab_width: float = 12
    tab_height: float = 25
    tab_thickness: float = 7
    thickness: float = 3
    top_chamfer: float = 10
    corner_r: float = 10
    hole_r: float = 4
    screw_d: float = 4
    switch: bool = True
    switch_r: float = 12.5 / 2


def main(params: Params) -> Result:
    width = params.width
    height = params.height
    corner_width = params.corner_width
    corner_height = params.corner_height

    with BuildPart() as part:
        with BuildSketch() as sk:
            with BuildLine():
                # bottom-left, going clockwise
                points = (
                    (0, 0),
                    (0, height),
                    (width - corner_width, height),
                    (width, height - corner_height),
                    (width, 0),
                    (0, 0),
                )
                Polyline(points)
            make_face()
        extrude(amount=params.depth)

        topf = part.faces().sort_by(Axis.Z)[-1]
        chamfer(topf.edges(), length=params.top_chamfer)
        edges = part.edges().filter_by(Axis.Z)
        fillet(edges, radius=params.corner_r)
        bottomf = part.faces().sort_by(Axis.Z)[0]
        offset(openings=bottomf, amount=-params.thickness)

        topf = part.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(Plane(topf)):
            with HexLocations(radius=params.hole_r * 2, x_count=10, y_count=4):
                RegularPolygon(radius=params.hole_r, side_count=6)
        extrude(amount=-params.thickness, mode=Mode.SUBTRACT)

        # left tab
        with BuildSketch() as left_tab_sk:
            with Locations((0, params.height / 2 + params.tab_height / 2)):
                Rectangle(
                    params.tab_width, params.tab_height, align=(Align.MAX, Align.CENTER)
                )
        extrude(amount=params.tab_thickness)
        frontf = part.faces(Select.LAST).filter_by(Axis.Y).sort_by(Axis.Y)[0]
        frontf_vertex = frontf.vertices().sort_by(Axis.Z)[2:].sort_by(Axis.X)[0]
        with BuildSketch(Plane(frontf).shift_origin(frontf_vertex)) as support_sk:
            Triangle(a=params.tab_width, b=params.tab_width, C=90, align=Align.MIN)
        extrude(amount=-params.tab_thickness)
        with BuildSketch(
            Plane(frontf).shift_origin(frontf_vertex).offset(-params.tab_height)
        ) as support_sk:
            Triangle(a=params.tab_width, b=params.tab_width, C=90, align=Align.MIN)
        extrude(amount=params.tab_thickness)

        topf = part.faces(Select.LAST).filter_by(Axis.Z).sort_by(Axis.Z)[-1]
        with BuildSketch(Plane(topf)):
            Rectangle(params.screw_d, params.tab_height - params.tab_thickness * 2)
        extrude(amount=-params.tab_thickness, mode=Mode.SUBTRACT)

        # right tab
        with BuildSketch() as right_tab_sk:
            with Locations((params.width, params.height / 2)):
                Rectangle(
                    params.tab_width, params.tab_height, align=(Align.MIN, Align.CENTER)
                )
        extrude(amount=params.tab_thickness)

        frontf = part.faces(Select.LAST).filter_by(Axis.Y).sort_by(Axis.Y)[0]
        frontf_vertex = frontf.vertices().sort_by(Axis.Z)[2:].sort_by(Axis.X)[0]
        with BuildSketch(Plane(frontf).shift_origin(frontf_vertex)) as support_sk:
            Triangle(a=params.tab_width, c=params.tab_width, B=90, align=Align.MIN)
        extrude(amount=-params.tab_thickness)

        with BuildSketch(
            Plane(frontf).shift_origin(frontf_vertex).offset(-params.tab_height)
        ) as support_sk:
            Triangle(a=params.tab_width, c=params.tab_width, B=90, align=Align.MIN)
        extrude(amount=params.tab_thickness)

        topf = part.faces(Select.LAST).filter_by(Axis.Z).sort_by(Axis.Z)[-1]
        with BuildSketch(Plane(topf)):
            Rectangle(params.screw_d, params.tab_height - params.tab_thickness * 2)
        extrude(amount=-params.tab_thickness, mode=Mode.SUBTRACT)

        if params.switch:
            leftf = part.faces().filter_by(Axis.X).sort_by(Axis.X)[-4]
            assert leftf.width
            with BuildSketch(Plane(leftf)):
                with Locations((leftf.width / 4, 0)):
                    Circle(radius=params.switch_r)
            extrude(amount=-params.thickness, mode=Mode.SUBTRACT)

    assert part.part
    return Result(name="housing", part=part.part, locals=locals())

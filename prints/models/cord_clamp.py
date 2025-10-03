from build123d import *

from prints import ParamsBase, Result


class Params(ParamsBase):
    thickness: float = 5
    min_thickness: float = 1
    cable_d: float = 8
    cutout_width: float = 6.5

    screw_d: float = 3
    screw_head_d: float = 6
    screw_head_height: float = 3
    screw_spacing: float = 0.5
    screw_nut_d: float = 6
    screw_nut_spacing: float = 0.5
    screw_nut_height: float = 3

    inset: bool = True
    inset_d: float = 10
    inset_thickness: float = 1


def main(params: Params) -> Result:
    total_width = params.thickness * 2 + params.cutout_width
    bottom = params.cable_d / 2 + params.screw_head_d + params.min_thickness * 2
    side = total_width / 2

    total_thickness = params.screw_head_d + params.min_thickness * 2

    screw_hole_d = params.screw_d + params.screw_spacing
    screw_nut_d = params.screw_nut_d + params.screw_nut_spacing

    points = [
        (-side, -bottom),  # bottom left
        (-side, 0),  # top left
        (side, 0),  # top right
        (side, -bottom),  # bottom right
    ]
    with BuildPart() as part:
        with BuildSketch() as sk:
            with BuildLine() as line:
                Line(points[:2])
                CenterArc(
                    (0, 0),
                    radius=total_width / 2,
                    start_angle=0,
                    arc_size=180,
                )
                Line(points[2:])
                Line([points[-1], points[0]])
            make_face()
            Circle(radius=params.cable_d / 2, mode=Mode.SUBTRACT)
            Rectangle(
                width=params.cutout_width,
                height=bottom,
                align=(Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )
        extrude(amount=total_thickness)

        left_f, right_f = (
            part.faces()
            .filter_by(GeomType.PLANE)
            .filter_by(Plane.YZ)
            .sort_by(Axis.X)[1:3]
        )

        right_plane = Plane(right_f).offset(total_width / 2 + params.cutout_width / 2)
        with Locations(right_plane):
            CounterBoreHole(
                radius=screw_hole_d / 2,
                counter_bore_radius=params.screw_head_d / 2,
                counter_bore_depth=params.screw_head_height,
            )

        left_plane = Plane(left_f).offset(total_width / 2 + params.cutout_width / 2)
        with BuildSketch(left_plane) as nut_sk:
            RegularPolygon(radius=screw_nut_d / 2, side_count=6)
        extrude(amount=-params.screw_nut_height, mode=Mode.SUBTRACT)

        if params.inset:
            assert sk.sketch.location
            with BuildSketch(sk.sketch.location):
                Circle(radius=params.inset_d / 2)
            extrude(amount=params.inset_thickness, mode=Mode.SUBTRACT)

    assert part.part
    return Result(part=part.part, locals=locals())

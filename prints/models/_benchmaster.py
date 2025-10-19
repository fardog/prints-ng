from build123d import *

from prints.params import ParamsBase


class LouvreParams(ParamsBase):
    slot_width: float = 5.3 * CM
    slot_height: float = 12
    slot_depth: float = 4
    total_height: float = 2.5 * CM
    metal_thickness: float = 1.5
    min_thickness: float = 3


def louvre_blank(params: LouvreParams) -> Part:
    width = params.slot_width + params.min_thickness * 2 + params.slot_depth * 2
    height = params.total_height
    depth = params.slot_depth + params.metal_thickness + params.min_thickness

    with BuildPart() as part:
        with BuildSketch():
            Rectangle(width=width, height=depth)
        extrude(amount=height)

        faces = part.faces().filter_by(Plane.XY).sort_by(Axis.Z)
        topf = faces[-1]
        edge = topf.edges().filter_by(Axis.X).sort_by(Axis.Y)[0]
        plane = Plane(topf).shift_origin(edge.center())
        with BuildSketch(plane):
            with Locations((0, params.slot_depth)):
                Rectangle(
                    params.slot_width,
                    params.metal_thickness,
                    align=(Align.CENTER, Align.MIN),
                )
        extrude(amount=-height, mode=Mode.SUBTRACT)

        with BuildSketch(plane.offset(-params.slot_height)):
            Trapezoid(
                params.slot_width + params.slot_depth * 2 + params.metal_thickness * 2,
                params.slot_depth + params.metal_thickness,
                45,
                45,
                align=(Align.CENTER, Align.MIN),
            )
        extrude(amount=-height, mode=Mode.SUBTRACT)

    assert part.part
    return part.part

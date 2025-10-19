# A roll/spool holder for mounting to a louvred tool panel
from build123d import *

from prints.params import ParamsBase, Result

from ._benchmaster import LouvreParams, louvre_blank


class Params(ParamsBase):
    louvre: LouvreParams = LouvreParams()
    dowel_r: float = 16 / 2
    dowel_spacing: float = 0.3
    cap_dowel: bool = False
    mirror: bool = False
    spool_r: float = 5 * CM
    spool_offset: float = 1 * CM
    min_thickness: float = 2
    bracket_width: float = 2 * CM


def main(params: Params) -> Result:
    backing = louvre_blank(params.louvre)
    dowel_total_r = params.dowel_r + params.dowel_spacing

    with BuildPart() as part:
        add(backing)

        face = backing.faces().filter_by(Plane.YZ).sort_by(Axis.X)[0]
        vertex = face.vertices().sort_by(Axis.Z)[2:].sort_by(Axis.Y)[-1]
        plane = Plane(face).shift_origin(vertex - (0, params.louvre.min_thickness, 0))
        with BuildSketch(plane) as sk:
            length = params.spool_r + params.spool_offset
            depth = dowel_total_r * 2 + params.min_thickness * 2
            with BuildLine():
                Polyline(
                    (
                        (0, 0),
                        (length, 0),
                        (length, depth),
                        (0, params.louvre.total_height),
                        (0, 0),
                    )
                )
            face = make_face()
            outer = face.vertices().sort_by(Axis.X)[-2:]
            fillet(outer, radius=depth / 2)
            dowel_center = (
                sk.edges(Select.LAST)
                .filter_by(GeomType.CIRCLE)
                .sort_by(Axis.Y)[0]
                .arc_center
            )
            offset(amount=-params.min_thickness, mode=Mode.SUBTRACT)
            with Locations(dowel_center):
                Circle(radius=depth / 2)
                Circle(radius=dowel_total_r, mode=Mode.SUBTRACT)
        extrude(amount=-params.bracket_width)

        if params.cap_dowel:
            with BuildSketch(plane) as fill_sk:
                with Locations(dowel_center):
                    Circle(radius=dowel_total_r)
            extrude(amount=-params.min_thickness)

        if params.mirror:
            mirror(about=Plane.ZY, mode=Mode.REPLACE)

    assert part.part
    return Result(part=part.part, locals=locals())

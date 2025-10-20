# A printable dowel for the roll/spool holder if you don't have one around
from build123d import *

from prints.params import Result

from .roll_spool_holder import Params as WireSpoolBaseParams


class Params(WireSpoolBaseParams):
    dowel_length: float = 21.9 * CM
    insert_end_offset: float = 3
    screw_r: float = 3 / 2


def main(params: Params) -> Result:
    total_length = params.dowel_length
    if params.cap_dowel:
        # subtract min thickness to accout for cap end, if enabled
        total_length = total_length - params.min_thickness

    with BuildPart() as part:
        Cylinder(radius=params.dowel_r, height=total_length)

        topf = part.faces().sort_by(Axis.Z)[-1]
        offset_amount = params.bracket_width + params.insert_end_offset
        with Locations(Plane(topf).offset(-offset_amount).rotated((90, 0, 0))):
            Hole(radius=params.screw_r)

    assert part.part
    return Result(part=part.part, locals=locals())

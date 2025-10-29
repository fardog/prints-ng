"""
A telescoping box, defined by its interior dimensions when the top and bottom
are closed.

By default:
    - The top will be sized to fully enclose the bottom when closed, you may
      adjust this fit with ``top_bottom_offset`` to shorten the top, and
      ``bottom_top_offset`` to shorten the bottom.
    - The bottom interior edge will have a fillet to avoid a hard transition
      between the bottom face and walls, but the top will not to allow the lid
      to fit fully. You may add a top fillet by setting ``top_interior_fillet``
      to ``True``.
    - The top and bottom will have a 0.3mm gap to allow the halves to fit
      together. You may adjust this with the ``fit`` parameter if necessary.

Any fillets may be disabled by setting their radius to ``0``.
"""

from typing import Any
from build123d import *

from prints.params import ParamsBase, Result


class Params(ParamsBase):
    interior_width: float = 50
    interior_depth: float = 20
    interior_height: float = 40
    interior_fillet_r: float = 2
    top_interior_fillet: bool = False
    corner_fillet_r: float = 2
    thickness: float = 0.75
    fit: float = 0.3
    top_bottom_offset: float = 0
    bottom_top_offset: float = 0
    cutout_r: float = 7


def _build_body(
    *,
    width: float,
    depth: float,
    height: float,
    corner_fillet_r: float,
    interior_fillet_r: float,
    thickness: float,
    cutout_r: float,
) -> tuple[Part, Any]:
    total_height = height + thickness
    with BuildPart() as part:
        with BuildSketch() as sk:
            face = Rectangle(width, depth)
            if corner_fillet_r > 0:
                face = fillet(face.vertices(), radius=corner_fillet_r)
            outer = offset(face, amount=thickness)
        extrude(face, amount=thickness)
        wall = outer - face
        extrude(wall, amount=total_height)

        if interior_fillet_r > 0:
            inner_f = part.faces().filter_by(Plane.XY).sort_by(Axis.Z)[1]
            fillet(inner_f.edges(), radius=interior_fillet_r)

        if cutout_r > 0:
            outer_f = part.faces().filter_by(Plane.XZ).sort_by(Axis.Y)[0]
            with BuildSketch(Plane(outer_f)) as cutout_sk:
                with Locations((0, total_height / 2)):
                    Circle(radius=cutout_r)
            extrude(cutout_sk.sketch, amount=-depth * 2, mode=Mode.SUBTRACT)

    assert part.part
    return part.part, locals()


def main(params: Params) -> list[Result]:
    thickness = params.thickness
    interior_fillet_r = params.interior_fillet_r

    bottom_width = params.interior_width
    bottom_depth = params.interior_depth
    bottom_height = params.interior_height - params.bottom_top_offset
    bottom_corner_fillet_r = params.corner_fillet_r

    def calc_top(dim: float) -> float:
        return dim + thickness * 2 + params.fit

    top_width = calc_top(bottom_width)
    top_depth = calc_top(bottom_depth)
    top_height = (
        params.interior_height + thickness + params.fit - params.top_bottom_offset
    )
    # since the additions need to act on the diameter, temporarily deal in that
    top_corner_fillet_r = calc_top(bottom_corner_fillet_r * 2) / 2
    top_interior_fillet_r = interior_fillet_r if params.top_interior_fillet else 0
    if top_interior_fillet_r:
        # we need to adjust the height if the top has a fillet, since the cases
        # won't close. the goal is to keep the interior space the same, so we'll
        # adjust the bottom height
        bottom_height -= top_interior_fillet_r

    bottom, b_locals = _build_body(
        width=bottom_width,
        depth=bottom_depth,
        height=bottom_height,
        corner_fillet_r=bottom_corner_fillet_r,
        interior_fillet_r=interior_fillet_r,
        thickness=thickness,
        cutout_r=0,
    )

    top, t_locals = _build_body(
        width=top_width,
        depth=top_depth,
        height=top_height,
        corner_fillet_r=top_corner_fillet_r,
        interior_fillet_r=top_interior_fillet_r,
        thickness=thickness,
        cutout_r=params.cutout_r,
    )

    return [
        Result(name="top", part=top, locals=t_locals),
        Result(name="bottom", part=bottom, locals=b_locals),
    ]

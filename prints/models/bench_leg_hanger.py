from build123d import *

from prints import ParamsBase, Result


class Params(ParamsBase):
    dowel_d: float = 18.5
    post_width: float = 39
    post_depth: float = 39
    spool_clearance: int = 100
    thickness: int = 6


def main(params: Params) -> Result:
    part_thickness = params.thickness * 2 + params.post_width
    with BuildPart() as part:
        with BuildSketch() as sk:
            Rectangle(
                params.dowel_d + params.thickness,
                params.dowel_d + params.thickness,
                align=(Align.MIN, Align.MIN),
            )
            with Locations((-params.spool_clearance, 0)):
                Rectangle(
                    params.post_width + params.thickness * 3,
                    params.post_width,
                    align=(Align.MAX, Align.MIN),
                )
            make_hull()
        extrude(sk.sketch, amount=part_thickness)

        # dowel cutout; this goes on the upper face as far to the top right as it can
        face = part.faces().sort_by(Axis.Z).last
        vertex = face.vertices()[1]
        with Locations(vertex - (params.thickness, 0, 0)):
            Cylinder(
                params.dowel_d / 2,
                params.post_width,
                align=(Align.MAX, Align.MAX, Align.MAX),
                mode=Mode.SUBTRACT,
            )
            Box(
                params.dowel_d,
                params.dowel_d,
                params.post_width,
                mode=Mode.SUBTRACT,
                align=(Align.MAX, Align.CENTER, Align.MAX),
            )

        # front angle cut
        face = part.faces().sort_by(Axis.Y).first
        assert face.width
        assert face.length
        with BuildSketch(face) as sk:
            pts = (
                (0, face.width / 2),
                (face.length / 2, face.width / 2),
                (face.length / 2, 0),
            )
            with BuildLine():
                Polyline(pts, close=True)
            make_face()
        extrude(sk.sketch, amount=-part_thickness, mode=Mode.SUBTRACT)

        # post slot
        with BuildSketch(part.faces().sort_by(Axis.Y).last) as sk:
            Rectangle(params.post_width, params.post_depth)
        extrude(sk.sketch, amount=-params.post_width, mode=Mode.SUBTRACT)

        # post insert cutout; we're putting this on the face of the post slot,
        # second Z-axis from the bottom
        face = part.faces().sort_by(Axis.Z)[1]
        assert face.width
        assert face.length
        with BuildSketch(face) as sk:
            with Locations((-face.length / 2 - params.thickness, -face.width / 2)):
                Rectangle(
                    params.post_width,
                    params.post_depth * 2,
                    rotation=-30,
                    align=(Align.MIN, Align.MIN),
                )
        extrude(
            sk.sketch,
            amount=params.post_depth + params.thickness * 2,
            mode=Mode.SUBTRACT,
        )

    assert part.part
    return Result(part=part.part, locals=locals())

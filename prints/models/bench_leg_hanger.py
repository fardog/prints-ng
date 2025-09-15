import build123d as b

from prints import ParamsBase, Result


class Params(ParamsBase):
    dowel_d: float = 18.5
    post_width: float = 39
    post_depth: float = 39
    spool_clearance: int = 100
    thickness: int = 6


def main(params: Params) -> Result:
    part_thickness = params.thickness * 2 + params.post_width
    with b.BuildPart() as part:
        with b.BuildSketch() as sk:
            b.Rectangle(
                params.dowel_d + params.thickness,
                params.dowel_d + params.thickness,
                align=(b.Align.MIN, b.Align.MIN),
            )
            with b.Locations((-params.spool_clearance, 0)):
                b.Rectangle(
                    params.post_width + params.thickness * 3,
                    params.post_width,
                    align=(b.Align.MAX, b.Align.MIN),
                )
            b.make_hull()
        b.extrude(sk.sketch, amount=part_thickness)

        # dowel cutout; this goes on the upper face as far to the top right as it can
        face = part.faces().sort_by(b.Axis.Z).last
        vertex = face.vertices()[1]
        with b.Locations(vertex - (params.thickness, 0, 0)):
            b.Cylinder(
                params.dowel_d / 2,
                params.post_width,
                align=(b.Align.MAX, b.Align.MAX, b.Align.MAX),
                mode=b.Mode.SUBTRACT,
            )
            b.Box(
                params.dowel_d,
                params.dowel_d,
                params.post_width,
                mode=b.Mode.SUBTRACT,
                align=(b.Align.MAX, b.Align.CENTER, b.Align.MAX),
            )

        # front angle cut
        face = part.faces().sort_by(b.Axis.Y).first
        with b.BuildSketch(face) as sk:
            pts = (
                (0, face.width / 2),
                (face.length / 2, face.width / 2),
                (face.length / 2, 0),
            )
            with b.BuildLine():
                b.Polyline(pts, close=True)
            b.make_face()
        b.extrude(sk.sketch, amount=-part_thickness, mode=b.Mode.SUBTRACT)

        # post slot
        with b.BuildSketch(part.faces().sort_by(b.Axis.Y).last) as sk:
            b.Rectangle(params.post_width, params.post_depth)
        b.extrude(sk.sketch, amount=-params.post_width, mode=b.Mode.SUBTRACT)

        # post insert cutout; we're putting this on the face of the post slot,
        # second Z-axis from the bottom
        face = part.faces().sort_by(b.Axis.Z)[1]
        with b.BuildSketch(face) as sk:
            with b.Locations((-face.length / 2 - params.thickness, -face.width / 2)):
                b.Rectangle(
                    params.post_width,
                    params.post_depth * 2,
                    rotation=-30,
                    align=(b.Align.MIN, b.Align.MIN),
                )
        b.extrude(
            sk.sketch,
            amount=params.post_depth + params.thickness * 2,
            mode=b.Mode.SUBTRACT,
        )

    return Result(part=part.part, locals=locals())

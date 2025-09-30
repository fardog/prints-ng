"""LED Ring"""

from build123d import *

from prints import ParamsBase, Result
from prints.constants import M3X5_7_INSERT

# from published specs, the philips TL-E 32W bulb is between 236.5mm and 246.1mm
# inner diameter, and the tube has a diameter between 26.2mm and 30.9 mm; we'll
# average them to get some sensible dimensions
TLE_BULB_D = (26.2 + 30.9) / 2
TLE_BULB_INNER_D = (236.5 + 246.1) / 2
TLE_BULB_CENTER_D = TLE_BULB_INNER_D + TLE_BULB_D / 2


class DriverParams(ParamsBase):
    width: float = 46
    length: float = 95
    mount: float = 140
    mount_overhang_x: float = 5
    mount_overhang_y: float = 0.5
    plate_thickness: float = 6
    plate_min_thickness: float = 1.5
    screw_d: float = 4
    screw_spacing: float = 0.5


class ShroudPlateParams(ParamsBase):
    d: float = 330
    width_upper: float = 98
    width_lower: float = 90
    height: float = 53
    thickness: float = 2
    fillet: float = 10
    screw_offset: float = -2.5
    screw_separation: float = 85
    screw_d: float = 5.5


class BracketParams(ParamsBase):
    bulb_d: float = TLE_BULB_D
    bulb_padding: float = 2
    rad: float = 290
    width: float = 13
    thickness: float = 4
    lip: float = 3


class RingParams(ParamsBase):
    peg_w: float = 5
    peg_spacing: float = 0.3
    peg_rad: float = 5
    center_d: float = 275
    width: float = 10
    led_offset: float = 4
    height: float = 8
    segments: int = 3


class _Shared(ParamsBase):
    screw_d: float = 3
    screw_head_d: float = 6
    screw_spacing: float = 0.5


class Params(_Shared):
    ring: RingParams = RingParams()
    bracket: BracketParams = BracketParams()
    driver: DriverParams = DriverParams()
    shroud: ShroudPlateParams = ShroudPlateParams()


def _shroud_plate(params: ShroudPlateParams) -> Result:
    width_upper = params.width_upper
    width_lower = params.width_lower
    height = params.height
    points = [
        (-width_lower / 2, -height / 2),  # bottom left
        (-width_upper / 2, height / 2),  # top left
        (width_upper / 2, height / 2),  # top right
        (width_lower / 2, -height / 2),  # bottom right
    ]
    with BuildPart() as part:
        with BuildSketch() as part_sk:
            with BuildLine() as line:
                Line(points[:2])
                RadiusArc(
                    start_point=points[1],
                    end_point=points[2],
                    radius=(params.d + height) / 2,
                )
                Line(points[2:])
                RadiusArc(
                    start_point=points[0],
                    end_point=points[-1],
                    radius=params.d / 2,
                )
            make_face()

            with Locations((0, params.screw_offset)):
                with GridLocations(params.screw_separation, 0, 2, 1):
                    Circle(radius=params.screw_d / 2, mode=Mode.SUBTRACT)

        extrude(amount=params.thickness)

        edges = [e for e in part.edges().filter_by(Axis.Z) if e.center().Y > 0]

        fillet(edges, radius=params.fillet)

    assert part.part
    return Result(name="shroud_plate", part=part.part, locals=locals())


def _driver_plate(shared: _Shared, params: DriverParams) -> Result:
    total_width = params.width + params.mount_overhang_y * 2
    total_length = params.mount + params.mount_overhang_x * 2
    screw_hole_d = shared.screw_d + shared.screw_spacing
    driver_screw_hole_d = params.screw_d + params.screw_spacing
    with BuildPart() as plate:
        Box(length=total_length, width=total_width, height=params.plate_thickness)

        edges = plate.edges().filter_by(Axis.Z)

        fillet(edges, radius=params.mount_overhang_x)
        topf = plate.faces().sort_by(Axis.Z).last
        chamfer(topf.edges(), length=2)

        topf = plate.faces().sort_by(Axis.Z).last
        with Locations(topf):
            with GridLocations(
                params.length - screw_hole_d * 2,
                params.width - screw_hole_d * 2,
                2,
                2,
            ) as screw_locs:
                CounterBoreHole(
                    radius=screw_hole_d / 2,
                    counter_bore_radius=shared.screw_head_d / 2,
                    counter_bore_depth=params.plate_thickness
                    - params.plate_min_thickness,
                )

            with GridLocations(params.mount, 0, 2, 1) as driver_screw_locs:
                Hole(radius=driver_screw_hole_d / 2)

    assert plate.part
    return Result(name="driver_plate", part=plate.part, locals=locals())


def _ring(shared: _Shared, params: RingParams) -> Result:
    center_d = params.center_d
    ring_thickness = params.width
    ring_height = params.height
    inner_d = center_d - ring_thickness
    outer_d = center_d + ring_thickness
    screw_opening = shared.screw_d + shared.screw_spacing

    arc_size = 360 / params.segments

    with BuildPart() as ring:
        with BuildSketch() as ring_sk:
            with BuildLine() as ring_outline:
                outer_arc = CenterArc(
                    (0, 0),
                    radius=outer_d / 2,
                    start_angle=0,
                    arc_size=arc_size,
                )
                inner_arc = CenterArc(
                    (0, 0),
                    radius=inner_d / 2,
                    start_angle=0,
                    arc_size=arc_size,
                )
                Line(outer_arc @ 0, inner_arc @ 0)
                Line(outer_arc @ 1, inner_arc @ 1)
            make_face()

            with BuildLine() as peg_male:
                peg_inner_d = center_d - params.peg_w + params.peg_spacing / 2
                peg_outer_d = center_d + params.peg_w - params.peg_spacing / 2
                peg_outer_arc = CenterArc(
                    (0, 0),
                    radius=peg_outer_d / 2,
                    start_angle=-params.peg_rad,
                    arc_size=params.peg_rad,
                )
                peg_inner_arc = CenterArc(
                    (0, 0),
                    radius=peg_inner_d / 2,
                    start_angle=-params.peg_rad,
                    arc_size=params.peg_rad,
                )
                Line(peg_outer_arc @ 0, peg_inner_arc @ 0)
                Line(peg_outer_arc @ 1, peg_inner_arc @ 1)
            make_face()

            with BuildLine() as peg_female:
                peg_inner_d = center_d - params.peg_w
                peg_outer_d = center_d + params.peg_w
                peg_outer_arc = CenterArc(
                    (0, 0),
                    radius=peg_outer_d / 2,
                    start_angle=arc_size - params.peg_rad,
                    arc_size=params.peg_rad,
                )
                peg_inner_arc = CenterArc(
                    (0, 0),
                    radius=peg_inner_d / 2,
                    start_angle=arc_size - params.peg_rad,
                    arc_size=params.peg_rad,
                )
                Line(peg_outer_arc @ 0, peg_inner_arc @ 0)
                Line(peg_outer_arc @ 1, peg_inner_arc @ 1)
            make_face(mode=Mode.SUBTRACT)

            with BuildLine(mode=Mode.PRIVATE) as slot:
                slot_width = 360 / 12
                CenterArc(
                    (0, 0),
                    radius=center_d / 2,
                    start_angle=360 / (params.segments * 2) - slot_width / 2,
                    arc_size=360 / (params.segments * 4),
                )
            SlotArc(
                arc=slot.edges()[0],
                height=screw_opening,
                rotation=0,
                mode=Mode.SUBTRACT,
            )

        extrude(amount=ring_height)

    assert ring.part
    return Result(name="ring", part=ring.part, locals=locals())


def _bracket(ring: RingParams, params: BracketParams) -> Result:
    bracket_d = params.bulb_d + params.bulb_padding
    bracket_total_height = params.width + params.thickness * 2
    bracket_total_d = bracket_d + params.lip * 2

    with BuildPart() as bracket:
        with BuildSketch() as bracket_sk:
            with BuildLine() as bracket_outline:
                arc = CenterArc(
                    (0, 0),
                    radius=bracket_total_d / 2,
                    start_angle=360 - params.rad / 2,
                    arc_size=params.rad,
                )
                Line(arc @ 0, arc @ 1)
            make_face()
        extrude(amount=bracket_total_height)

        assert bracket.part

        # bracket groove
        with BuildSketch(
            Plane(origin=bracket.part.center(), z_dir=(-1, 0, 0))
        ) as lip_sk:
            with Locations((0, bracket_total_d / 2)):
                Polygon(
                    (0, 0),
                    (-params.lip, params.lip),
                    (params.width, params.lip),
                    (params.width, 0),
                    align=(Align.CENTER, Align.MAX),
                )
        revolve(lip_sk.sketch.face(), axis=Axis.Z, mode=Mode.SUBTRACT)

        plane = Plane(origin=bracket.part.center(), z_dir=(-1, 0, 0))
        # LED track
        with BuildSketch(plane) as cutout_sk:
            Rectangle(bracket_total_height + 1, ring.width + ring.led_offset * 2)
        extrude(amount=bracket_total_d, mode=Mode.SUBTRACT)

        # insert
        with BuildSketch(plane) as insert_sk:
            Circle(radius=M3X5_7_INSERT.diameter / 2)
        extrude(amount=-M3X5_7_INSERT.depth, mode=Mode.SUBTRACT)

    return Result(name="bracket", part=bracket.part, locals=locals())


def main(params: Params) -> list[Result]:
    return [
        _ring(params, params.ring),
        _bracket(params.ring, params.bracket),
        _driver_plate(params, params.driver),
        _shroud_plate(params.shroud),
    ]

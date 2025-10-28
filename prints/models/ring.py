from build123d import *

from prints import ParamsBase, Result


class Params(ParamsBase):
    outer_r: float = 3 * CM
    thickness: float = 2.7
    height: float = 2.5


def main(params: Params) -> Result:
    outer_r = params.outer_r
    inner_r = outer_r - params.thickness
    height = params.height
    with BuildPart() as part:
        Cylinder(radius=outer_r, height=height)
        Cylinder(radius=inner_r, height=height, mode=Mode.SUBTRACT)

    assert part.part
    return Result(part=part.part, locals=locals())

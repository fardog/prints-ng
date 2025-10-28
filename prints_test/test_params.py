from unittest import TestCase

from prints.params import ParamsBase


class TestParamsBase(TestCase):
    def test_dict(self) -> None:
        class Params(ParamsBase):
            a: int = 1
            b: float = 2.0

        expected = {
            "a": 1,
            "b": 2.0,
        }

        assert Params()._dict() == expected

    def test_annotations(self) -> None:
        class SubParams(ParamsBase):
            c: bool = True

        class Params(ParamsBase):
            a: int = 1
            b: float = 2.0
            c: SubParams = SubParams()

        expected = {
            "a": int,
            "b": float,
            "c": SubParams,
        }

        assert dict(Params()._annotations()) == expected

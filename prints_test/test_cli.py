from unittest import TestCase

import pytest
from prints.cli import create_param_parser, serialize_params, validate_mod_name
from prints.params import ParamsBase


class TestParamParser(TestCase):
    def test_param_parser_primitives_defaults(self):
        class Params(ParamsBase):
            int_p: int = 10
            float_p: float = 1.1
            bool_p: bool = False

        params = Params()
        parser = create_param_parser(Params, description=None)
        parser.parse_args([], namespace=params)

        assert params.int_p == 10
        assert params.float_p == 1.1
        assert not params.bool_p

    def test_param_parser_primitives_overrides(self):
        class Params(ParamsBase):
            int_p: int = 10
            float_p: float = 1.1
            bool_p: bool = False

        params = Params()
        parser = create_param_parser(Params, description=None)
        parser.parse_args(
            ["--int_p", "11", "--float_p", "2.2", "--bool_p"], namespace=params
        )

        assert params.int_p == 11
        assert params.float_p == 2.2
        assert params.bool_p

    def test_param_parser_bool_inversion(self):
        class Params(ParamsBase):
            bool_p: bool = True

        params = Params()
        parser = create_param_parser(Params, description=None)
        parser.parse_args(["--no-bool_p"], namespace=params)

        assert not params.bool_p

    def test_param_parser_nested_defaults(self):
        class Nested(ParamsBase):
            int_p: int = 10
            float_p: float = 1.1
            bool_p: bool = False

        class Params(ParamsBase):
            nest: Nested = Nested()

        params = Params()
        parser = create_param_parser(Params, description=None)
        parser.parse_args([], namespace=params)

        assert params.nest.int_p == 10
        assert params.nest.float_p == 1.1
        assert not params.nest.bool_p

    def test_param_parser_nested_overrides(self):
        class Nested(ParamsBase):
            int_p: int = 10
            float_p: float = 1.1
            bool_p: bool = False

        class Params(ParamsBase):
            nest: Nested = Nested()

        params = Params()
        parser = create_param_parser(Params, description=None)
        parser.parse_args(
            ["--nest_int_p", "11", "--nest_float_p", "2.2", "--nest_bool_p"],
            namespace=params,
        )

        assert params.nest.int_p == 11
        assert params.nest.float_p == 2.2
        assert params.nest.bool_p

    def test_param_parser_multi_nested_defaults(self):
        class DoubleNested(ParamsBase):
            int_p: int = 10
            float_p: float = 1.1
            bool_p: bool = False

        class Nested(ParamsBase):
            double: DoubleNested = DoubleNested()

        class Params(ParamsBase):
            nest: Nested = Nested()

        params = Params()
        parser = create_param_parser(Params, description=None)
        parser.parse_args(
            [],
            namespace=params,
        )

        assert params.nest.double.int_p == 10
        assert params.nest.double.float_p == 1.1
        assert not params.nest.double.bool_p

    def test_param_parser_multi_nested_overrides(self):
        class DoubleNested(ParamsBase):
            int_p: int = 10
            float_p: float = 1.1
            bool_p: bool = False

        class Nested(ParamsBase):
            double: DoubleNested = DoubleNested()

        class Params(ParamsBase):
            nest: Nested = Nested()

        params = Params()
        parser = create_param_parser(Params, description=None)
        parser.parse_args(
            [
                "--nest_double_int_p",
                "11",
                "--nest_double_float_p",
                "2.2",
                "--nest_double_bool_p",
            ],
            namespace=params,
        )

        assert params.nest.double.int_p == 11
        assert params.nest.double.float_p == 2.2
        assert params.nest.double.bool_p


class TestSerializeParams(TestCase):
    def test_serialize(self):
        expected = "one=1&two&three=3&four"
        result = serialize_params(["--one=1", "--two", "--three", "3", "--four"])

        assert result == expected


class TestValidateModName(TestCase):
    def test_valid(self):
        assert validate_mod_name("whatever") is None
        assert validate_mod_name("whatever.wherever") is None

    def test_invalid(self):
        with pytest.raises(
            ValueError, match="invalid module name; may not contain spaces"
        ):
            validate_mod_name("what module")

        with pytest.raises(
            ValueError, match="invalid module name; may not import private modules"
        ):
            validate_mod_name("some._module")

        with pytest.raises(ValueError, match="invalid module name; invalid import"):
            validate_mod_name("some..module")

        with pytest.raises(ValueError, match="invalid module name; invalid import"):
            validate_mod_name("..module")

        with pytest.raises(ValueError, match="invalid module name; invalid import"):
            validate_mod_name("some.cool-module")

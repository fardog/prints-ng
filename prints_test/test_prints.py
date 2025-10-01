import pytest
from unittest import TestCase

from prints import ParamsBase, Result, check_module, create_param_parser


class TestCheckModule(TestCase):
    def test_good_module(self):
        class Params(ParamsBase):
            pass

        def main(params: Params) -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "main", main)
        setattr(mod, "Params", Params)

        assert check_module(mod) is None

    def test_missing_main(self):
        class Params(ParamsBase):
            pass

        def main(params: Params) -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "Params", Params)

        with pytest.raises(TypeError, match="module does not export a function `main`"):
            check_module(mod)

    def test_missing_params(self):
        class Params(ParamsBase):
            pass

        def main(params: Params) -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "main", main)

        with pytest.raises(TypeError, match="module does not export `Params`"):
            check_module(mod)

    def test_params_incorrect_subclass(self):
        class Params:
            pass

        def main(params: Params) -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "main", main)
        setattr(mod, "Params", Params)

        with pytest.raises(
            TypeError,
            match="module's `Params` export must subclass `prints.ParamsBase`",
        ):
            check_module(mod)

    def test_main_no_params(self):
        class Params(ParamsBase):
            pass

        def main() -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "main", main)
        setattr(mod, "Params", Params)

        with pytest.raises(
            TypeError, match="module must accept at least one parameter"
        ):
            check_module(mod)

    def test_main_invalid_parameter(self):
        class Params(ParamsBase):
            pass

        def main(name: str) -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "main", main)
        setattr(mod, "Params", Params)

        with pytest.raises(
            TypeError,
            match="module's `main` function must accept an instance of `Params` as its first parameter",
        ):
            check_module(mod)

    def test_main_non_default_args(self):
        class Params(ParamsBase):
            pass

        def main(params: Params, whatever: str) -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "main", main)
        setattr(mod, "Params", Params)

        with pytest.raises(
            TypeError,
            match="module may not contain args without defaults; found whatever",
        ):
            check_module(mod)

    def test_main_non_default_kwargs(self):
        class Params(ParamsBase):
            pass

        def main(params: Params, *, whatever: str) -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "main", main)
        setattr(mod, "Params", Params)

        with pytest.raises(
            TypeError,
            match="module may not contain kwargs without defaults; found whatever",
        ):
            check_module(mod)

    def test_main_accepts_args_with_defaults(self):
        class Params(ParamsBase):
            pass

        def main(
            params: Params, name: str = "name", *, do_thing: bool = True
        ) -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "main", main)
        setattr(mod, "Params", Params)

        assert check_module(mod) is None

    def test_main_accepts_varargs(self):
        class Params(ParamsBase):
            pass

        def main(params: Params, *args, **kwargs) -> Result:
            raise Exception("should not run")

        class mod:
            pass

        setattr(mod, "main", main)
        setattr(mod, "Params", Params)

        assert check_module(mod) is None


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

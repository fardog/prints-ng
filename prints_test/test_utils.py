import pytest
from unittest import TestCase
from prints.utils import check_module, flatten_params
from prints.params import ParamsBase, Result


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


class TestFlattenParams(TestCase):
    def test_flatten_simple(self):
        class Params(ParamsBase):
            a: str = "wut"
            b: int = 1
            c: float = 2.0

        expected = {
            "a": "wut",
            "b": 1,
            "c": 2.0,
        }

        assert flatten_params(Params()) == expected

    def test_flatten_nested(self):
        class SubParams(ParamsBase):
            d: str = "hmm"

        class Params(ParamsBase):
            a: str = "wut"
            b: int = 1
            c: float = 2.0
            sub: SubParams = SubParams()

        expected = {
            "a": "wut",
            "b": 1,
            "c": 2.0,
            "sub.d": "hmm",
        }

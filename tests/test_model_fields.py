import os
from typing import ClassVar

import numpy as np
import pytest

from cmap import Color, Colormap
from cmap._colormap import ColorStops

try:
    import pydantic
    from pydantic_compat import BaseModel

    V2 = int(pydantic.__version__.split(".")[0]) >= 2
except ImportError:
    pytest.skip("pydantic not installed", allow_module_level=True)

try:
    import pydantic_extra_types.color as pydantic_color
except (ImportError, NotImplementedError):
    import pydantic.color as pydantic_color


def test_pydantic_casting() -> None:
    assert Color(pydantic_color.Color("red")) is Color("red")


# we're interested in testing serializeability...
# Color can serialized with `str`, and Colormap can be serialized with `as_dict`
@pytest.mark.filterwarnings("ignore:`json_encoders` is deprecated")
def test_pydantic_validate() -> None:
    class MyModel(BaseModel):
        color: Color
        colormap: Colormap

        if V2:

            class Config:
                # since json.dump is not extendable, this just needs to be documented.
                json_encoders: ClassVar[dict] = {Color: str, Colormap: Colormap.as_dict}

    obj = MyModel(color=np.array([1.0, 0, 0]), colormap=["r", (0.7, "b"), "w"])
    assert obj.color is Color("red")
    assert obj.colormap == Colormap(["r", (0.7, "b"), "w"])
    serialized = obj.json()
    if os.getenv("CI"):
        # not sure why this is different in CI
        assert serialized == (
            '{"color":"red",'
            '"colormap":{"name":"custom colormap","identifier":"custom_colormap",'
            '"category":null,'
            '"value":['
            "[0.0,[1.0,0.0,0.0,1]],"
            "[0.7,[0.0,0.0,1.0,1]],"
            "[1.0,[1.0,1.0,1.0,1]]]}"
            "}"
        )
    if hasattr(MyModel, "model_validate_json"):
        assert MyModel.model_validate_json(serialized) == obj
    else:
        assert MyModel.parse_raw(serialized) == obj

    # with category colormaps, we only use the qualified name
    obj2 = MyModel(color="red", colormap=Colormap("viridis"))
    serialized2 = obj2.json()
    assert '"colormap":"bids:viridis"' in serialized2


def test_psygnal_serialization() -> None:
    # support for _json_encode_ is built into psygnal, ... don't need json_encoders
    psygnal = pytest.importorskip("psygnal")

    class MyModel(psygnal.EventedModel):  # type: ignore
        color: Color
        colormap: Colormap
        stops: ColorStops

    obj = MyModel(
        color=np.array([1, 0, 0]), colormap=["r", (0.7, "b"), "w"], stops="green_r"
    )

    data = obj.model_dump_json() if V2 else obj.json()

    if hasattr(MyModel, "model_validate_json"):
        assert MyModel.model_validate_json(data) == obj
    else:
        assert MyModel.parse_raw(data) == obj


def test_pydantic_preserves_modified_catalog_colormaps() -> None:
    class MyModel(BaseModel):
        colormap: Colormap

    def round_trip(cmap: Colormap) -> Colormap:
        obj = MyModel(colormap=cmap)
        data = obj.model_dump_json() if V2 else obj.json()
        model = (
            MyModel.model_validate_json(data)
            if hasattr(MyModel, "model_validate_json")
            else MyModel.parse_raw(data)
        )
        return model.colormap

    # an unmodified catalog colormap still serializes to its qualified name alone
    obj = MyModel(colormap=Colormap("viridis"))
    assert '"colormap":"bids:viridis"' in (obj.model_dump_json() if V2 else obj.json())

    assert round_trip(Colormap("viridis", under="red")).under_color == Color("red")
    assert round_trip(Colormap("viridis", name="renamed")).name == "renamed"
    assert round_trip(Colormap("viridis_r")) == Colormap("viridis_r")

    # a parametrization too small for the tolerant __eq__ to see still must not
    # collapse to the plain catalog name
    tweaked = Colormap("cubehelix", cmap_kwargs={"start": 0.500001})
    assert round_trip(tweaked).as_dict() == tweaked.as_dict()


def test_psygnal_serialization_of_a_configured_colormap() -> None:
    psygnal = pytest.importorskip("psygnal")

    class MyModel(psygnal.EventedModel):  # type: ignore
        colormap: Colormap

    cmap = Colormap(["r", "b"], interpolation="nearest", under="green", masked="orange")
    obj = MyModel(colormap=cmap)

    data = obj.model_dump_json() if V2 else obj.json()

    if hasattr(MyModel, "model_validate_json"):
        assert MyModel.model_validate_json(data).colormap == cmap
    else:
        assert MyModel.parse_raw(data).colormap == cmap

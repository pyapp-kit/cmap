import numpy as np
import pytest

from cmap import Color, Colormap
from cmap._colormap import ColorStops

pydantic = pytest.importorskip("pydantic", minversion="2")

try:
    import pydantic_extra_types.color as pydantic_color
except (ImportError, NotImplementedError):
    import pydantic.color as pydantic_color


def test_pydantic_casting() -> None:
    assert Color(pydantic_color.Color("red")) is Color("red")


def test_pydantic_validate() -> None:
    class MyModel(pydantic.BaseModel):
        color: Color
        colormap: Colormap

    obj = MyModel(color=np.array([1.0, 0, 0]), colormap=["r", (0.7, "b"), "w"])
    assert obj.color is Color("red")
    assert obj.colormap == Colormap(["r", (0.7, "b"), "w"])
    serialized = obj.model_dump_json()
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
    assert MyModel.model_validate_json(serialized) == obj

    # with category colormaps, we only use the qualified name
    obj2 = MyModel(color="red", colormap=Colormap("viridis"))
    serialized2 = obj2.model_dump_json()
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

    data = obj.model_dump_json()
    assert MyModel.model_validate_json(data) == obj

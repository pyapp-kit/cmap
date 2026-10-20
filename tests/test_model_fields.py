import json

import numpy as np
import pytest

from cmap import Color, Colormap
from cmap._colormap import ColorStops

pydantic = pytest.importorskip("pydantic", minversion="2")


def test_pydantic_casting() -> None:
    pydantic_color = pytest.importorskip("pydantic_extra_types.color")
    assert Color(pydantic_color.Color("red")) is Color("red")


def test_pydantic_validate() -> None:
    class MyModel(pydantic.BaseModel):
        color: Color
        colormap: Colormap

    obj = MyModel(color=np.array([1.0, 0, 0]), colormap=["r", (0.7, "b"), "w"])
    assert obj.color is Color("red")
    assert obj.colormap == Colormap(["r", (0.7, "b"), "w"])
    serialized = obj.model_dump_json()
    # (parsed, because alpha may serialize as either `1` or `1.0`)
    assert json.loads(serialized) == {
        "color": "red",
        "colormap": {
            "name": "custom colormap",
            "identifier": "custom_colormap",
            "category": None,
            "value": [
                [0.0, [1.0, 0.0, 0.0, 1]],
                [0.7, [0.0, 0.0, 1.0, 1]],
                [1.0, [1.0, 1.0, 1.0, 1]],
            ],
        },
    }
    assert MyModel.model_validate_json(serialized) == obj

    # with category colormaps, we only use the qualified name
    obj2 = MyModel(color="red", colormap=Colormap("viridis"))
    serialized2 = obj2.model_dump_json()
    assert '"colormap":"bids:viridis"' in serialized2
    assert MyModel.model_validate_json(serialized2) == obj2


def test_psygnal_serialization() -> None:
    psygnal = pytest.importorskip("psygnal")

    class MyModel(psygnal.EventedModel):  # type: ignore
        color: Color
        colormap: Colormap
        stops: ColorStops

    obj = MyModel(
        color=np.array([1, 0, 0]), colormap=["r", (0.7, "b"), "w"], stops="green_r"
    )
    assert MyModel.model_validate_json(obj.model_dump_json()) == obj


def test_pydantic_preserves_modified_catalog_colormaps() -> None:
    class MyModel(pydantic.BaseModel):
        colormap: Colormap

    def round_trip(cmap: Colormap) -> Colormap:
        obj = MyModel(colormap=cmap)
        return MyModel.model_validate_json(obj.model_dump_json()).colormap

    # an unmodified catalog colormap still serializes to its qualified name alone
    obj = MyModel(colormap=Colormap("viridis"))
    assert '"colormap":"bids:viridis"' in obj.model_dump_json()

    assert round_trip(Colormap("viridis", under="red")).under_color == Color("red")
    assert round_trip(Colormap("viridis", name="renamed")).name == "renamed"
    assert round_trip(Colormap("viridis_r")) == Colormap("viridis_r")
    # ... and the reversed name alone rebuilds it, so it serializes to that
    obj = MyModel(colormap=Colormap("viridis_r"))
    assert '"colormap":"bids:viridis_r"' in obj.model_dump_json()
    # a falsy argument is still an override: False is "nearest", viridis is linear
    nearest = Colormap("viridis", interpolation=False)
    assert round_trip(nearest).interpolation == "nearest"

    # a parametrization too small for the tolerant __eq__ to see still must not
    # collapse to the plain catalog name
    tweaked = Colormap("cubehelix", cmap_kwargs={"start": 0.500001})
    assert round_trip(tweaked).as_dict() == tweaked.as_dict()


def test_psygnal_serialization_of_a_configured_colormap() -> None:
    psygnal = pytest.importorskip("psygnal")

    class MyModel(psygnal.EventedModel):  # type: ignore
        colormap: Colormap

    cmap = Colormap(["r", "b"], interpolation="nearest", under="green", nan="orange")
    obj = MyModel(colormap=cmap)
    assert MyModel.model_validate_json(obj.model_dump_json()).colormap == cmap

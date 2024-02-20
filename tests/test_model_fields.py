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
except ImportError:
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
        # FIXME: why is this different on CI?
        assert serialized == (
            '{"color": "red", '
            '"colormap": {"name": "custom colormap", "identifier": "custom_colormap", '
            '"category": null, '
            '"value": ['
            "[0.0, [1.0, 0.0, 0.0, 1]], "
            "[0.7, [0.0, 0.0, 1.0, 1]], "
            "[1.0, [1.0, 1.0, 1.0, 1]]]}"
            "}"
        )
    if hasattr(MyModel, "model_validate_json"):
        assert MyModel.model_validate_json(serialized) == obj
    else:
        assert MyModel.parse_raw(serialized) == obj


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

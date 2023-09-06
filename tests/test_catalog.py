from itertools import chain

import numpy as np
import pytest

from cmap import Colormap
from cmap._catalog import Catalog

catalog = Catalog()


@pytest.mark.filterwarnings("ignore:The name:")
def test_catalog_data() -> None:
    """Test that all catalog data is one of a couple normalized types."""
    for name, item in catalog.items():
        if isinstance(item.data, list):
            item_lengths = [len(x) for x in item.data]
            assert len(set(item_lengths)) == 1
            if item_lengths[0] == 2:
                assert all(len(x[1]) == 3 for x in item.data) or all(
                    len(x[1]) == 4 for x in item.data
                )
            else:
                assert item_lengths[0] in (3, 4)
        elif callable(item.data):
            x = np.linspace(0, 1, 256)
            assert item.data(x).shape in ((256, 3), (256, 4))
        else:
            raise AssertionError(f"Unexpected data type: {type(item.data)}")
        Colormap(name)  # smoke test

    assert len(catalog) > 100


def test_lower_map() -> None:
    # make sure the lower map is the same length as the original
    # ... i.e. that we have no name collisions
    assert len(catalog._data) == len(catalog._data)


def test_data_loading() -> None:
    for name in catalog._original_names:
        Colormap(name)


def test_catalog_names() -> None:
    assert "bids:viridis" in catalog.namespacedKeys()
    assert "viridis" in catalog.shortKeys()
    assert [
        catalog.resolve(x) for x in chain(catalog.shortKeys(), catalog.namespacedKeys())
    ]
    with pytest.raises(KeyError):
        catalog.resolve("not-a-cmap")

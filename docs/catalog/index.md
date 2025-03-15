# Colormap Catalog

To use any colormap in the catalog, you can pass its name to the [`Colormap`][cmap.Colormap]
constructor:

```python
from cmap import Colormap

cmap = Colormap('viridis')
```

!!!note  "Coming from matplotlib?"
    We test against all of the named colormaps in matplotlib, so any `'name'`
    that you can use with `matplotlib.colormaps['name']` can also be passed to
    `cmap.Colormap`. To convert a `cmap.Colormap` to a native
    `matplotlib.colors.Colormap` instance, you may call
    [`.to_mpl()`][cmap.Colormap.to_matplotlib].

See the [Colormap API docs][cmap.Colormap] for details.

<!--
With that object you can do things like:

```python
# call it directly to colorize an ndarray of values
# values should be (pre-normalized to 0-1)
img = np.random.random((24, 24))
colored = cmap(img)
assert colored.shape == (24, 24, 4)

# use it in matplotlib
import matplotlib.pyplot as plt
plt.imshow(img, cmap=cmap.to_mpl())

# use it in napari
from napari import view_image
view_image(img, colormap=cmap.to_napari())
``` -->

!!!tip "Tip: Reversed colormaps"

    You can append `'_r'` to any of the colormap names listed below to get a
    reversed version of that colormap. For example, `'viridis_r'`

    {{ cmap: viridis }}
    {{ cmap: viridis_r }}

    This works with function based colormaps as well:

    {{ cmap: cubehelix }}
    {{ cmap: cubehelix_r }}

## Colormaps by category { data-search-exclude }

{{ CMAP_CATALOG }}

<!-- Note: this is here because of `navigation.instant` in the mkdocs settings -->
<script>typeof(initFilters) !== 'undefined' && initFilters();</script>

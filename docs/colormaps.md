# Colormaps

The `cmap.Colormap` type represents a colormap.

Also known as a LUT (look-up table), a colormap is a mapping from a scalar value to a color.  Colormaps are used in a variety of contexts, including image processing, data visualization, and scientific visualization.  The `cmap` library provides a [number of built-in colormaps](catalog/index.md), including all of the colormaps in matplotlib, napari, vispy, and more.

```python
from cmap import Colormap

# argument can be any "ColormapLike".  See rules below
cm = Colormap('viridis')
```

## `ColormapLike` objects

The following objects can be interpreted as a colormap, and used as the first argument
to the [`cmap.Colormap`][] constructor; `cmap` refers to these objects collectively as
"`ColormapLike`".  Briefly, valid arguments are of type:

- [⬇️ `str`](#str)
- [⬇️ `Iterable[ColorLike | tuple[float, ColorLike]]`](#iterablecolorlike-tuple)  *(see [`ColorLike`](colors.md#colorlike-objects))*
- [⬇️ `numpy.ndarray`](#numpyndarray)
- [⬇️ `dict`](#dict)
- [⬇️ `Callable[[ArrayLike], ArrayLike]`](#callable)

### `str`

- A `string` containing a [recognized colormap name](catalog/index.md).

    - `Colormap('viridis')` {{ cmap_expr: 'viridis' }}
    - `Colormap('batlow')` {{ cmap_expr: 'batlow' }}

    !!!note "Matplotlib names ✅"
        Any valid matplotlib colormap key that could be used in `matplotlib.colormaps[...]`
        is also a valid `cmap` colormap name.

- A string containing a [recognized colormap name](catalog/index.md) suffixed with `"_r"`
   to reverse the colormap:

    - `Colormap('viridis_r')` {{ cmap_expr: 'viridis_r' }}
    - `Colormap('batlow_r')` {{ cmap_expr: 'batlow_r' }}

### `Iterable[ColorLike | tuple]`

- An [`Iterable`][typing.Iterable] of [`ColorLike`](colors.md#colorlike-objects) objects:

    - `Colormap(['blue', 'yellow', 'red'])` {{ cmap_expr: ['blue', 'yellow', 'red'] }}
    - `Colormap([(0, 0, 1.), "#FF0", "rgb(255, 0, 0)"])` {{ cmap_expr: [(0, 0, 1.), "#FF0", "rgb(255, 0, 0)"] }}

    !!!note
        In the case of an iterable of colors, all colors are assumed to be
        equally spaced along the colormap.

- An [`Iterable`][typing.Iterable] of `ColorLike` OR `tuple[float,
   ColorLike]` objects, where the `float` represents the position of the color
   along the colormap from 0-1 (*aka* the "color stop"):

    - `Colormap([(0, 'blue'), (0.8, 'yellow'), (1, 'red')])` {{ cmap_expr: [(0, 'blue'), (0.8, 'yellow'), (1, 'red')] }}

    If omitted, the first and last color stops are assumed to be at 0 and 1,
    respectively.

    - `Colormap(['blue', (0.8, 'yellow'), 'red'])` {{ cmap_expr: ['blue', (0.8, 'yellow'), 'red'] }}

    If the first or last color stop is *not* at 0 or 1, the first/last color is
    repeated at the 0th or 1 position, respectively.

    - `Colormap([(0.4, 'blue'), (0.8, 'yellow'), 'red'])` {{ cmap_expr: [(0.4, 'blue'), (0.8, 'yellow'), 'red'] }}

         *(same as `['blue', (0.4, 'blue'), (0.8, 'yellow'), 'red']`)*

    If internal stops are *partially* provided, the missing values are
    assumed to be equally spaced between any provided neighboring positions
    (or 0 and 1, if none are provided).  They are **NOT** placed at their global
    `index / (len(colors) - 1)`.

    - `Colormap(['blue', 'green', (0.8, 'yellow'), 'red'])` {{ cmap_expr: ['blue', 'green', (0.8, 'yellow'), 'red'] }}

        *(same as `['blue', (0.4, 'green'), (0.8, 'yellow'), 'red']`)*

### `numpy.ndarray`

A [`numpy.ndarray`][], in one of the following formats:

- an **`(N, 3)`** array of `N` RGB colors equally spaced along the colormap:

    `Colormap(np.array([[0, 0, 1.], [1., 1., 0], [1., 0, 0]]))` {{ cmap_expr: np.array([[0, 0, 1.], [1., 1., 0], [1., 0, 0]]) }}

- an **`(N, 4)`** array of `N` RGBA colors equally spaced along the colormap:

    `Colormap(np.array([[0, 0, 1., 1.], [1., 1., 0, 0.7], [1., 0, 0, 0.3]]))` {{ cmap_expr: np.array([[0, 0, 1., 1.], [1., 1., 0, 0.7], [1., 0, 0, 0.3]]) }}

- an **`(N, 5)`** array of color stops, where the first column is the position of the color stop
    and the remaining 4 columns are the RGBA colors:

    ```python
    Colormap(
        np.array([
            [0.0, 0.0, 0.0, 1.0, 1.0],
            [0.8, 1.0, 1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 0.0, 1.0]
        ])
    )
    ```

    {{ cmap_expr: np.array([[0, 0, 0, 1., 1.], [0.8, 1., 1., 0, 1.], [1., 1., 0, 0, 1.]]) }}

### `dict`

- A `{position -> color}` `dict` of color stops, where the keys are the positions of the color stops
   and the values are the colors:

    - `Colormap({0: 'blue', 0.5: 'yellow', 1: 'red'})` {{ cmap_expr: {0: 'blue', 0.5: 'yellow', 1: 'red'} }}

- A [matplotlib-style `segmentdata`
   dict](https://matplotlib.org/stable/tutorials/colors/colormap-manipulation.html#creating-linear-segmented-colormaps),
   with keys `"red"`, `"green"`, `"blue"`, and (optionally) `"alpha"` and values that are
   either:

    - an (N, 3) array-like `[[x, y0, y1], ...]` where `x` is the color stop position,
      and `y0` and `y1` are the values of the color on either side of the stop
      position.

        ```python
        cdict = {'red':  [[0.0,  0.0, 0.0],
                        [0.5,  1.0, 1.0],
                        [1.0,  1.0, 1.0]],
                'green': [[0.0,  0.0, 0.0],
                        [0.25, 0.0, 0.0],
                        [0.75, 1.0, 1.0],
                        [1.0,  1.0, 1.0]],
                'blue':  [[0.0,  0.0, 0.0],
                        [0.5,  0.0, 0.0],
                        [1.0,  1.0, 1.0]]}
        Colormap(cdict)
        ```

        {{ cmap_expr: {'red': [[0,0,0],[0.5,1.,1.],[1.,1.,1.]], 'green': [[0,0,0],[0.25,0,0],[0.75,1.,1.],[1.,1.,1.]], 'blue': [[0,0,0],[0.5,0,0],[1.,1.,1.]]} }}

    - a callable that accepts an array of 0-1 values and returns another array of 0-1 values:

        `Colormap({"red": lambda x: x, "green": lambda x: x**2, "blue": lambda x: x**0.5})`
        {{ cmap_expr: {"red": lambda x: x, "green": lambda x: x\*\*2, "blue": lambda x: x\*\*0.5} }}

### `Callable`

- A single [`Callable`][typing.Callable], object which must accept an array of
  values and return an `(N, 3)` or `(N, 4)` array of colors
    - `Colormap(lambda x: np.stack([x, np.sin(x*10), np.cos(x*10)], axis=1))`
      {{ cmap_expr: lambda x: np.stack([x, np.sin(x\*10), np.cos(x\*10)], axis=1) }}

## Usage

### Useful properties

 ... TODO

## Immutability

All colormaps are immutable and cannot be modified after instantiation.

## Usage with external visualization libraries

A primary motivation of `cmap` is to make it easy to use colormaps in
external visualization libraries.  To that end, `cmap.Colormap` provides
`to_<libname>()` methods for a number of libraries:

!!!tip
    Some of these methods take additional arguments, see [Colormap API](api/colormap.md)
    for details.

- [matplotlib](https://matplotlib.org/)

    ```python
    Colormap("viridis").to_mpl()  # or to_matplotlib()
    ```

    Returns an instance of `matplotlib.colors.Colormap`.

- [napari](https://napari.org/)

    ```python
    Colormap("viridis").to_napari()
    ```

    Returns an instance of `napari.utils.colormaps.colormap.Colormap`.

- [vispy](https://vispy.org/)

    ```python
    Colormap("viridis").to_vispy()
    ```

    Returns an instance of `vispy.color.colormap.Colormap`.

- [pygfx](https://pygfx.readthedocs.io/en/latest/)

    ```python
    Colormap("viridis").to_pygfx()
    ```

    Returns an instance of `pygfx.Texture`.

- [plotly](https://plotly.com/python/)

    ```python
    Colormap("viridis").to_plotly()
    ```

    Returns a list of tuples, where each tuple is a color stop:

    ```python
    [
        [0.0, 'rgb(68, 1, 84)'],
        [0.00392156862745098, 'rgb(68, 2, 86)'],
        [0.00784313725490196, 'rgb(69, 4, 87)'],
        [0.011764705882352941, 'rgb(69, 5, 89)'],
        ...
    ```

- [bokeh](https://docs.bokeh.org/en/latest/)

    ```python
    Colormap("viridis").to_bokeh()
    ```

    Returns an instance of `bokeh.models.mappers.LinearColorMapper`

- [altair](https://altair-viz.github.io/)

    ```python
    Colormap("viridis").to_altair()
    ```

    Returns a list of hexadecimal color strings.

## Usage with pydantic

`Colormap` can be used as a field type in
[pydantic](https://pydantic-docs.helpmanual.io/usage/types/). models.

```python
from pydantic import BaseModel
from cmap import Colormap

class Foo(BaseModel):
    colormap: Colormap


foo = Foo(colormap='viridis')  # or any other ColormapLike
foo.colormap
```

!!!tip "Serialization in pydantic"
    Unfortunately, serialization with the `json` module is not easily
    pluggable, so if you want to serialize a pydantic model with a `Colormap`
    field to JSON, add the following encoder to your model:

    ```python
    class Foo(BaseModel):
        colormap: Colormap

        class Config:
            json_encoders = {Colormap: Colormap.as_dict}

    #example
    Foo(colormap=['red', 'green']).json()
    ```

    results in

    ```json
    {"colormap":
        {"name": "custom colormap",
         "identifier": "custom_colormap",
          "category": null,
          "color_stops": [[0.0, [1.0, 0.0, 0.0, 1]], [1.0, [0.0, 0.5019607843137255, 0.0, 1]]]
        }
    }
    ```

!!!tip "Serialization in `psygnal.EventedModel`"
    `Colormap` supports serialization in
    [`psygnal.EventedModel`](https://psygnal.readthedocs.io/en/latest/API/model/)
    out of the box.  The `json_encoders = {Colormap: Colormap.as_dict}` line in the `Config`
    class mentioned above is not necessary.

## Rich repr

If you use [`rich` pretty
printing](https://rich.readthedocs.io/en/stable/reference/pretty.html#rich.pretty.install),
`Colormap` objects have a nice repr that shows the color in the terminal

```python
from rich import pretty

pretty.install()
```

![rich repr](images/colormap_repr.png)

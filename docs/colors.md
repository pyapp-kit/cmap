# Colors

The `cmap.Color` type represents an individual color.

```python
from cmap import Color

# argument can be any "ColorLike".  See rules below
red   = Color('red')
red2  = Color('#FF0000')
red3  = Color('rgb(255, 0, 0)')
red4  = Color('hsl(0, 100%, 50%)')
red5  = Color((255, 0, 0))
red6  = Color((1.0, 0.0, 0.0))
red7  = Color([1.0, 0.0, 0.0])
red8  = Color(np.array([1.0, 0.0, 0.0]))
red9  = Color(0xFF0000)
red10 = Color(16711680)
```


## `ColorLike` objects

The following objects can be interpreted as a color, and used as the first argument
to the `Color` constructor; `cmap` refers to these objects collectively as "`ColorLike`".

Briefly, valid arguments are of type:

- `str`
- `tuple[float | int, float | int, float | int]`
- `tuple[float | int, float | int, float | int, float]`
- `Sequence[int | float]`
- `numpy.ndarray`
- `None`
- `int`
- `cmap.Color`
- `pydantic.color.Color`
- `colour.Color`

In detail:

1. A string containing a color name. All CSS color names are supported, case is
   ignored along with spaces, underscores and dashes  (see [complete list
   below](#recognized-color-names).)

    - `'red'`
    - `'slategray'`

1. A string containing a 3, 6, or 8-digit [hexadecimal color
   code](https://w3c.github.io/csswg-drafts/css-color/#hex-notation):

    - `'#0F5'`     (RGB)
    - `'#00FF55'`   (RRGGBB)
    - `'#00FF55FF'`  (RRGGBBAA)

1. A string containing a valid css
   [`rgb(a)`](https://w3c.github.io/csswg-drafts/css-color/#rgb-functions) or
   [`hsl(a)`](https://w3c.github.io/csswg-drafts/css-color/#the-hsl-notation)
   color:
    - `'rgb(255, 0, 0)'`
    - `'rgb(100%, 0%, 0%)'`
    - `'rgba(255, 0, 0, 0.5)'`
    - `'rgba(255, 0, 0)'`  (it's ok to use `rgba` without an alpha value)
    - `'rgba(100%, 0%, 0%, 0.5)'`
    - `'hsl(180, 100%, 50%)'`
    - `'hsla(180, 100%, 50%, 0.5)'`
    - `'hsla(180, 100%, 50%)'` (it's ok to use `hsla` without an alpha value)

1. A `tuple` containing 3 `int` values between 0-255 (for RGB), or 3 int values
   and a `float` alpha value from 0-1 (for RGBA). (Note: the alpha value is
   *always* a float between 0-1).
    - `(0, 128, 255)`
    - `(0, 128, 255, 0.5)`

1. A `tuple` containing 3 or 4 `float` values (see note on ambiguity below):
    - `(0.0, 0.5, 1.0)`
    - `(0.0, 0.5, 1.0, 0.5)`

    !!!warning "Ambiguities with tuples of 0 and 1"

        While it's nice to support both the 8-bit and float inputs, there is
        amgiguity in the case of a tuple of integers containing only zeros
        and ones (e.g. `(0, 0, 1)`).  The convention in `cmap` is to treat a
        tuple of *all* integers as 8-bit RGB values, and a tuple with *any*
        floats (excepting the 4th alpha value) as float RGB values, so

        - `(0, 0, 1) == (0, 0, 1/255) == '#000001'`
        - `(0, 0, 1.) == (0, 0, 255) == '#0000FF'`

        :exclamation: **To avoid ambiguity, it's best to use float values.** :exclamation:

    !!! note "Overflow"
        In all cases, numeric values are clipped to their valid range, so `(0, 300,
        0, 2.0)` is equivalent to `(0, 255, 0, 1.0)`, and `(0.0, 1.5, 0.0, -0.5)` is
        equivalent to `(0.0, 1.0, 0.0, 0)`.

1. A [`numpy.ndarray`][] with shape `(3,)` or `(4,)`: where integer dtypes are
   interpreted as 8-bit color values (from 0-255) and float dtypes are interpreted
   as float color values (from 0-1). For colors with alpha, you must use a float
   dtype.
    - `np.array([0, 128, 255])`  (8-bit RGB)
    - `np.array([0.0, 0.5, 1.0])`  (float RGB)
    - `np.array([0.0, 0.5, 1.0, 0.5])`  (float RGBA)
    - **NOT:** `np.array([0, 128, 255, 0.5])` (the 0.5 makes this evaluated as a
      float color, which will be clipped to (0, 1., 1., 0.5))

1. The literal `None`, interpreted as transparent black (i.e. `(0, 0, 0, 0)`)

1. A single integer value: interpreted as a 24-bit integer RGB color value,
   where the first 8 bits are the red channel, the next 8 bits are the green
   channel, the last 8 bits are the blue channel (alpha values other than 1
   aren't supported in this mode).  This is most convenient when [expressing
   integers in base-16](https://docs.python.org/3/library/functions.html#int).
    - `0xFF0000`  (red, in base 16 integer form)
    - `16711680`  (also red, but in the default base 10 integer form)
    - `0xFF00FF`  (magenta, in base 16 integer form)
    - `16711935`  (also magenta, but in the default base 10 integer form)

    !!!Note
        [Base-16 integers](https://docs.python.org/3/library/functions.html#int)
        look the same as their hexadecimal color string representation, but
        lacks the quotes, and are preceded by `0x` instead of `#`.

1. An instance of [`cmap.Color`][] itself: which is returned unchanged
    - `Color(Color('red')) is Color('red')`)

1. (*Third-party object*): An instance of [`pydantic.color.Color`](https://docs.pydantic.dev/usage/types/#color-type).

1. (*Third-party object*): An instance of [`colour.Color`](https://github.com/vaab/colour)

## Usage

See [Color class API][cmap.Color] for complete details, highlights are listed here:

```python
from cmap import Color

trq = Color('turquoise')
```

### Useful properties

Convert to a variety of forms:

```python
trq.hex          # '#40E0D0'
trq.rgba         # RGBA(r=0.2510, g=0.8784, b=0.8157, a=1)
trq.hsl          # HSLA(h=0.4833, s=0.7207, l=0.5647, a=1)
trq.hsv          # HSVA(h=0.4833, s=0.7143, v=0.8784, a=1)
trq.rgba8        # RGBA8(r=64, g=224, b=208, a=1)
trq.rgba_string  # 'rgb(64, 224, 208)'
trq.name         # 'turquoise'
```

### Useful magic methods

Comparing a color to anything will attempt to cast the other object:

```python
trq == 'turquoise'  # True
trq is 'turquoise'  # False ... naturally, it's not the same object
```

!!!tip
    The internal representation of `Color` is a 4-tuple of float values
    from 0-1 (RGBA). In general, you can assume that sequence-based methods
    will return those values.

`Color` implements [`__array__`](https://numpy.org/devdocs/user/basics.interoperability.html#the-array-method) so it behaves as an ArrayLike object:

```python
np.asarray(trq)  # array([0.25098039, 0.87843137, 0.81568627, 1.])
```

You can iterate it

```python
list(trq)  #  [0.25098039, 0.87843137, 0.81568627, 1]
```

.. or index it:

```python
trq[:2]  # (0.25098039215686274, 0.8784313725490196)
```

## Object Caching

Note that `Color` objects are cached after creation and the same object
instance is returned for equivalent inputs.  This means that you can use
`is` to compare colors, and that you can use `Color` objects as dictionary
keys.

```python
assert Color('red') is Color((255, 0, 0))
```

## Immutability

All colors are immutable and cannot be modified after instantiation.

```python
trq.name = 'foo'  # AttributeError: Color is immutable
```

## Usage with pydantic

`Color` can be used as a field type in
[pydantic](https://pydantic-docs.helpmanual.io/usage/types/). models.

```python
from pydantic import BaseModel
from cmap import Color

class Foo(BaseModel):
    color: Color


foo = Foo(color='red')
foo.color is Color('red')  # True
```

!!!tip "Serialization in pydantic"
    Unfortunately, serialization with the `json` module is not easily
    pluggable, so if you want to serialize a pydantic model with a `Color`
    field to JSON, add the following encoder to your model to cast
    `Color` objects to strings:

    ```python
    class Foo(BaseModel):
        color: Color

        class Config:
            json_encoders = {Color: str}

    #example
    Foo(color=(0, 11, 23)).json()  # '{"color": "#000B17"}'
    ```

!!!tip "Serialization in `psygnal.EventedModel`"
    Color supports serialization in
    [`psygnal.EventedModel`](https://psygnal.readthedocs.io/en/latest/API/model/)
    out of the box.  The `json_encoders = {Color: str}` line in the `Config`
    class mentioned above is not necessary.

## Rich repr

If you use [`rich` pretty
printing](https://rich.readthedocs.io/en/stable/reference/pretty.html#rich.pretty.install),
Color objects have a nice repr that shows the color in the terminal

```python
from rich import pretty

pretty.install()
```

![rich repr](images/color_repr.png){ width=300 }

## Recognized Color Names { data-search-exclude }

The following names may be used as string inputs to the `Color` constructor.

(case insensitive; spaces, dashes, and underscores are ignored)

{{ COLOR_LIST }}

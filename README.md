# cmap

[![License](https://img.shields.io/pypi/l/cmap.svg?color=green)](https://github.com/tlambert03/cmap/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/cmap.svg?color=green)](https://pypi.org/project/cmap)
![Conda](https://img.shields.io/conda/v/conda-forge/cmap)
[![Python Version](https://img.shields.io/pypi/pyversions/cmap.svg?color=green)](https://python.org)
[![CI](https://github.com/tlambert03/cmap/actions/workflows/ci.yml/badge.svg)](https://github.com/tlambert03/cmap/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tlambert03/cmap/branch/main/graph/badge.svg)](https://codecov.io/gh/tlambert03/cmap)
[![Documentation Status](https://readthedocs.org/projects/cmap-docs/badge/?version=latest)](https://cmap-docs.readthedocs.io/en/latest/?badge=latest)

Scientific colormaps for python, with no dependencies beyond numpy.

With `cmap`, you can use any of the colormaps from
[matplotlib](https://matplotlib.org/stable/tutorials/colors/colormaps.html),
[cmocean](https://matplotlib.org/cmocean/),
[colorbrewer](https://colorbrewer2.org/),
[crameri](https://www.fabiocrameri.ch/colourmaps/),
[seaborn](https://seaborn.pydata.org/tutorial/color_palettes.html), and a host
of other collections in your python code, without having to install matplotlib
or any other dependencies beyond numpy.

:book: [See the complete
catalog](https://cmap-docs.readthedocs.io/en/latest/catalog/)

There are a number of python libraries that provide or require colormaps or
basic color support, but they all either depend on matplotlib, provide a
specialized set of colormaps intended to extend those provided by matplotlib, or
roll their own colormap solution that vendors/duplicates other libraries.

`cmap` is a lightweight, library that provides a large collection of colormaps
with no dependencies beyond numpy.  It provides exports to a number of known
third-party colormap objects, allowing it to be used across a wide range of
python visualization libraries.  The intention is to provide a library that can
be used by any python library that needs colormaps, without forcing the user to
install matplotlib (while still being compatible with matplotlib and other
libraries that use matplotlib colormaps).

`cmap` is strictly typed and fully tested, with a focus on good developer
experience.

## Install

```
pip install cmap
```

```
conda install -c conda-forge cmap
```

## Usage

See [Documentation](https://cmap-docs.readthedocs.io/) for full details.

### [`cmap.Color`](https://cmap-docs.readthedocs.io/en/latest/colors/)

The `cmap.Color` object is a simple wrapper around a tuple of RGBA scalars, with
a few convenience methods for converting to other color objects.

```python
from cmap import Color

red = Color("red")  # or a variety of other "color like" inputs
```

### [`cmap.Colormap`](https://cmap-docs.readthedocs.io/en/latest/colormaps/)

The `cmap.Colormap` object is a callable that can map a scalar value (or numpy
array of values) to an RGBA color (or a numpy array of RGBA colors).  API is
intended to mimic the behavior of a
[`matplotlib.colors.Colormap`](https://matplotlib.org/stable/api/_as_gen/matplotlib.colors.Colormap.html#matplotlib.colors.Colormap)
object (without requiring matplotlib)

```python
In [1]: import cmap

# or a variety of other "colormap like" inputs
In [2]: cmap1 = cmap.Colormap(["red", "green", "blue"])

In [3]: cmap1(np.linspace(0,1,5))
Out[3]:
array([[1.        , 0.        , 0.        , 1.        ],
       [0.50393701, 0.24900417, 0.        , 1.        ],
       [0.        , 0.50196078, 0.        , 1.        ],
       [0.        , 0.24900417, 0.50393701, 1.        ],
       [0.        , 0.        , 1.        , 1.        ]])
```

Note that the input array must be normalized from 0-1, so if you're applying a colormap
to an integer array (like an image) you must apply any contrast limits and rescale to
0-1 before passing it to a `Colormap`.

## Third Party Library Support

The `cmap.Colormap` object has convenience methods that allow it to be used with a number of third-party colormap objects (like
`matplotlib`, `vispy`, `napari`, `plotly`, etc...).

See [documentation](https://cmap-docs.readthedocs.io/en/latest/colormaps/#usage-with-external-visualization-libraries)
for details.

If you would like to see support added for a particular library, please open an issue or PR.

## Alternatives

Other libraries providing colormaps:


- [matplotlib](https://matplotlib.org/stable/tutorials/colors/colormaps.html)
- [seaborn](https://seaborn.pydata.org/tutorial/color_palettes.html)  (subclasses matplotlib)
- [proplot](https://proplot.readthedocs.io/en/latest/colormaps.html)  (subclasses matplotlib)
- [palettable](https://jiffyclub.github.io/palettable/) (mostly data, import doesn't depend on matplotlib, but usage largely does)
- [cmocean](https://matplotlib.org/cmocean/) (mostly data, outputs matplotlib colormaps)
- [colorcet](https://colorcet.holoviz.org/) (mostly data, usage requires either matplotlib or bokeh)
- [cmasher](https://cmasher.readthedocs.io/) (requires matplotlib)
- [cmyt](https://github.com/yt-project/cmyt) (requires matplotlib)
- [cmcrameri](https://github.com/callumrollo/cmcrameri) (requires matplotlib, wraps <https://www.fabiocrameri.ch/colourmaps/>)
- [distinctipy](https://github.com/alan-turing-institute/distinctipy)  (generates distinct color sets, only requires numpy)
- [Farrow & Ball Matplotlib](https://github.com/vork/farrowandball) (requires matplotlib)
- [mplcyberpunk](https://github.com/dhaitz/mplcyberpunk) (requires matplotlib)

## References and Further reading

- [Choosing Colormaps in Matplotlib](https://matplotlib.org/stable/tutorials/colors/colormaps.html)
- [A Better Default Colormap for Matplotlib | SciPy 2015 | Nathaniel Smith and Stéfan van der Walt](https://www.youtube.com/watch?v=xAoljeRJ3lU)
- blog post for above video: <https://bids.github.io/colormap/>
- [Origins of Colormaps, Cleve Moler, February 2, 2015](https://blogs.mathworks.com/cleve/2015/02/02/origins-of-colormaps/)
- [Documenting the matplotlib colormaps, @endolith](https://gist.github.com/endolith/2719900)
- [Color Map Advice for Scientific Visualization](https://www.kennethmoreland.com/color-advice/)
- <https://colorcet.com/>, Peter Kovesi
- [Kovesi: Good Colour Maps: How to Design Them.](https://arxiv.org/abs/1509.03700)
- https://www.fabiocrameri.ch/colourmaps/

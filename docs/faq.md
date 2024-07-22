# FAQ

## How can I add a new colormap?

We welcome contributions!

Before opening a PR, please [open an
issue](https://github.com/tlambert03/cmap/issues/new) to discuss the colormap(s)
you would like to add.  A screenshot and description of the colormap is helpful.

To add a colormap: you first need to pick a namespace for your colormap.
Namespaces are directories in the `src/cmap/data` folder.

- If you are extending an existing colormap library, you should add to that
existing directory.
- If you want to add a new collection of colormaps, you should create a new
namespace (please open an issue to discuss this first).
- If you have a few colormaps that you have personally created that are not part
of any existing collection, feel free to contribut to the `cmap/contrib`
namespace

Once you have picked a namespace:

1. Find the `cmap/data/<namespace>/record.json` file
1. For each colormap you want to add, add a new item to the `colormaps` object
    in the `record.json` file.  The key should be the name of the colormap, and
    the value should be an object with the following keys:

    - `data`: either a direct
       [`ColormapLike` data](https://cmap-docs.readthedocs.io/en/stable/colormaps/#colormaplike-objects)
       entry, such as an array of RGB values; or a
       string pointing to the python-path of colormap data in the form of
       `cmap.data.<namespace>:<colormap>`.
    - `category`: one of `"sequential"`, `"diverging"`, `"cyclic"`,
       `"qualitative"`, or `"miscellaneous"`

    The following keys are optional:

    - `tags`: a list of tags to help categorize the colormap.  These appear on
       the website.
    - `info`: a brief description of the colormap.  This appears on the
       website (recommended).
    - `interpolation`: whether the colormap should be interpolated, between
       stops. If not provided, the assumption is `True`.
    - `aliases`: a list of alternative names for the colormap.
    - `over`: color to show when values are over the range.
    - `under`: color to show when values are under the range.
    - `bad`: color to show when values are NaN or masked.
1. If your `data` object above `module:attribute` string, don't forget to add
   the data into the `cmap/data/<namespace>/__init__.py` file.  For example:

    ```python
    my_colormap = [
        [0.468775, 0.468876, 0.468851],
        [0.473809, 0.47391, 0.473885],
        [0.478873, 0.478974, 0.478949],
        [0.483952, 0.484053, 0.484028],
        ...
    ]
    ```

It may be helpful to look at existing namespaces in the
`cmap/data` directory for examples of how to structure the data.

## How can I add support for exporting to another colormap format?

cmap [exports to a variety of known third-party colormap
formats](https://cmap-docs.readthedocs.io/en/latest/colormaps/#usage-with-external-visualization-libraries).

If you are the author (or user) of a library that consumes colormaps, and you
would like to have a `to_your_lib()` function in `cmap`, we welcome
contributions!

Have a look at `_external.py` for examples of how to add support for your
format.

## Don't we already have enough colormap libraries?

Yes, we do!  But maybe just one more? :joy:.

The primary driver for this
was to create a dependency-free library (save numpy) that could be used
in a variety of visualization libraries.  We will never depend on anything
outside of numpy, and we export to a variety of third-party colormaps.

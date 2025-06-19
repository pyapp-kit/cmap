# FAQ

## How can I add a new colormap?

We welcome contributions!

To add a colormap: you first need to pick a namespace for your colormap.
Namespaces are directories in the `src/cmap/data` folder.

- If the colormap is part of known broader collection (e.g., `cet`, `cmocean`,
  `colorbrewer`, etc.), please check to see whether the collection already
  exists in the [`cmap/data`
  directory](https://github.com/pyapp-kit/cmap/tree/main/src/cmap/data).  If so,
  please extend that collection. If not, please create a new namespace and
  directory for that collection.
- If you would like to contribute a colormap that doesn't nicely fit into an
  broader collection of colormaps (regardless of whether that collection exists
  in `cmap`), please contribute to the `cmap/contrib` namespace.

If you are unsure where to put your colormap, please open an issue.

Once you have picked a namespace:

1. Find the `cmap/data/<namespace>/record.json` file
1. For each colormap you want to add, add a new item to the `colormaps` object
   in the `record.json` file.  The key should be the name of the colormap, and
   the value should be an object with the following keys:
      - `data`: either a direct
         [`ColormapLike` data](colormaps.md#colormaplike-objects)
         entry, such as an array of RGB values; or a
         string pointing to the python-path of colormap data in the form of
         `cmap.data.<namespace>:<colormap>`.
      - `category`: one of `"sequential"`, `"diverging"`, `"cyclic"`,
         `"qualitative"`, or `"miscellaneous"`

      _The following keys are optional_:

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

1. If your `data` object above is a `module:attribute` string, don't forget to add
   the data in the `cmap/data/<namespace>/__init__.py` file.  For example:

    ```python
    my_colormap = [
        [0.468775, 0.468876, 0.468851],
        [0.473809, 0.47391, 0.473885],
        [0.478873, 0.478974, 0.478949],
        [0.483952, 0.484053, 0.484028],
        ...
    ]
    ```

1. Run `scripts/make_cmapnames.py` to ensure that the `ColormapLike` type alias
   includes your contribution.
   `pre-commit` will update it for you, but will fail if changes were made.

!!!tip
    It may be helpful to look at existing folders and files in the
    [`cmap/data` directory](https://github.com/pyapp-kit/cmap/tree/main/src/cmap/data)
    for examples of how to structure the data

When opening a PR, please include a screenshot of the colormap, along
with a brief description of the colormap design and its intended use.

!!!info "Licensing"
    Please ensure that the colormap you are adding is available
    under a permissive license.  Note that namespaces share a license, so if you
    are adding a colormap to an existing namespace, make sure that the
    colormap is compatible with the existing license.  New licenses may be added
    to the `LICENSES` directory at the root of the repo.  If you are unsure
    about licensing, please open an issue.

## How can I add support for exporting to another colormap format?

cmap [exports to a variety of known third-party colormap
formats](colormaps.md#usage-with-external-visualization-libraries).

If you are the author (or user) of a library that consumes colormaps, and you
would like to have a `to_your_lib()` function in `cmap`, we welcome
contributions!

Have a look at `_external.py` for examples of how to add support for your
format.

## Don't we already have enough colormap libraries?

Perhaps!  But maybe just one more? :joy:

The primary driver for this
was to create a dependency-free library (save numpy) that could be used
in a variety of visualization libraries.  We will never depend on anything
outside of numpy, and we export to a variety of third-party colormaps.

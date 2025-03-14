# Overview

`cmap` is a colormap library for python, providing all of the colormaps in
matplotlib, vispy, cmocean, (and more), with no dependencies beyond numpy.

## Purpose

Mapping scalar values to colors is a very common procedure in scientific
visualization; as such, many visualization libraries (e.g. matplotlib, vispy,
pygfx, etc...) have some need for and some internal representation of colors
and colormaps.

!!!question "Don't we already have this?"
    Many libraries that use colormaps end up either directly depending on
    matplotlib, vendoring just the colors module or colormap data, or reimplementing
    a colormapping solution internally (even if it's not the core purpose of the
    library).

    This library attempts to avoid the need for that duplication, aiming to provide
    a comprehensive, **dependency-free** (except numpy) collection of colormaps; and
    an API for using these colormaps in a wide variety of third party libraries
    (beyond matplotlib).

**Specifically there are three goals:**

1. Accumulate colormap data from a variety of sources into a single repository.
2. Provide an API for creating and applying colormaps *without* any dependencies
   beyond numpy. (by "applying" here, we mean converting an array of scalar
   values to an array of RGBA values)
3. Provide an API for converting colormaps to the native format for a variety of
   third party libraries (currently including, matplotlib, napari, vispy, pygfx,
   bokeh, plotly, altair, and more)

## Colormaps

For a complete list of available colormaps, see the [Colormaps
catalog](catalog/index.md). You can also use the search bar at the top to search
for a specific colormap.

For details on using the `cmap.Colormap` object, see [Colormaps](colormaps.md).

## Colors

This library also offers a simple `cmap.Color` object.  It can cast a variety of
inputs (including strings, tuples/lists, arrays, integers) to an RGBA color
representation, and offers some basic conversions.  See [Colors](colors.md) for
details

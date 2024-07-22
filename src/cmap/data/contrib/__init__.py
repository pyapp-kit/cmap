"""Namespace for colormaps contributed by the community.

For example, to add a new colormap here, first define the data in this file
(or in a new file in this directory, imported here). Even-spaced colormaps are
best expressed as a list of RGB triplets, for example:


    my_colormap = [
        [0.468775, 0.468876, 0.468851],
        [0.473809, 0.47391, 0.473885],
        [0.478873, 0.478974, 0.478949],
        [0.483952, 0.484053, 0.484028],
        ...
    ]

However, if you have a more complicated colormap, you can define it as a any
[`ColormapLike` object](https://cmap-docs.readthedocs.io/en/stable/colormaps/#colormaplike-objects)

Then update `contrib/record.json`, adding a new item to the `colormaps` dict,
with a pointer to your data (`module:attribute`), and assign it to a category.
For example:

    {
        "authors": [
            "Jane Doe"  # add your name to the authors list
        ],
        "colormaps": {
            "my_colormap": {
                "category": "sequential",
                "data": "cmap.data.contrib:my_colormap"
            }
        },
        ...
    }

Each colormap object may also have any of the following optional attributes:

    tags: list[str]       A list of tags to help categorize the colormap.
                          These appear on the website.
    info: str             A brief description of the colormap.
                          This appears on the website.
    interpolation: bool   Whether the colormap should be interpolated,
                          between stops. default is True.
    aliases: list[str]    A list of alternative names for the colormap.
    over: str             Color to show when values are over the range.
    under: str            Color to show when values are under the range.
    bad: str              Color to show when values are NaN or masked.

"""

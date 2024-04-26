"""color-jitter module from Quorumetrix, Tyler Sloan.

https://github.com/Quorumetrix/color_jitter/blob/d682f94d097aa300913e968d6771335df5c2c053/color_jitter.py

MIT License

Copyright (c) 2024 Quorumetrix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import colorsys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# Define the Nightingale color palette in HEX
nightingale_palette = {
    "Bauhaus blue": "#2C5AA0",
    "Bauhaus red": "#F93F17",
    "Bauhaus yellow": "#FFED00",
    "70s orange": "#FF8E00",
    "70s pink": "#FFC5E5",
    "Modern green": "#5A7247",
    "Modern violet": "#926AA6",
    "Modern blue": "#7EBDC2",
}

# Define the Tableau 10 color palette in HEX
tableau_10_palette = {
    "blue": "#4E79A7",
    "orange": "#F28E2B",
    "green": "#59A14F",
    "red": "#E15759",
    "purple": "#B07AA1",
    "brown": "#9C755F",
    "pink": "#FABFD2",
    "gray": "#BAB0AC",
    "olive": "#8CD17D",
    "cyan": "#86BCB6",
}


def rgb_to_hsv_color_wheel(rgb_colors):
    """
    Convert a list of RGB colors to their positions on an HSV color wheel.

    Parameters
    ----------
    - rgb_colors: Array of RGB colors with shape (n, 3).

    Returns
    -------
    - A tuple containing two arrays: angles (in radians) and radii for the polar plot.
    """
    hsv_colors = np.array([colorsys.rgb_to_hsv(*color) for color in rgb_colors])
    hues = hsv_colors[:, 0]  # Hue component
    saturations = hsv_colors[:, 1]  # Saturation component

    # Convert hue to angle (in radians) and saturation to radius
    angles = hues * 2 * np.pi
    radii = saturations

    return angles, radii


def apply_hue_jitter_rgb(rgb_color, intensity):
    """
    Apply jitter to an RGB color.
    Args:
        rgb_color (numpy.ndarray): RGB color as a numpy array.
        intensity (float): Intensity of the jitter to apply.

    Returns
    -------
        numpy.ndarray: Jittered RGB color.
    """
    jitter = intensity * (2 * np.random.rand(3) - 1)
    jittered_rgb = np.clip(rgb_color + jitter, 0, 1)
    return jittered_rgb


def color_wheel_plot(
    n_categories: int,
    colormap=plt.cm.Spectral,
    custom_palette=None,
    n_jitter_samples=50,
    color_jitter=0,
    cmap_samples=0,
    colorspace_samples=50000,
):  # , min_brightness=0.2, max_brightness=1.0):
    if custom_palette is not None:
        cmap_samples = 0

    # Initialize the polar plot
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 8), dpi=300)

    # Plot the overall RGB color space
    if colorspace_samples > 0:
        color_space = np.random.rand(colorspace_samples, 3)  # Sample from the RGB cube
        angles_space, radii_space = rgb_to_hsv_color_wheel(color_space)
        ax.scatter(
            angles_space, radii_space, c=color_space, alpha=0.2, s=5, linewidth=0
        )

    # Determine the color palette to use
    if custom_palette:
        if len(custom_palette) < n_categories:
            raise ValueError(
                "The custom palette has fewer colors than the number of categories."
            )
        colors = list(custom_palette.values())[:n_categories]
    else:
        colors = colormap(np.linspace(0, 1, n_categories))

    if cmap_samples > 0:
        # Plot the colormap if specified
        cmap_colors = colormap(np.linspace(0, 1, cmap_samples))
        rgb_cmap_colors = cmap_colors[:, :3]  # Discard the alpha channel if present
        angles_cmap, radii_cmap = rgb_to_hsv_color_wheel(rgb_cmap_colors)
        ax.scatter(
            angles_cmap, radii_cmap, c=cmap_colors, alpha=0.5, s=1, linewidth=0.0
        )

        # Plotting line segments to represent transitions in the colormap
        for i in range(len(angles_cmap) - 1):
            ax.plot(
                [angles_cmap[i], angles_cmap[i + 1]],
                [radii_cmap[i], radii_cmap[i + 1]],
                color=rgb_cmap_colors[i],
                linewidth=1,
                alpha=0.5,
            )

    if n_categories > 0:
        rgb_colors = (
            colors[:, :3]
            if isinstance(colors, np.ndarray)
            else [matplotlib.colors.to_rgb(color) for color in colors]
        )

        if color_jitter > 0:
            # Plot jittered points for each color
            for rgb_color in rgb_colors:
                jittered_colors = np.array(
                    [
                        apply_hue_jitter_rgb(rgb_color, color_jitter)
                        for _ in range(n_jitter_samples)
                    ]
                )
                jittered_angles, jittered_radii = rgb_to_hsv_color_wheel(
                    jittered_colors
                )
                ax.scatter(
                    jittered_angles,
                    jittered_radii,
                    c=jittered_colors,
                    alpha=1,
                    s=50,
                    edgecolors="black",
                    linewidths=0.1,
                )

        # Plot the color palette (as points and/or lines)
        angles_palette, radii_palette = rgb_to_hsv_color_wheel(rgb_colors)
        ax.scatter(
            angles_palette,
            radii_palette,
            c=rgb_colors,
            alpha=1,
            s=250,
            edgecolors="black",
            linewidths=0.1,
        )

    # Configure plot appearance
    ax.set_rlim(0, max(radii_space) if colorspace_samples > 0 else 1)
    ax.grid(False)
    ax.set_yticklabels([])
    ax.set_xticklabels([])

    plt.show()


# The function to generate the color map, now updated to handle a custom palette if provided
def generate_color_map(
    categories, custom_palette=None, colormap=plt.cm.tab10, use_full_range=True
):
    if custom_palette:
        # Use the custom color palette if provided
        return custom_palette
    elif use_full_range:
        # Create a color map with a distinct color for each category from the specified colormap
        colors = colormap(np.linspace(0, 1, len(categories)))
    else:
        # Use the first N colors from the colormap
        colors = colormap(np.arange(len(categories)) / len(categories))

    # Convert colors to hexadecimal format
    hex_colors = [
        "#" + "".join([f"{int(c*255):02X}" for c in color[:3]]) for color in colors
    ]
    return dict(zip(categories, hex_colors))


# The function to apply jitter to a hex color, generating a new jittered hex color
def apply_hue_jitter(hex_color, intensity):
    # Convert hex to RGB
    rgb = np.array([int(hex_color[i : i + 2], 16) for i in (1, 3, 5)])

    # Apply jitter
    jitter = intensity * (2 * np.random.rand(3) - 1) * 255
    jittered_rgb = np.clip(rgb + jitter, 0, 255).astype(int)

    # Convert back to hex
    return "#" + "".join([f"{val:02X}" for val in jittered_rgb])


# The main plotting function with hue jitter and accepting a custom color palette
def colorjitter_scatterplot(
    df,
    x_var,
    y_var,
    category_var,
    jitter_intensity=0.5,
    point_size=5,
    opacity=0.8,
    custom_palette=None,
    use_full_range=True,
    plot_title=None,
    legend_marker_size=10,
    x_label=None,
    y_label=None,
):
    # def colorjitter_scatterplot(df, x_var, y_var, category_var, jitter_intensity=0.5, point_size=5, opacity=0.8, custom_palette=None, use_full_range=True, plot_title=None, legend_marker_size=10):
    # Ensure the category variable is converted to Categorical with the desired order
    if not pd.api.types.is_categorical_dtype(df[category_var]):
        df[category_var] = pd.Categorical(df[category_var], ordered=True)
    categories = df[category_var].cat.categories

    # Generate color map based on the ordered categories and the specified colormap or custom palette
    color_map = generate_color_map(
        categories, custom_palette=custom_palette, use_full_range=use_full_range
    )

    # Create a figure and axis for plotting
    fig, ax = plt.subplots(
        figsize=(8, 8), dpi=300
    )  # Set the figure size and dpi for high resolution

    for (
        category
    ) in categories:  # Iterates in the order defined in the Categorical dtype
        group = df[df[category_var] == category]
        jittered_colors = [
            apply_hue_jitter(color_map[category], jitter_intensity)
            for _ in range(len(group))
        ]
        ax.scatter(
            group[x_var],
            group[y_var],
            color=jittered_colors,
            s=point_size,
            alpha=opacity,
            label=category,
            edgecolors="none",
        )

    # Create custom legend handles with the specified marker size
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color=color_map[category],
            label=category,
            linestyle="None",
            markersize=legend_marker_size,
        )
        for category in categories
    ]

    ax.legend(handles=legend_handles, title=category_var)
    ax.set_title(
        plot_title
        if plot_title
        else f"Categorical Scatterplot of {x_var} vs. {y_var} with Hue Jitter",
        fontsize=20,
    )
    ax.set_xlabel(x_label if x_label else x_var, fontsize=14)
    ax.set_ylabel(y_label if y_label else y_var, fontsize=14)

    # Save the figure with high quality
    plt.show()

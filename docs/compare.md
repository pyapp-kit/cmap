---
title: Compare colormaps
description: Compare colormaps side by side, including perceptual lightness and simulated color vision deficiencies.
---

# Compare colormaps

Add up to six colormaps from the [catalog](catalog/index.md) to compare them
side by side.
Each colormap is shown as a colorbar and applied to a
[sine ramp](https://arxiv.org/abs/1509.03700) test image: in a good colormap,
the sine wave at the top should be equally visible across the whole range.
Below that, each colormap is applied to a sample image, or to one of your own,
and the chart at the bottom shows the perceptual lightness of each colormap.

The URL updates as you go, so you can share a comparison.

<div class="cmap-compare" data-base="../catalog/_data/" markdown>

<div class="cmap-compare-controls">
<form class="cmap-compare-form">
<input class="cmap-compare-input" list="cmap-compare-names" placeholder="Add a colormap…" aria-label="Colormap name" autocomplete="off">
<datalist id="cmap-compare-names"></datalist>
<button type="submit" class="md-button md-button--primary">Add</button>
</form>
<fieldset class="cmap-pills cmap-cvd" role="radiogroup" aria-label="Simulate color vision deficiency">
<label><input type="radio" name="cvd" value="normal" checked><span>Normal vision</span></label>
<label><input type="radio" name="cvd" value="protan"><span title="Simulates missing L (long-wavelength, red) cones"><span class="cmap-cvd-cone" aria-hidden="true">L</span>Protanopia</span></label>
<label><input type="radio" name="cvd" value="deutan"><span title="Simulates missing M (medium-wavelength, green) cones"><span class="cmap-cvd-cone" aria-hidden="true">M</span>Deuteranopia</span></label>
<label><input type="radio" name="cvd" value="tritan"><span title="Simulates missing S (short-wavelength, blue) cones"><span class="cmap-cvd-cone" aria-hidden="true">S</span>Tritanopia</span></label>
</fieldset>
</div>

## Colorbars

<div class="cmap-compare-rows"></div>

## Image

<div class="cmap-image">
<div class="cmap-image-drop">
<label class="md-button cmap-image-pick">Choose image…<input type="file" accept="image/*" hidden></label>
<fieldset class="cmap-pills cmap-image-samples" role="radiogroup" aria-label="Sample image">
<label><input type="radio" name="sample" value="cat" data-image="../images/cat.jpg" checked><span title="A sweet gray cat. Perceptually uniform cuteness, no meaningful midpoint. Best for sequential colormaps, and for being happy">Cat</span></label>
<label><input type="radio" name="sample" value="corsica" data-image="../images/corsica.png"><span title="Land and seafloor heights, with sea level at the middle: best for diverging colormaps">Corsica</span></label>
</fieldset>
<span class="cmap-image-name" hidden></span>
<button type="button" class="cmap-image-reset" title="Back to the sample image" aria-label="Back to the sample image" hidden>✕</button>
<label class="cmap-image-stretch" hidden><input type="checkbox" checked><span title="Stretch the 1st to 99th percentile of the image's values to the full colormap">Stretch contrast</span></label>
<span class="cmap-image-hint">Or drop or paste an image here. It's converted to grayscale and stays in your browser: nothing is uploaded.</span>
</div>
<div class="cmap-image-grid"></div>
<p class="cmap-image-credit" data-sample="cat">Sample: a cat in crumpled paper, with fine detail (fur, whiskers) and smooth shading (paper). It has no meaningful middle value: for diverging colormaps, use Corsica.</p>
<p class="cmap-image-credit" data-sample="corsica" hidden>Sample: land and seafloor heights (−2759 to +2532 m), scaled so that sea level is the middle of each colormap. Data from NOAA's <a href="https://doi.org/10.25921/fd45-gt74">ETOPO 2022 Global Relief Model</a> (CC0).</p>
</div>

## Lightness

<fieldset class="cmap-pills cmap-line-colors" role="radiogroup" aria-label="Line colors">
<label><input type="radio" name="line-colors" value="colormap" checked><span title="Color each line by its colormap">Colormap colors</span></label>
<label><input type="radio" name="line-colors" value="distinct"><span title="Give each line its own distinct color (petroff:petroff6)">Distinct colors</span></label>
</fieldset>
<div class="cmap-chart-wrap"><canvas class="cmap-chart" data-chart="compare" role="img" aria-label="Lightness of each compared colormap"></canvas></div>

</div>

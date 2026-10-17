---
title: Compare colormaps
description: Compare colormaps side by side, including perceptual lightness and simulated color vision deficiencies.
---

# Compare colormaps

Add colormaps from the [catalog](catalog/index.md) to compare them side by side.
Each colormap is shown as a colorbar and applied to a
[sine ramp](https://www.peterkovesi.com/matlabfns/) test image: in a good colormap,
the sine wave at the top should be equally visible across the whole range. The
chart below shows the perceptual lightness of each colormap.

The URL updates as you go, so you can share a comparison.

<div class="cmap-compare" data-base="../catalog/_data/">
<form class="cmap-compare-form">
<input class="cmap-compare-input" list="cmap-compare-names" placeholder="Add a colormap…" aria-label="Colormap name" autocomplete="off">
<datalist id="cmap-compare-names"></datalist>
<button type="submit" class="md-button md-button--primary">Add</button>
</form>
<fieldset class="cmap-cvd" role="radiogroup" aria-label="Simulate color vision deficiency">
<label><input type="radio" name="cvd" value="normal" checked><span>Normal vision</span></label>
<label><input type="radio" name="cvd" value="protan"><span>Protanopia</span></label>
<label><input type="radio" name="cvd" value="deutan"><span>Deuteranopia</span></label>
<label><input type="radio" name="cvd" value="tritan"><span>Tritanopia</span></label>
</fieldset>
<div class="cmap-compare-rows"></div>
<div class="cmap-chart-wrap"><canvas class="cmap-chart" data-chart="compare"></canvas></div>
</div>

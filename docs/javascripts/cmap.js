// Interactive bits of the cmap docs. Data comes from docs/_gen_catalog.py.
// Everything is (re-)initialized on each page load via `document$`, which
// zensical emits on initial load and on every instant navigation.

const CVD_TYPES = ["normal", "protan", "deutan", "tritan"];
const dataCache = new Map();

document$.subscribe(() => {
  document.querySelectorAll(".cmap-catalog").forEach(initCatalogFilter);
  document.querySelectorAll(".cmap-detail").forEach(initDetail);
  document.querySelectorAll(".cmap-compare").forEach(initCompare);
});

// re-render charts when the color scheme changes
new MutationObserver(() => {
  for (const canvas of document.querySelectorAll("canvas.cmap-chart")) {
    canvas.dispatchEvent(new Event("cmap:rerender"));
  }
}).observe(document.body, { attributeFilter: ["data-md-color-scheme"] });

// ---------------------------------------------------------------------------
// Data helpers
// ---------------------------------------------------------------------------

function fetchData(url) {
  url = String(url); // (URL objects are compared by identity)
  if (!dataCache.has(url)) {
    dataCache.set(
      url,
      fetch(url)
        .then((r) => {
          if (!r.ok) throw new Error(`${r.status} fetching ${url}`);
          return r.json();
        })
        .catch((err) => {
          dataCache.delete(url); // (so that it's retried next time)
          throw err;
        })
    );
  }
  return dataCache.get(url);
}

// Replace the contents of `el` with an error message.
function showError(el, message) {
  el.replaceChildren(Object.assign(document.createElement("p"), { className: "cmap-error", textContent: message }));
}

// A colormap's data (one CVD type), for the reversed colormap.
function reverseData(d) {
  const reversed = (k, v) => (k === "dJ" ? v.map((x) => (x == null ? x : -x)) : [...v]).reverse();
  return Object.fromEntries(Object.entries(d).map(([k, v]) => [k, reversed(k, v)]));
}

const hexToRgb = (hex) => [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16));
const linspace = (n) => Array.from({ length: n }, (_, i) => (n > 1 ? i / (n - 1) : 0));

// Port of cmap._util.sineramp(...)[:, ::-1] (Peter Kovesi's test image), values in
// [0, 1].
function sineramp([rows, cols], amp = 0.05, wavelen = 8, power = 2) {
  cols = Math.round(cols / wavelen) * wavelen;
  const im = new Float32Array(rows * cols);
  for (let r = 0; r < rows; r++) {
    const a = ((rows - 1 - r) / (rows - 1)) ** power;
    let min = Infinity;
    let max = -Infinity;
    for (let c = 0; c < cols; c++) {
      const v =
        a * amp * Math.sin((2 * Math.PI * c) / wavelen) + (c / (cols - 1)) * -2 * amp;
      // columns are flipped so that the ramp goes from low to high, left to right
      im[r * cols + (cols - 1 - c)] = v;
      min = Math.min(min, v);
      max = Math.max(max, v);
    }
    for (let c = 0; c < cols; c++) {
      im[r * cols + c] = (im[r * cols + c] - min) / (max - min);
    }
  }
  return { im, rows, cols };
}

// Port of Peter Kovesi's circlesineramp: test image for cyclic colormaps. A sine
// wave on a spiral ramp, values in [0, 1], NaN outside the annulus.
// https://codeberg.org/peterkovesi/matlabfns/src/branch/main/Misc/circlesineramp.m
function circlesineramp(size = 320, amp = Math.PI / 10, wavelen = 8, power = 2) {
  const maxr = (size / 2) * 0.9;
  const minr = 0.15 * size;
  const cycles = Math.round((2 * Math.PI * ((maxr + minr) / 2)) / wavelen);
  const im = new Float32Array(size * size);
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      const x = col - size / 2;
      const y = row - size / 2;
      const theta = (Math.atan2(-y, x) + 2 * Math.PI) % (2 * Math.PI);
      const rad = (Math.hypot(x, y) - minr) / (maxr - minr);
      const v = amp * rad ** power * Math.sin(cycles * theta) + theta;
      const wrapped = ((v % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
      im[row * size + col] = rad < 0 || rad > 1 ? NaN : wrapped / (2 * Math.PI);
    }
  }
  return { im, rows: size, cols: size };
}

// MATLAB's `peaks` surface over [-3, 3]^2, scaled so that 0 maps to the middle of
// the colormap (for diverging colormaps).
// https://www.mathworks.com/help/matlab/ref/peaks.html
function peaks(size = 320) {
  const z = new Float32Array(size * size);
  let absmax = 0;
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      const x = -3 + (6 * col) / (size - 1);
      const y = 3 - (6 * row) / (size - 1);
      const v =
        3 * (1 - x) ** 2 * Math.exp(-(x ** 2) - (y + 1) ** 2) -
        10 * (x / 5 - x ** 3 - y ** 5) * Math.exp(-(x ** 2) - y ** 2) -
        (1 / 3) * Math.exp(-((x + 1) ** 2) - y ** 2);
      z[row * size + col] = v;
      absmax = Math.max(absmax, Math.abs(v));
    }
  }
  for (let i = 0; i < z.length; i++) z[i] = 0.5 + z[i] / (2 * absmax);
  return { im: z, rows: size, cols: size };
}

// Test images are generated at their displayed size in device pixels (`s` per CSS
// pixel), so the 8px wavelength of the sine patterns is the same in every layout.
const TEST_IMAGES = {
  sineramp: (rows, cols, s) => sineramp([rows, cols], 0.05, 8 * s),
  circlesineramp: (rows, cols, s) => circlesineramp(Math.min(rows, cols), Math.PI / 10, 8 * s),
  peaks: (rows, cols) => peaks(Math.min(rows, cols)),
};
const _testImages = new Map();
function getTestImage(kind, rows, cols, s) {
  const key = `${kind}:${rows}x${cols}`;
  if (_testImages.get(kind)?.key !== key) {
    _testImages.set(kind, { key, value: TEST_IMAGES[kind](rows, cols, s) });
  }
  return _testImages.get(kind).value;
}

const testImageColors = new WeakMap();
const testImageObserver = new ResizeObserver((entries) => {
  for (const { target } of entries) paintTestImage(target);
});

// Paint `canvas` (with a `data-test-image` kind) through `colors`, now and on resize.
function setTestImageColors(canvas, colors) {
  testImageColors.set(canvas, colors);
  testImageObserver.observe(canvas);
  paintTestImage(canvas);
}

function paintTestImage(canvas) {
  const s = Math.max(1, Math.round(window.devicePixelRatio || 1));
  const rows = Math.round(canvas.clientHeight * s);
  const cols = Math.round(canvas.clientWidth * s);
  if (!rows || !cols) return; // not laid out yet: the ResizeObserver will repaint
  const { im, rows: r, cols: c } = getTestImage(canvas.dataset.testImage, rows, cols, s);
  paint(canvas, testImageColors.get(canvas), im, r, c);
}

// The runs of identical colors in a (discrete) colormap's samples: each with its
// color, its J′ and the x at its middle.
function colorRuns(d) {
  const runs = [];
  d.color.forEach((c, i) => {
    const last = runs.at(-1);
    if (last && last.color === c) last.end = i;
    else runs.push({ color: c, start: i, end: i });
  });
  const n = Math.max(d.color.length - 1, 1);
  return runs.map((r) => ({
    color: `#${r.color}`,
    x: (r.start + r.end) / 2 / n,
    J: d.J[Math.floor((r.start + r.end) / 2)],
  }));
}

// The smallest 1, 2 or 5 (times a power of 10) that is >= `v`.
function niceCeil(v) {
  if (!(v > 0)) return 1;
  const p = 10 ** Math.floor(Math.log10(v));
  return [1, 2, 5, 10].map((m) => m * p).find((s) => s >= v);
}

// Paint values in [0, 1] (row-major, `rows` x `cols`) through the LUT `colors`.
function paint(canvas, colors, values, rows, cols) {
  const lut = colors.map(hexToRgb);
  const n = lut.length;
  canvas.width = cols;
  canvas.height = rows;
  const ctx = canvas.getContext("2d");
  const img = ctx.createImageData(cols, rows);
  for (let i = 0; i < values.length; i++) {
    if (Number.isNaN(values[i])) continue; // leave transparent
    const [r, g, b] = lut[Math.max(0, Math.min(n - 1, Math.floor(values[i] * n)))];
    img.data.set([r, g, b, 255], i * 4);
  }
  ctx.putImageData(img, 0, 0);
}

function paintBar(canvas, colors, width = 826) {
  paint(canvas, colors, linspace(width), 1, width);
}

// ---------------------------------------------------------------------------
// Catalog grid filtering
// ---------------------------------------------------------------------------

function initCatalogFilter(root) {
  if (root.dataset.ready) return;
  root.dataset.ready = "1";
  const text = root.querySelector(".cmap-filter-text");
  const ns = root.querySelector(".cmap-filter-ns"); // (absent on collection pages)
  const mono = root.querySelector(".cmap-filter-mono input");
  const catButtons = [...root.querySelectorAll(".cmap-filter-cats button")];
  const count = root.querySelector(".cmap-filter-count");
  const empty = root.querySelector(".cmap-empty");
  const items = [...root.querySelectorAll(".cmap-grid > .cmap")];
  let category = "all";

  // the filters are kept in the URL, so that a filtered view can be linked to:
  // ?q=<text>&collection=<namespace>&category=<category>&monotonic=1
  const params = new URLSearchParams(location.search);
  text.value = params.get("q") ?? "";
  if (ns && [...ns.options].some((o) => o.value === params.get("collection"))) {
    ns.value = params.get("collection");
  }
  mono.checked = params.get("monotonic") === "1";
  const requested = catButtons.find((b) => b.dataset.category === params.get("category"));
  if (requested) category = requested.dataset.category;
  catButtons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.category === category)));

  function syncUrl() {
    const url = new URL(location.href);
    const set = (key, value) =>
      value ? url.searchParams.set(key, value) : url.searchParams.delete(key);
    set("q", text.value.trim());
    set("collection", ns?.value);
    set("category", category === "all" ? "" : category);
    set("monotonic", mono.checked ? "1" : "");
    history.replaceState(history.state, "", url);
  }

  function apply() {
    const words = text.value.toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const el of items) {
      const d = el.dataset;
      const visible =
        (category === "all" || d.category === category) &&
        (!ns?.value || d.namespace === ns.value) &&
        (!mono.checked || d.monotonic === "1") &&
        words.every((w) => d.search.includes(w));
      el.hidden = !visible;
      shown += visible;
    }
    count.textContent = `${shown} of ${items.length} colormaps`;
    empty.hidden = shown > 0;
    syncUrl();
  }

  for (const btn of catButtons) {
    btn.addEventListener("click", () => {
      category = btn.dataset.category;
      catButtons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
      apply();
    });
  }
  text.addEventListener("input", apply);
  ns?.addEventListener("change", apply);
  mono.addEventListener("change", apply);
  apply();
}

// ---------------------------------------------------------------------------
// Colormap detail page
// ---------------------------------------------------------------------------

async function initDetail(root) {
  if (root.dataset.ready) return;
  root.dataset.ready = "1";
  const name = root.dataset.cmapName;
  let data;
  try {
    data = await fetchData(new URL(root.dataset.json, location.href));
  } catch (err) {
    const message = document.createElement("div");
    showError(message, `Couldn't load this colormap's data (${err.message})`);
    root.prepend(message);
    return;
  }
  const bars = [...root.querySelectorAll(".cmap > img")];
  const originals = bars.map((img) => img.src);
  const testImages = [...root.querySelectorAll("canvas[data-test-image]")];
  const charts = [...document.querySelectorAll(`canvas.cmap-chart[data-cmap-name="${name}"]`)];

  function render(cvd) {
    const d = data[cvd] ?? data.normal;
    if (cvd === "normal") {
      bars.forEach((img, i) => (img.src = originals[i]));
    } else {
      const tmp = document.createElement("canvas");
      paintBar(tmp, d.color);
      const url = tmp.toDataURL();
      bars.forEach((img) => (img.src = url));
    }
    for (const canvas of testImages) setTestImageColors(canvas, d.color);
    for (const canvas of charts) drawChart(canvas, d);
  }

  // (only the charts depend on the color scheme)
  for (const canvas of charts) {
    canvas.addEventListener("cmap:rerender", () =>
      drawChart(canvas, data[currentCvd()] ?? data.normal)
    );
  }
  const currentCvd = () => root.querySelector('.cmap-cvd input:checked')?.value ?? "normal";
  root.querySelector(".cmap-cvd").addEventListener("change", () => render(currentCvd()));
  render(currentCvd());
}

// ---------------------------------------------------------------------------
// Charts
// ---------------------------------------------------------------------------

function themeColors() {
  const style = getComputedStyle(document.body);
  return {
    fg: style.getPropertyValue("--md-default-fg-color--light").trim(),
    grid: style.getPropertyValue("--md-default-fg-color--lightest").trim(),
  };
}

function baseOptions(yScales) {
  const { fg, grid } = themeColors();
  const scales = { x: { type: "linear", min: 0, max: 1 }, ...yScales };
  for (const axis of Object.values(scales)) {
    axis.ticks = { color: fg, ...axis.ticks };
    axis.grid = { color: grid, ...axis.grid };
    if (axis.title) axis.title.color = fg;
  }
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        boxPadding: 4,
        // (point-style swatches: the default boxes have a white backing and outline)
        usePointStyle: true,
        callbacks: {
          title: (items) => `x = ${items[0].parsed.x.toFixed(3)}`,
          label: ({ dataset, parsed }) =>
            `${dataset.label}: ${parsed.y == null ? "–" : Number(parsed.y.toPrecision(3))}`,
          // a solid swatch of the line's color (or, for lines colored by the colormap,
          // of the color at that point)
          labelColor: ({ dataset, dataIndex }) => {
            let color = dataset.tooltipColors?.[dataIndex] ?? dataset.borderColor;
            if (typeof color !== "string") color = themeColors().fg;
            return { borderColor: color, backgroundColor: color, borderWidth: 0 };
          },
          labelPointStyle: () => ({ pointStyle: "rectRounded", rotation: 0 }),
        },
      },
    },
    scales,
  };
}

function points(xs, ys) {
  return ys.map((y, i) => ({ x: xs[i], y }));
}

function drawChart(canvas, d) {
  Chart.getChart(canvas)?.destroy();
  const x = linspace(d.color.length);
  const colors = d.color.map((c) => `#${c}`);
  const kind = canvas.dataset.chart;

  if (kind === "lightness" && "discrete" in canvas.dataset) {
    // a discrete colormap: one point per color, and no derivative
    const runs = colorRuns(d);
    new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: "J′",
            data: runs.map((r) => ({ x: r.x, y: r.J })),
            backgroundColor: runs.map((r) => r.color),
            tooltipColors: runs.map((r) => r.color),
            pointRadius: 10,
            pointHoverRadius: 12,
            borderWidth: 0,
            clip: false,
          },
        ],
      },
      options: baseOptions({
        y: { min: 0, max: 100, title: { text: "Lightness J′", display: true } },
      }),
    });
  } else if (kind === "lightness") {
    // symmetric derivative axis, fit to the data (ignoring the most extreme 2%)
    const dJ = d.dJ.filter(Number.isFinite).map(Math.abs).sort((a, b) => a - b);
    const dJmax = niceCeil(1.25 * (dJ[Math.floor(0.98 * (dJ.length - 1))] ?? 0));
    const options = baseOptions({
      y: { min: 0, max: 100, title: { text: "Lightness J′", display: true } },
      y2: {
        min: -dJmax,
        max: dJmax,
        position: "right",
        grid: { drawOnChartArea: false },
        title: { text: "Lightness derivative", display: true },
      },
    });
    new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: "J′",
            data: points(x, d.J),
            backgroundColor: colors,
            tooltipColors: colors,
            pointRadius: 10,
            pointHoverRadius: 12,
            borderWidth: 0,
            // (don't cut off the points near the top and bottom)
            clip: false,
          },
          {
            label: "dJ′",
            data: points(x, d.dJ),
            showLine: true,
            pointRadius: 0,
            borderColor: "#88888866",
            tooltipColors: Array(x.length).fill("#888888"),
            borderWidth: 3,
            yAxisID: "y2",
          },
        ],
      },
      options,
    });
  } else if (kind === "rgb") {
    const rgb = d.color.map(hexToRgb);
    const channel = (i, label, color) => ({
      label,
      data: points(x, rgb.map((c) => c[i] / 255)),
      showLine: true,
      pointRadius: 0,
      borderWidth: 4,
      borderColor: color,
    });
    new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: [
          channel(0, "red", "#DD2222BB"),
          channel(1, "green", "#22BB22BB"),
          channel(2, "blue", "#2255FFBB"),
        ],
      },
      options: baseOptions({
        y: { min: 0, max: 1, title: { text: "Component value", display: true } },
      }),
    });
  } else if (kind === "hsl") {
    const options = baseOptions({
      y: { min: 0, max: 100, title: { text: "Saturation / chroma", display: true } },
      y2: {
        min: 0,
        max: 360,
        position: "right",
        ticks: { stepSize: 60 },
        grid: { drawOnChartArea: false },
        title: { text: "Hue (degrees)", display: true },
      },
    });
    options.plugins.legend = {
      display: true,
      labels: { usePointStyle: true, pointStyle: "line", color: themeColors().fg },
    };
    const line = (label, ys, axis = "y") => ({
      label,
      data: points(x, ys),
      showLine: true,
      pointRadius: 0,
      borderWidth: 3,
      yAxisID: axis,
    });
    // break the hue line where it wraps around, instead of drawing a vertical line
    const hue = d.hue.map((h, i) => (i && Math.abs(h - d.hue[i - 1]) > 95 ? null : h));
    new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: [
          line("saturation", d.saturation),
          line("chroma", d.chroma),
          line("hue", hue, "y2"),
        ],
      },
      options,
    });
  }
}

// ---------------------------------------------------------------------------
// Compare page
// ---------------------------------------------------------------------------

const COMPARE_MAX = 6;
// one dash pattern per line, so lines can be told apart even when the colormaps are
// similar. (with round caps, each dash grows by the line width and each gap shrinks)
const COMPARE_DASHES = [[], [12, 10], [0.1, 9], [18, 9, 0.1, 9], [6, 9], [26, 10]];
const COMPARE_LINE_WIDTH = 5;
// petroff:petroff6 from the catalog: six colors chosen to stay distinguishable,
// including with color vision deficiencies (https://arxiv.org/abs/2107.02270)
const COMPARE_COLORS = ["5790FC", "F89C20", "E42536", "964A8B", "9C9CA1", "7A21DD"];

// A horizontal gradient through `colors`, spanning `x0` to `x1` on `ctx`.
function lutGradient(ctx, colors, x0, x1) {
  const gradient = ctx.createLinearGradient(x0, 0, x1, 0);
  const n = Math.max(colors.length - 1, 1);
  colors.forEach((c, i) => gradient.addColorStop(i / n, `#${c}`));
  return gradient;
}

// A small dashed line in the colormap's colors, for the chart legend.
function lineSwatch(colors, dash, width = 40, height = 10) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  const lineWidth = 4;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = "round";
  ctx.setLineDash(dash.map((d) => d * (lineWidth / COMPARE_LINE_WIDTH)));
  ctx.strokeStyle = lutGradient(ctx, colors, 0, width);
  ctx.beginPath();
  ctx.moveTo(lineWidth / 2, height / 2);
  ctx.lineTo(width - lineWidth / 2, height / 2);
  ctx.stroke();
  return canvas;
}

// user images are scaled down to at most this many pixels on their long edge
const IMAGE_MAX = 768;
const GRAY = Array.from({ length: 256 }, (_, i) => i.toString(16).padStart(2, "0").repeat(3));

// The image at `src` as values in [0, 1] (NaN where transparent).
async function loadImage(src) {
  // (an <img> decodes anything the browser can show, SVG included)
  const img = new Image();
  img.src = src;
  await img.decode();
  const { naturalWidth: width, naturalHeight: height } = img;
  if (!width || !height) throw new Error(`${src} has no size`);
  const scale = Math.min(1, IMAGE_MAX / Math.max(width, height));
  const cols = Math.max(1, Math.round(width * scale));
  const rows = Math.max(1, Math.round(height * scale));
  const canvas = Object.assign(document.createElement("canvas"), { width: cols, height: rows });
  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, 0, 0, cols, rows);
  const px = ctx.getImageData(0, 0, cols, rows).data;
  const im = new Float32Array(rows * cols);
  for (let i = 0; i < im.length; i++) {
    const [r, g, b, a] = px.subarray(i * 4, i * 4 + 4);
    // (luma of the encoded values, so that a grayscale image keeps its own values)
    im[i] = a ? (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 : NaN;
  }
  return { im, rows, cols, width, height };
}

// `image` with its 1st to 99th percentile stretched to [0, 1].
function stretchContrast(image) {
  const sorted = image.im.filter((v) => !Number.isNaN(v)).sort();
  if (!sorted.length) return image;
  const lo = sorted[Math.floor(0.01 * (sorted.length - 1))];
  const hi = sorted[Math.ceil(0.99 * (sorted.length - 1))];
  if (!(hi > lo)) return image;
  const im = image.im.map((v) => Math.min(1, Math.max(0, (v - lo) / (hi - lo))));
  return { ...image, im };
}

async function initCompare(root) {
  if (root.dataset.ready) return;
  root.dataset.ready = "1";
  const base = new URL(root.dataset.base, location.href);
  let index;
  try {
    index = await fetchData(new URL("index.json", base));
  } catch (err) {
    showError(root.querySelector(".cmap-compare-rows"), `Couldn't load the catalog (${err.message})`);
    return;
  }
  const byName = new Map(index.map((e) => [e.name.toLowerCase(), e]));
  for (const e of index) {
    for (const a of e.aliases) byName.set(a.toLowerCase(), e);
  }

  const input = root.querySelector(".cmap-compare-input");
  const list = root.querySelector("datalist");
  list.replaceChildren(
    ...index.map((e) => Object.assign(document.createElement("option"), { value: e.name }))
  );
  const rowsEl = root.querySelector(".cmap-compare-rows");
  const chart = root.querySelector("canvas.cmap-chart");
  const cvdGroup = root.querySelector(".cmap-cvd");
  const params = new URLSearchParams(location.search);
  // a colormap name or alias (optionally reversed, with "_r") to
  // { name, entry, reversed }, or undefined if it isn't in the catalog
  const resolve = (n) => {
    const key = n.trim().toLowerCase();
    const reversed = key.endsWith("_r") && !byName.has(key);
    const entry = byName.get(reversed ? key.slice(0, -2) : key);
    return entry && { name: entry.name + (reversed ? "_r" : ""), entry, reversed };
  };
  let selected = params.has("cmaps")
    ? params.get("cmaps").split(",").filter(Boolean).map(resolve).filter(Boolean)
    : ["bids:viridis", "cmocean:thermal", "crameri:batlow"].map(resolve);
  selected = selected.slice(0, COMPARE_MAX);

  const cvd = () => cvdGroup.querySelector("input:checked")?.value ?? "normal";
  const lineColorsGroup = root.querySelector(".cmap-line-colors");
  // the colors of the i-th line: its colormap's, or one distinct color
  const lineColors = (data, i) =>
    lineColorsGroup.querySelector("input:checked")?.value === "distinct"
      ? [COMPARE_COLORS[i % COMPARE_COLORS.length]]
      : (data[cvd()] ?? data.normal).color;

  function syncUrl() {
    const url = new URL(location.href);
    url.searchParams.delete("cmaps");
    // (":" and "," are fine in a query string, and easier to read unescaped)
    const cmaps = selected.map((s) => encodeURIComponent(s.name).replace(/%3A/gi, ":"));
    url.search += `${url.search ? "&" : "?"}cmaps=${cmaps.join(",")}`;
    history.replaceState(history.state, "", url);
  }

  // the catalog data of a selected colormap (reversed, for a reversed colormap)
  async function loadData(s) {
    const file = `${encodeURIComponent(s.entry.path.split("/").pop())}.json`;
    const data = await fetchData(new URL(file, base));
    if (!s.reversed) return data;
    return Object.fromEntries(Object.entries(data).map(([k, d]) => [k, reverseData(d)]));
  }

  // The image section: a sample image, or one of the user's own, shown in grayscale
  // and through each colormap.
  const imageEl = root.querySelector(".cmap-image");
  const imageGrid = imageEl.querySelector(".cmap-image-grid");
  const imageName = imageEl.querySelector(".cmap-image-name");
  const imageFile = imageEl.querySelector("input[type=file]");
  const imageReset = imageEl.querySelector(".cmap-image-reset");
  const imageCredits = imageEl.querySelectorAll(".cmap-image-credit");
  const sampleGroup = imageEl.querySelector(".cmap-image-samples");
  const stretch = imageEl.querySelector(".cmap-image-stretch");
  const samples = new Map(); // sample name -> Promise of its image
  let sampleInput = sampleGroup.querySelector("input:checked");
  let sample = null; // (the image of `sampleInput`, once loaded)
  let userImage = null;
  let maps = []; // the colormaps as last rendered: [{ name, data }]

  function renderImages() {
    // (samples are never stretched: Corsica's middle value is sea level)
    const image = !userImage
      ? sample
      : stretch.querySelector("input").checked
        ? (userImage.stretched ??= stretchContrast(userImage))
        : userImage;
    if (userImage) {
      imageName.textContent = `${userImage.name} (${userImage.width}×${userImage.height})`;
    }
    imageName.hidden = imageReset.hidden = stretch.hidden = !userImage;
    for (const p of imageCredits) {
      p.hidden = !!userImage || p.dataset.sample !== sampleInput.value;
    }
    if (!image) return;
    const aspect = image.cols / image.rows;
    imageGrid.dataset.shape = aspect > 1.5 ? "wide" : aspect < 0.75 ? "tall" : "square";
    const tile = (name, colors) => {
      const el = document.createElement("div");
      el.className = "cmap-image-tile";
      const canvas = document.createElement("canvas");
      paint(canvas, colors, image.im, image.rows, image.cols);
      const label = Object.assign(document.createElement("span"), { textContent: name });
      el.append(canvas, label);
      return el;
    };
    imageGrid.replaceChildren(
      tile("grayscale", GRAY),
      ...maps.map(({ name, data }) => tile(name, (data[cvd()] ?? data.normal).color))
    );
  }

  async function setImage(file) {
    if (!file?.type.startsWith("image/")) return;
    const src = URL.createObjectURL(file);
    try {
      userImage = { ...(await loadImage(src)), name: file.name };
      sampleInput.checked = false;
    } catch {
      // (whatever was shown before stays shown)
      imageName.textContent = `Couldn't read ${file.name}`;
      imageName.hidden = false;
      return;
    } finally {
      URL.revokeObjectURL(src);
    }
    renderImages();
  }

  async function showSample(input) {
    sampleInput = input;
    input.checked = true;
    userImage = null;
    renderImages();
    if (!samples.has(input.value)) {
      samples.set(input.value, loadImage(new URL(input.dataset.image, location.href)));
    }
    const image = await samples.get(input.value);
    if (sampleInput !== input || userImage) return; // (something else was picked since)
    sample = image;
    renderImages();
  }
  showSample(sampleInput);

  sampleGroup.addEventListener("change", (ev) => showSample(ev.target));
  imageFile.addEventListener("change", () => {
    setImage(imageFile.files[0]);
    imageFile.value = ""; // (so that choosing the same file again still fires)
  });
  imageReset.addEventListener("click", () => showSample(sampleInput));
  stretch.addEventListener("change", renderImages);
  imageEl.addEventListener("dragover", (ev) => {
    ev.preventDefault();
    imageEl.classList.add("is-dragging");
  });
  imageEl.addEventListener("dragleave", (ev) => {
    if (!imageEl.contains(ev.relatedTarget)) imageEl.classList.remove("is-dragging");
  });
  imageEl.addEventListener("drop", (ev) => {
    ev.preventDefault();
    imageEl.classList.remove("is-dragging");
    setImage(ev.dataTransfer.files[0]);
  });
  // pasting an image anywhere on the page (until we navigate away from it)
  const onPaste = (ev) => {
    if (!root.isConnected) return document.removeEventListener("paste", onPaste);
    const file = [...ev.clipboardData.files].find((f) => f.type.startsWith("image/"));
    if (!file) return;
    ev.preventDefault();
    setImage(file);
  };
  document.addEventListener("paste", onPaste);

  function row({ name, entry, data }) {
    const d = data[cvd()] ?? data.normal;
    const el = document.createElement("div");
    el.className = "cmap-compare-row";
    const head = document.createElement("div");
    head.className = "cmap-compare-head";
    const link = Object.assign(document.createElement("a"), {
      href: new URL(`../${entry.path}/`, base).href,
      textContent: name,
    });
    const remove = Object.assign(document.createElement("button"), {
      type: "button",
      className: "cmap-compare-remove",
      title: `Remove ${name}`,
      textContent: "✕",
    });
    remove.setAttribute("aria-label", `Remove ${name}`);
    remove.addEventListener("click", () => {
      selected = selected.filter((s) => s.name !== name);
      render();
    });
    head.append(link, remove);
    const bar = document.createElement("canvas");
    bar.className = "cmap-compare-bar";
    paintBar(bar, d.color);
    el.append(head, bar);
    // (a sine ramp means nothing for a discrete colormap)
    if (!entry.discrete) {
      const sine = document.createElement("canvas");
      sine.className = "cmap-sineramp";
      sine.dataset.testImage = "sineramp";
      el.append(sine);
      setTestImageColors(sine, d.color);
    }
    return el;
  }

  function drawCompareChart() {
    Chart.getChart(chart)?.destroy();
    const options = baseOptions({
      y: { min: 0, max: 100, title: { text: "Lightness J′", display: true } },
    });
    // legend swatches are little dashed lines in each colormap's colors
    const swatches = maps.map(({ data }, i) => lineSwatch(lineColors(data, i), COMPARE_DASHES[i]));
    options.plugins.legend = {
      display: true,
      labels: {
        color: themeColors().fg,
        usePointStyle: true,
        pointStyleWidth: 40,
        boxHeight: 10,
        padding: 16,
        generateLabels: (c) =>
          Chart.defaults.plugins.legend.labels
            .generateLabels(c)
            .map((item, i) => ({ ...item, pointStyle: swatches[i] })),
      },
    };
    new Chart(chart, {
      type: "scatter",
      data: {
        datasets: maps.map(({ name, data }, i) => {
          const d = data[cvd()] ?? data.normal;
          const x = linspace(d.color.length);
          const colors = lineColors(data, i);
          return {
            label: name,
            data: points(x, d.J),
            showLine: true,
            pointRadius: 0,
            borderWidth: COMPARE_LINE_WIDTH,
            borderCapStyle: "round",
            borderDash: COMPARE_DASHES[i],
            tooltipColors: x.map((v) => `#${colors[Math.round(v * (colors.length - 1))]}`),
            // color the line by the colormap itself (one gradient for the whole line,
            // rather than per-segment colors, so that the dash pattern is continuous)
            borderColor: ({ chart }) => {
              const x0 = chart.scales.x?.getPixelForValue(0);
              const x1 = chart.scales.x?.getPixelForValue(1);
              // (before the first layout, there are no pixel positions yet)
              if (!Number.isFinite(x0) || !Number.isFinite(x1)) return `#${colors[0]}`;
              return lutGradient(chart.ctx, colors, x0, x1);
            },
          };
        }),
      },
      options,
    });
  }

  let renderId = 0;
  async function render() {
    syncUrl();
    const id = ++renderId;
    const shown = [...selected];
    let allData;
    try {
      allData = await Promise.all(shown.map(loadData));
    } catch (err) {
      if (id === renderId) showError(rowsEl, `Couldn't load colormap data (${err.message})`);
      return;
    }
    if (id !== renderId) return; // (the selection changed while loading: a newer render wins)
    maps = shown.map((s, i) => ({ ...s, data: allData[i] }));
    rowsEl.replaceChildren(...maps.map(row));
    renderImages();
    drawCompareChart();
  }

  // (only the chart depends on the color scheme)
  chart.addEventListener("cmap:rerender", drawCompareChart);
  cvdGroup.addEventListener("change", render);
  lineColorsGroup.addEventListener("change", drawCompareChart);
  // (a custom validity message blocks submitting the form until it's cleared)
  input.addEventListener("input", () => input.setCustomValidity(""));
  root.querySelector(".cmap-compare-form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const s = resolve(input.value);
    input.setCustomValidity(s ? "" : "Unknown colormap");
    input.reportValidity();
    if (!s) return;
    const isNew = !selected.some((x) => x.name === s.name);
    if (isNew && selected.length >= COMPARE_MAX) {
      input.setCustomValidity(`Up to ${COMPARE_MAX} colormaps: remove one first`);
      input.reportValidity();
      return;
    }
    if (isNew) selected = [...selected, s];
    input.value = "";
    render();
  });
  render();
}

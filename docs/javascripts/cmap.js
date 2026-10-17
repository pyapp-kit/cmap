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
  if (!dataCache.has(url)) {
    dataCache.set(
      url,
      fetch(url).then((r) => {
        if (!r.ok) throw new Error(`${r.status} fetching ${url}`);
        return r.json();
      })
    );
  }
  return dataCache.get(url);
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
// https://www.peterkovesi.com/matlabfns/Misc/circlesineramp.m
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

// A small colorbar canvas, e.g. for chart legends.
function swatch(colors, width = 32, height = 10) {
  const canvas = document.createElement("canvas");
  paint(canvas, colors, Array.from({ length: height }, () => linspace(width)).flat(), height, width);
  return canvas;
}

// ---------------------------------------------------------------------------
// Catalog grid filtering
// ---------------------------------------------------------------------------

function initCatalogFilter(root) {
  if (root.dataset.ready) return;
  root.dataset.ready = "1";
  const text = root.querySelector(".cmap-filter-text");
  const ns = root.querySelector(".cmap-filter-ns");
  const mono = root.querySelector(".cmap-filter-mono input");
  const catButtons = [...root.querySelectorAll(".cmap-filter-cats button")];
  const count = root.querySelector(".cmap-filter-count");
  const empty = root.querySelector(".cmap-empty");
  const items = [...root.querySelectorAll(".cmap-grid > .cmap")];
  let category = "all";

  function apply() {
    const words = text.value.toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const el of items) {
      const d = el.dataset;
      const visible =
        (category === "all" || d.category === category) &&
        (!ns.value || d.namespace === ns.value) &&
        (!mono.checked || d.monotonic === "1") &&
        words.every((w) => d.search.includes(w));
      el.hidden = !visible;
      shown += visible;
    }
    count.textContent = `${shown} of ${items.length} colormaps`;
    empty.hidden = shown > 0;
  }

  for (const btn of catButtons) {
    btn.addEventListener("click", () => {
      category = btn.dataset.category;
      catButtons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
      apply();
    });
  }
  text.addEventListener("input", apply);
  ns.addEventListener("change", apply);
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
  const data = await fetchData(new URL(root.dataset.json, location.href));
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

  for (const canvas of charts) {
    canvas.addEventListener("cmap:rerender", () => render(currentCvd()));
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
    plugins: { legend: { display: false } },
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

  if (kind === "lightness") {
    const options = baseOptions({
      y: { min: 0, max: 100, title: { text: "Lightness J′", display: true } },
      y2: {
        min: -500,
        max: 500,
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
            pointRadius: 10,
            pointHoverRadius: 12,
            borderWidth: 0,
          },
          {
            label: "dJ′",
            data: points(x, d.dJ),
            showLine: true,
            pointRadius: 0,
            borderColor: "#88888866",
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

async function initCompare(root) {
  if (root.dataset.ready) return;
  root.dataset.ready = "1";
  const base = new URL(root.dataset.base, location.href);
  const index = await fetchData(new URL("index.json", base));
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
  const resolve = (n) => byName.get(n.trim().toLowerCase().replace(/_r$/, ""));
  let selected = (params.get("cmaps") ?? "")
    .split(",")
    .map(resolve)
    .filter(Boolean)
    .slice(0, COMPARE_MAX);
  if (!selected.length) selected = ["bids:viridis", "cmocean:thermal", "crameri:batlow"]
    .map(resolve)
    .filter(Boolean);

  const cvd = () => cvdGroup.querySelector("input:checked")?.value ?? "normal";

  function syncUrl() {
    const url = new URL(location.href);
    url.searchParams.set("cmaps", selected.map((e) => e.name).join(","));
    history.replaceState(history.state, "", url);
  }

  async function render() {
    syncUrl();
    const datas = await Promise.all(
      selected.map((e) => fetchData(new URL(`${encodeURIComponent(e.path.split("/").pop())}.json`, base)))
    );
    rowsEl.replaceChildren(
      ...selected.map((e, i) => {
        const d = datas[i][cvd()] ?? datas[i].normal;
        const row = document.createElement("div");
        row.className = "cmap-compare-row";
        const head = document.createElement("div");
        head.className = "cmap-compare-head";
        const link = Object.assign(document.createElement("a"), {
          href: new URL(`../${e.path}/`, base).href,
          textContent: e.name,
        });
        const remove = Object.assign(document.createElement("button"), {
          type: "button",
          className: "cmap-compare-remove",
          title: `Remove ${e.name}`,
          textContent: "✕",
        });
        remove.addEventListener("click", () => {
          selected = selected.filter((s) => s !== e);
          render();
        });
        head.append(link, remove);
        const bar = document.createElement("canvas");
        bar.className = "cmap-compare-bar";
        paintBar(bar, d.color);
        const sine = document.createElement("canvas");
        sine.className = "cmap-sineramp";
        sine.dataset.testImage = "sineramp";
        row.append(head, bar, sine);
        setTestImageColors(sine, d.color);
        return row;
      })
    );

    Chart.getChart(chart)?.destroy();
    const options = baseOptions({
      y: { min: 0, max: 100, title: { text: "Lightness J′", display: true } },
    });
    // legend swatches are little colorbars of each colormap
    const swatches = datas.map((data) => swatch((data[cvd()] ?? data.normal).color));
    options.plugins.legend = {
      display: true,
      labels: {
        color: themeColors().fg,
        usePointStyle: true,
        pointStyleWidth: 32,
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
        datasets: selected.map((e, i) => {
          const d = datas[i][cvd()] ?? datas[i].normal;
          const x = linspace(d.color.length);
          const colors = d.color.map((c) => `#${c}`);
          return {
            label: e.name,
            data: points(x, d.J),
            showLine: true,
            pointRadius: 0,
            borderWidth: 5,
            // round caps hide the seams between the separately-colored segments
            borderCapStyle: "round",
            borderColor: colors[Math.floor(colors.length / 2)],
            // color each segment of the line by the colormap itself
            segment: { borderColor: (ctx) => colors[ctx.p0DataIndex] },
          };
        }),
      },
      options,
    });
  }

  chart.addEventListener("cmap:rerender", render);
  cvdGroup.addEventListener("change", render);
  root.querySelector(".cmap-compare-form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const e = resolve(input.value);
    input.setCustomValidity(e ? "" : "Unknown colormap");
    input.reportValidity();
    if (!e) return;
    if (!selected.includes(e)) selected = [...selected, e].slice(-COMPARE_MAX);
    input.value = "";
    render();
  });
  render();
}

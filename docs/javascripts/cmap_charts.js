GLOBAL_OPTIONS = {
  interaction: { mode: "index", intersect: false },
  plugins: { legend: { display: false } },
  clip: false,
};

initCharts();

async function initCharts() {
  var charts = document.getElementsByClassName("cmap-chart");
  if (charts.length == 0) {
    return;
  }

  var chartElems = {};
  // Make object mapping chart name to document element
  for (var i = 0; i < charts.length; i++) {
    var cmap_name = charts[i].getAttribute("data-cmap-name");
    if (cmap_name in chartElems) {
      chartElems[cmap_name].push(charts[i]);
    } else {
      chartElems[cmap_name] = [charts[i]];
    }
  }
  var cvd_type = document.getElementById("cvd").querySelector('input[name="cvd_button"]:checked')?.value;
  // Make all charts for each cmap name
  for (var cmap_name in chartElems) {
    // NOTE: we're using a global window variable here that will be
    // injected into the _gen_cmaps page... because it's much faster
    // on readthedocs than making an additional fetch request
    var cmap_data = window.cmap_data[cmap_name][cvd_type];
    for (var i = 0; i < chartElems[cmap_name].length; i++) {
      var canv = chartElems[cmap_name][i];
      const chart = Chart.getChart(canv);
      if (chart) {
        chart.destroy();
      }
    
      if (canv.classList.contains("rgb-chart")) {
        makeRGBChart(canv, cmap_data);
      } else if (canv.classList.contains("hsl-chart")) {
        makeHSLChart(canv, cmap_data);
      } else if (canv.classList.contains("linearity-chart")) {
        makeLinearityChart(canv, cmap_data);
      }
    }
  }
}

async function makeLinearityChart(canvas, data) {
  var lightness_data = [];
  var deltas = [];
  var a = [];
  var b = [];
  for (i = 0; i < data.x.length; i++) {
    lightness_data.push({ x: data.x[i], y: data.J[i] });
    deltas.push({ x: data.x[i], y: data.lightness_derivs[i] });
    // a.push({ x: cmap_data.x[i], y: cmap_data.a[i] })
    // b.push({ x: cmap_data.x[i], y: cmap_data.b[i] })
  }

  new Chart(canvas, {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "J",
          backgroundColor: data.color,
          data: lightness_data,
          pointRadius: 12,
          borderWidth: 0,
        },
        {
          label: "deltas",
          data: deltas,
          showLine: true,
          radius: 0,
          borderColor: "#AAAAAA66",
          borderWidth: 3,
          yAxisID: "y2",
        },
        // {
        //   label: "a",
        //   data: a,
        //   showLine: true,
        //   radius: 0,
        //   borderColor: "#AA222266",
        //   borderWidth: 2,
        //   yAxisID: "y3",
        // },
        // {
        //   label: "b",
        //   data: b,
        //   showLine: true,
        //   radius: 0,
        //   borderColor: "#2222AA66",
        //   borderWidth: 2,
        //   yAxisID: "y3",
        // },
      ],
    },
    options: {
      ...GLOBAL_OPTIONS,
      scales: {
        y: { max: 100, min: 0, title: { text: "Lightness L*", display: true } },
        y2: {
          max: 500,
          min: -500,
          title: { text: "Perceptual Lightness Deltas", display: true },
          position: "right",
        },
        // y3: { max: 120, min: -120, display: false },
      },
    },
  });
}

async function makeRGBChart(canvas, data) {
  var rdata = [];
  var gdata = [];
  var bdata = [];
  for (i = 0; i < data.x.length; i++) {
    rdata.push({ x: data.x[i], y: data.R[i] });
    gdata.push({ x: data.x[i], y: data.G[i] });
    bdata.push({ x: data.x[i], y: data.B[i] });
  }

  new Chart(canvas, {
    type: "scatter",
    data: {
      datasets: [
        { label: "red", showLine: true, borderColor: "#BB0000BB", data: rdata },
        {
          label: "green",
          showLine: true,
          borderColor: "#00CC00BB",
          data: gdata,
        },
        {
          label: "blue",
          showLine: true,
          borderColor: "#0000FFBB",
          data: bdata,
        },
      ],
    },
    options: {
      ...GLOBAL_OPTIONS,
      scales: {
        y: {
          max: 1,
          min: 0,
          title: { text: "Component Value", display: true },
        },
      },
      elements: {
        line: { borderWidth: 4 },
        point: { radius: 0 },
      },
    },
  });
}

async function makeHSLChart(canvas, data) {
  const datasets = [];
  var label_data, _data, val, lastval;

  ["saturation", "chroma", "hue"].forEach((label) => {
    label_data = data[label];
    _data = [];
    for (i = 0; i < data.x.length; i++) {
      val = label_data[i];
      // If the hue is jumping by more than 90 degrees, insert a null
      // value to break the line
      if (label == "hue" && Math.abs(val - lastval) > 95) {
        // we just fully skip this point, which does mean a data point is missed
        // but if we insert a null value, the chartjs hover tooltip will be offset
        // for all later points
        _data.push({ x: data.x[i], y: null });
      } else {
        _data.push({ x: data.x[i], y: val });
      }
      lastval = val;
    }
    datasets.push({
      label: label,
      showLine: true,
      data: _data,
      yAxisID: label == "hue" ? "y2" : "y",
    });
  });

  new Chart(canvas, {
    type: "scatter",
    data: { datasets: datasets },
    options: {
      ...GLOBAL_OPTIONS,
      plugins: { legend: { display: true, labels: { boxHeight: 1 } } },
      scales: {
        y: { max: 100, min: 0, title: { text: "Saturation/Chroma %", display: true } },
        y2: {
          max: 360,
          min: 0,
          ticks: { stepSize: 36 },
          title: { text: "Hue degree", display: true },
          position: "right",
        },
      },
      elements: {
        line: { borderWidth: 4 },
        point: { radius: 0 },
      },
    },
  });
}

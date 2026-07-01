const dataElement = document.querySelector("#weather-data");
const weeklyDataElement = document.querySelector("#weekly-data");
const canvas = document.querySelector("#weatherChart");
const weeklyCanvas = document.querySelector("#weeklyChart");
const buttons = document.querySelectorAll(".metric-button");
const weekButtons = document.querySelectorAll(".week-button");

const metricLabels = {
  temperature: "Temperature",
  humidity: "Humidity",
  wind_speed: "Wind speed",
  precipitation: "Rain chance"
};

const metricColors = {
  temperature: "#d95836",
  humidity: "#117c7d",
  wind_speed: "#547a47",
  precipitation: "#496f9f"
};

function resizeCanvas(targetCanvas, context, height) {
  const ratio = window.devicePixelRatio || 1;
  const rect = targetCanvas.getBoundingClientRect();
  targetCanvas.width = rect.width * ratio;
  targetCanvas.height = height * ratio;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
}

function drawLineChart({ targetCanvas, context, items, metric, height = 280, labelKey = "label" }) {
  resizeCanvas(targetCanvas, context, height);

  const width = targetCanvas.getBoundingClientRect().width;
  const padding = 36;
  const values = items.map((item) => Number(item[metric]));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const color = metricColors[metric];
  const average = values.reduce((total, value) => total + value, 0) / values.length;
  const averageY = height - padding - ((average - min) / range) * (height - padding * 2);

  context.clearRect(0, 0, width, height);
  context.lineWidth = 1;
  context.strokeStyle = "rgba(26, 31, 36, 0.13)";

  for (let index = 0; index < 5; index += 1) {
    const y = padding + ((height - padding * 2) / 4) * index;
    context.beginPath();
    context.moveTo(padding, y);
    context.lineTo(width - padding, y);
    context.stroke();
  }

  const points = values.map((value, index) => {
    const x = padding + ((width - padding * 2) / (values.length - 1)) * index;
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return { x, y, value };
  });

  function traceSmoothCurve(chartPoints) {
    chartPoints.forEach((point, index) => {
      if (index === 0) {
        context.moveTo(point.x, point.y);
        return;
      }

      const previousPoint = chartPoints[index - 1];
      const controlX = (previousPoint.x + point.x) / 2;
      context.bezierCurveTo(controlX, previousPoint.y, controlX, point.y, point.x, point.y);
    });
  }

  context.beginPath();
  context.moveTo(padding, averageY);
  context.lineTo(width - padding, averageY);
  context.setLineDash([6, 8]);
  context.lineWidth = 1;
  context.strokeStyle = "rgba(26, 31, 36, 0.2)";
  context.stroke();
  context.setLineDash([]);

  context.beginPath();
  traceSmoothCurve(points);
  context.lineTo(points[points.length - 1].x, height - padding);
  context.lineTo(points[0].x, height - padding);
  context.closePath();
  const fill = context.createLinearGradient(0, padding, 0, height - padding);
  fill.addColorStop(0, `${color}34`);
  fill.addColorStop(1, `${color}05`);
  context.fillStyle = fill;
  context.fill();

  context.beginPath();
  traceSmoothCurve(points);
  context.lineWidth = metric === "temperature" ? 4 : 3;
  context.lineCap = "round";
  context.lineJoin = "round";
  context.strokeStyle = color;
  context.shadowColor = `${color}55`;
  context.shadowBlur = metric === "temperature" ? 18 : 8;
  context.stroke();
  context.shadowBlur = 0;

  points.forEach((point, index) => {
    if (items.length <= 8 || index % 2 === 0) {
      context.beginPath();
      context.arc(point.x, point.y, metric === "temperature" ? 5 : 4, 0, Math.PI * 2);
      context.fillStyle = "#fffdf7";
      context.fill();
      context.lineWidth = 2;
      context.strokeStyle = color;
      context.stroke();
    }
  });

  context.fillStyle = "#1a1f24";
  context.font = "700 14px Source Sans 3";
  context.fillText(metricLabels[metric], padding, 20);
  context.fillText(`Avg ${average.toFixed(1)}`, padding + 120, 20);
  context.fillText(`${max}`, width - padding - 34, padding - 10);
  context.fillText(`${min}`, width - padding - 34, height - padding + 20);

  context.fillStyle = "#64707d";
  context.font = "600 12px Source Sans 3";
  items.forEach((item, index) => {
    if (items.length <= 8 || index % 4 === 0) {
      const point = points[index];
      context.fillText(item[labelKey], point.x - 14, height - 8);
    }
  });
}

function drawTemperatureBand({ targetCanvas, context, items, height = 300 }) {
  resizeCanvas(targetCanvas, context, height);

  const width = targetCanvas.getBoundingClientRect().width;
  const padding = 38;
  const lows = items.map((item) => Number(item.low));
  const highs = items.map((item) => Number(item.high));
  const min = Math.min(...lows);
  const max = Math.max(...highs);
  const range = max - min || 1;

  context.clearRect(0, 0, width, height);
  context.strokeStyle = "rgba(26, 31, 36, 0.13)";
  context.lineWidth = 1;

  for (let index = 0; index < 5; index += 1) {
    const y = padding + ((height - padding * 2) / 4) * index;
    context.beginPath();
    context.moveTo(padding, y);
    context.lineTo(width - padding, y);
    context.stroke();
  }

  const highPoints = highs.map((value, index) => {
    const x = padding + ((width - padding * 2) / (highs.length - 1)) * index;
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return { x, y, value };
  });

  const lowPoints = lows.map((value, index) => {
    const x = padding + ((width - padding * 2) / (lows.length - 1)) * index;
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return { x, y, value };
  });

  context.beginPath();
  highPoints.forEach((point, index) => {
    if (index === 0) {
      context.moveTo(point.x, point.y);
    } else {
      context.lineTo(point.x, point.y);
    }
  });
  [...lowPoints].reverse().forEach((point) => context.lineTo(point.x, point.y));
  context.closePath();
  context.fillStyle = "rgba(217, 88, 54, 0.18)";
  context.fill();

  [
    { points: highPoints, color: "#d95836", label: "High" },
    { points: lowPoints, color: "#496f9f", label: "Low" }
  ].forEach((series) => {
    context.beginPath();
    series.points.forEach((point, index) => {
      if (index === 0) {
        context.moveTo(point.x, point.y);
      } else {
        context.lineTo(point.x, point.y);
      }
    });
    context.lineWidth = 3;
    context.strokeStyle = series.color;
    context.stroke();

    series.points.forEach((point) => {
      context.beginPath();
      context.arc(point.x, point.y, 4, 0, Math.PI * 2);
      context.fillStyle = series.color;
      context.fill();
    });
  });

  context.fillStyle = "#1a1f24";
  context.font = "700 14px Source Sans 3";
  context.fillText("High / low temperature", padding, 20);
  context.fillText(`${max}`, width - padding - 34, padding - 10);
  context.fillText(`${min}`, width - padding - 34, height - padding + 20);

  context.fillStyle = "#64707d";
  context.font = "600 12px Source Sans 3";
  items.forEach((item, index) => {
    const point = highPoints[index];
    context.fillText(item.label, point.x - 14, height - 8);
  });
}

if (dataElement && canvas) {
  const weatherHours = JSON.parse(dataElement.textContent);
  const context = canvas.getContext("2d");

  let activeMetric = "temperature";

  function drawChart(metric) {
    drawLineChart({
      targetCanvas: canvas,
      context,
      items: weatherHours,
      metric
    });
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      activeMetric = button.dataset.metric;
      buttons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      drawChart(activeMetric);
    });
  });

  window.addEventListener("resize", () => drawChart(activeMetric));
  drawChart(activeMetric);
}

if (weeklyDataElement && weeklyCanvas) {
  const weekDays = JSON.parse(weeklyDataElement.textContent);
  const weekContext = weeklyCanvas.getContext("2d");

  let activeWeekMetric = "temperature";

  function drawWeeklyChart(metric) {
    if (metric === "temperature") {
      drawTemperatureBand({
        targetCanvas: weeklyCanvas,
        context: weekContext,
        items: weekDays
      });
      return;
    }

    drawLineChart({
      targetCanvas: weeklyCanvas,
      context: weekContext,
      items: weekDays,
      metric,
      height: 300
    });
  }

  weekButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeWeekMetric = button.dataset.weekMetric;
      weekButtons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      drawWeeklyChart(activeWeekMetric);
    });
  });

  window.addEventListener("resize", () => drawWeeklyChart(activeWeekMetric));
  drawWeeklyChart(activeWeekMetric);
}

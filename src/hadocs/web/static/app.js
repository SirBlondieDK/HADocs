const state = {
  status: null,
  logs: [],
};

const elements = {
  statusValue: document.getElementById("status-value"),
  statusDetail: document.getElementById("status-detail"),
  lastScanValue: document.getElementById("last-scan-value"),
  reportValue: document.getElementById("report-value"),
  scanButton: document.getElementById("scan-button"),
  progressCard: document.getElementById("scan-progress-card"),
  progressLabel: document.getElementById("progress-label"),
  progressPercent: document.getElementById("progress-percent"),
  progressBar: document.getElementById("progress-bar"),
  overviewLog: document.getElementById("overview-log"),
  fullLog: document.getElementById("full-log"),
  reportFrame: document.getElementById("report-frame"),
  reportEmpty: document.getElementById("report-empty"),
  reloadReportButton: document.getElementById("reload-report-button"),
  scrollButton: document.getElementById("clear-view-button"),
};

function apiUrl(path) {
  return `./api/${path}`;
}

async function fetchJson(url, options = undefined) {
  const response = await fetch(url, options);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }

  return payload;
}

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function openView(name) {
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${name}`);
  });

  document.querySelectorAll(".nav-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === name);
  });
}

function inferProgress(logs) {
  const text = logs.join("\n").toLowerCase();

  if (text.includes("documentation complete")) {
    return [100, "Documentation complete"];
  }

  if (text.includes("generating")) {
    return [78, "Generating reports"];
  }

  if (text.includes("building indexes")) {
    return [62, "Building indexes"];
  }

  if (text.includes("collecting")) {
    return [35, "Collecting Home Assistant data"];
  }

  return [12, "Starting scan"];
}

function render() {
  const status = state.status;

  if (!status) {
    return;
  }

  elements.scanButton.disabled = status.running;

  if (status.running) {
    elements.statusValue.textContent = "Scanning";
    elements.statusValue.className = "card-value";
    elements.statusDetail.textContent = "Documentation scan in progress";
    elements.scanButton.textContent = "Scan running…";
  } else if (status.exit_code === 0) {
    elements.statusValue.textContent = "Ready";
    elements.statusValue.className = "card-value success";
    elements.statusDetail.textContent = "Last scan completed successfully";
    elements.scanButton.textContent = "Start new scan";
  } else if (status.exit_code !== null) {
    elements.statusValue.textContent = "Scan failed";
    elements.statusValue.className = "card-value error";
    elements.statusDetail.textContent =
      status.error || `Exit code ${status.exit_code}`;
    elements.scanButton.textContent = "Retry scan";
  } else {
    elements.statusValue.textContent = "Ready";
    elements.statusValue.className = "card-value success";
    elements.statusDetail.textContent = "HADocs web service is online";
    elements.scanButton.textContent = "Start new scan";
  }

  elements.lastScanValue.textContent = formatDate(
    status.finished_at || status.started_at
  );

  if (status.report_available) {
    elements.reportValue.textContent = "Available";
    elements.reportValue.className = "card-value success";
    elements.reportFrame.classList.remove("hidden");
    elements.reportEmpty.classList.add("hidden");
  } else {
    elements.reportValue.textContent = "Not generated";
    elements.reportValue.className = "card-value";
    elements.reportFrame.classList.add("hidden");
    elements.reportEmpty.classList.remove("hidden");
  }

  const logText = state.logs.length
    ? state.logs.join("\n")
    : "No scan log available.";

  elements.overviewLog.textContent = logText;
  elements.fullLog.textContent = logText;

  if (status.running) {
    const [percent, label] = inferProgress(state.logs);

    elements.progressCard.classList.remove("hidden");
    elements.progressLabel.textContent = label;
    elements.progressPercent.textContent = `${percent}%`;
    elements.progressBar.style.width = `${percent}%`;

    elements.overviewLog.scrollTop = elements.overviewLog.scrollHeight;
    elements.fullLog.scrollTop = elements.fullLog.scrollHeight;
  } else {
    elements.progressCard.classList.add("hidden");
  }
}

async function refresh() {
  try {
    const [status, logPayload] = await Promise.all([
      fetchJson(apiUrl("status")),
      fetchJson(apiUrl("logs")),
    ]);

    state.status = status;
    state.logs = logPayload.logs || [];

    render();
  } catch (error) {
    elements.statusValue.textContent = "Connection error";
    elements.statusValue.className = "card-value error";
    elements.statusDetail.textContent = String(error);
  }
}

async function startScan() {
  elements.scanButton.disabled = true;

  try {
    await fetchJson(apiUrl("scan"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: "{}",
    });

    openView("overview");
  } catch (error) {
    window.alert(String(error));
  }

  await refresh();
}

function reloadReport() {
  elements.reportFrame.src =
    `./report/index.html?timestamp=${Date.now()}`;
}

document.querySelectorAll(".nav-button").forEach((button) => {
  button.addEventListener("click", () => {
    openView(button.dataset.view);
  });
});

document.querySelectorAll("[data-open-view]").forEach((button) => {
  button.addEventListener("click", () => {
    openView(button.dataset.openView);
  });
});

elements.scanButton.addEventListener("click", startScan);
elements.reloadReportButton.addEventListener("click", reloadReport);

elements.scrollButton.addEventListener("click", () => {
  elements.fullLog.scrollTop = elements.fullLog.scrollHeight;
});

refresh();
window.setInterval(refresh, 1500);
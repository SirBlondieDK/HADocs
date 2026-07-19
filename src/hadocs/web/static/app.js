const state = { status: null, logs: [], summary: null, overrides: [], devices: [], overrideFile: "", overrideQuery: "", overrideFilter: "all", editingDeviceId: null };

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
  explorerFrame: document.getElementById("explorer-frame"),
  explorerEmpty: document.getElementById("explorer-empty"),
  reloadExplorerButton: document.getElementById("reload-explorer-button"),
  scrollButton: document.getElementById("clear-view-button"),
  healthScore: document.getElementById("health-score"),
  healthStatus: document.getElementById("health-status"),
  inventoryValue: document.getElementById("inventory-value"),
  inventoryDetail: document.getElementById("inventory-detail"),
  recommendationTitle: document.getElementById("recommendation-title"),
  recommendationDetail: document.getElementById("recommendation-detail"),
  overrideCount: document.getElementById("override-count"),
  overrideExternalCount: document.getElementById("override-external-count"),
  overridePowerCount: document.getElementById("override-power-count"),
  overrideSeasonalCount: document.getElementById("override-seasonal-count"),
  overrideSearch: document.getElementById("override-search"),
  overrideList: document.getElementById("override-list"),
  overrideEmpty: document.getElementById("override-empty"),
  overrideError: document.getElementById("override-error"),
  addOverrideButton: document.getElementById("add-override-button"),
  overrideEditor: document.getElementById("override-editor"),
  overrideEditorLabel: document.getElementById("override-editor-label"),
  overrideEditorTitle: document.getElementById("override-editor-title"),
  overrideForm: document.getElementById("override-form"),
  overrideDevice: document.getElementById("override-device"),
  overridePolicy: document.getElementById("override-policy"),
  overrideOwnership: document.getElementById("override-ownership"),
  overridePurpose: document.getElementById("override-purpose"),
  overrideExpectedOffline: document.getElementById("override-expected-offline"),
  overrideIgnoreBattery: document.getElementById("override-ignore-battery"),
  overrideIgnoreStale: document.getElementById("override-ignore-stale"),
  overrideMonthsGroup: document.getElementById("override-months-group"),
  overrideReason: document.getElementById("override-reason"),
  overrideFormMessage: document.getElementById("override-form-message"),
  deleteOverrideButton: document.getElementById("delete-override-button"),
  saveOverrideButton: document.getElementById("save-override-button"),
  cancelOverrideButton: document.getElementById("cancel-override-button"),
  cancelOverrideButtonBottom: document.getElementById("cancel-override-button-bottom"),
};

function apiUrl(path) {
  return `./api/${path}`;
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
  return payload;
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function displayValue(value) {
  return String(value || "unspecified").replaceAll("_", " ");
}

function openView(name) {
  document.querySelectorAll(".view").forEach(view => {
    view.classList.toggle("active", view.id === `view-${name}`);
  });
  document.querySelectorAll(".nav-button").forEach(button => {
    button.classList.toggle("active", button.dataset.view === name);
  });

  if (name === "overrides") {
    Promise.all([loadOverrides(), loadDevices()]).catch(error => {
      elements.overrideError.textContent = String(error);
      elements.overrideError.classList.remove("hidden");
    });
  }
}

function inferProgress(logs) {
  const text = logs.join("\n").toLowerCase();
  if (text.includes("documentation complete") || text.includes("completed successfully")) return [100, "Documentation complete"];
  if (text.includes("generating")) return [78, "Generating reports"];
  if (text.includes("building indexes")) return [62, "Building indexes"];
  if (text.includes("collecting")) return [35, "Collecting Home Assistant data"];
  return [12, "Starting scan"];
}

function renderSummary() {
  const summary = state.summary || {};
  const health = summary.health || {};
  const inventory = summary.inventory || {};
  const recommendations = summary.recommendations || [];
  const score = health.health_score ?? health.score;
  const potential = health.potential_score;

  elements.healthScore.textContent = score == null ? "—" : `${score}`;
  elements.healthStatus.textContent =
    score == null
      ? "Run a scan to calculate health"
      : `${health.status || "Health calculated"}${potential == null ? "" : ` · Potential ${potential}`}`;

  const entities = inventory.entities ?? "—";
  const devices = inventory.devices ?? inventory.physical_devices ?? "—";
  elements.inventoryValue.textContent = entities;
  elements.inventoryDetail.textContent = `${devices} devices · ${inventory.integrations ?? "—"} integrations`;

  if (recommendations.length) {
    const top = recommendations[0];
    elements.recommendationTitle.textContent = top.title || "Top recommendation";
    const gain = top.estimated_score_gain ?? 0;
    const minutes = top.estimated_repair_minutes ?? 0;
    elements.recommendationDetail.textContent =
      `+${gain} health · about ${minutes} min${top.reason ? ` · ${top.reason}` : ""}`;
  }
}

function overrideFlags(policy) {
  const flags = [];
  if (policy.expected_offline) flags.push("Expected offline");
  if (policy.ignore_battery) flags.push("Ignore battery");
  if (policy.ignore_stale) flags.push("Ignore stale");
  if (Array.isArray(policy.active_months) && policy.active_months.length) {
    flags.push(`Active: ${formatMonths(policy.active_months)}`);
  }
  return flags;
}

function formatMonths(months) {
  const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return months.map(month => names[Number(month) - 1] || month).join(", ");
}

function policyPresentation(type) {
  const presentations = {
    external: {
      icon: "↗",
      title: "External device",
      explanation: "This device is not part of the Home Assistant installation.",
      className: "policy-external",
    },
    power_controlled: {
      icon: "⚡",
      title: "Power controlled",
      explanation: "This device can normally be offline because its power is controlled elsewhere.",
      className: "policy-power",
    },
    seasonal: {
      icon: "◷",
      title: "Seasonal device",
      explanation: "This device is only expected to be active during selected months.",
      className: "policy-seasonal",
    },
    temporary: {
      icon: "⌛",
      title: "Temporary device",
      explanation: "This device is only part of the installation for a limited period.",
      className: "policy-temporary",
    },
    normal: {
      icon: "✓",
      title: "Custom assessment",
      explanation: "HADocs applies the documented exceptions below.",
      className: "policy-normal",
    },
  };
  return presentations[type] || presentations.normal;
}

function updateOverrideStats() {
  const counts = state.overrides.reduce((result, item) => {
    const type = item.policy?.type || "normal";
    result[type] = (result[type] || 0) + 1;
    return result;
  }, {});

  elements.overrideCount.textContent = String(state.overrides.length);
  elements.overrideExternalCount.textContent = String(counts.external || 0);
  elements.overridePowerCount.textContent = String(counts.power_controlled || 0);
  elements.overrideSeasonalCount.textContent = String(counts.seasonal || 0);
}

function renderOverrides() {
  const query = state.overrideQuery.trim().toLowerCase();
  const visible = state.overrides.filter(item => {
    const policy = item.policy || {};
    const matchesFilter =
      state.overrideFilter === "all" || policy.type === state.overrideFilter;
    const haystack = [
      item.device_name,
      item.device_id,
      policy.type,
      policy.ownership,
      policy.purpose,
      item.reason,
      ...overrideFlags(policy),
    ].join(" ").toLowerCase();
    return matchesFilter && (!query || haystack.includes(query));
  });

  updateOverrideStats();
  elements.overrideEmpty.classList.toggle("hidden", state.overrides.length !== 0);
  elements.overrideList.innerHTML = "";

  if (!state.overrides.length) return;

  if (!visible.length) {
    elements.overrideList.innerHTML =
      '<section class="card empty-state compact-empty"><h2>No matching overrides</h2><p>Try another search term or filter.</p></section>';
    return;
  }

  elements.overrideList.innerHTML = visible.map(item => {
    const policy = item.policy || {};
    const presentation = policyPresentation(policy.type);
    const deviceName = item.device_name || item.device_id || "Unknown device";
    const deviceId = item.device_id || "No device ID";
    const flags = overrideFlags(policy);
    const flagHtml = flags.length
      ? flags.map(flag => `<span class="flag-badge">${escapeHtml(flag)}</span>`).join("")
      : '<span class="muted-text">No extra exceptions</span>';

    return `
      <article class="card override-card ${presentation.className}">
        <div class="override-card-heading">
          <div class="override-device">
            <strong>${escapeHtml(deviceName)}</strong>
            <code>${escapeHtml(deviceId)}</code>
          </div>
          <div class="policy-heading">
            <span class="policy-icon" aria-hidden="true">${presentation.icon}</span>
            <div>
              <strong>${escapeHtml(presentation.title)}</strong>
              <span>${escapeHtml(presentation.explanation)}</span>
            </div>
          </div>
        </div>

        <div class="override-properties">
          <div><span>Ownership</span><strong>${escapeHtml(displayValue(policy.ownership))}</strong></div>
          <div><span>Purpose</span><strong>${escapeHtml(displayValue(policy.purpose))}</strong></div>
          <div><span>Assessment</span><strong>${escapeHtml(displayValue(policy.type))}</strong></div>
        </div>

        <div class="override-flags">${flagHtml}</div>

        <div class="override-reason-block">
          <span>Why HADocs treats it differently</span>
          <p>${escapeHtml(item.reason || "No reason documented.")}</p>
        </div>

        <div class="override-card-actions">
          <button class="secondary-button edit-override-button" type="button" data-edit-device-id="${escapeHtml(deviceId)}">Edit</button>
        </div>
      </article>
    `;
  }).join("");

  document.querySelectorAll("[data-edit-device-id]").forEach(button => {
    button.addEventListener("click", () => openOverrideEditor(button.dataset.editDeviceId));
  });
}

async function loadDevices() {
  const payload = await fetchJson(apiUrl("devices"));
  state.devices = Array.isArray(payload.devices) ? payload.devices : [];
  renderDeviceOptions();
}

function renderDeviceOptions(selectedDeviceId = "") {
  const overrideIds = new Set(state.overrides.map(item => item.device_id).filter(Boolean));
  const options = ['<option value="">Choose a device…</option>'];

  state.devices.forEach(device => {
    const selected = device.device_id === selectedDeviceId ? " selected" : "";
    const alreadyConfigured = overrideIds.has(device.device_id) && device.device_id !== state.editingDeviceId;
    const disabled = alreadyConfigured ? " disabled" : "";
    const suffix = alreadyConfigured ? " — already configured" : "";
    options.push(
      `<option value="${escapeHtml(device.device_id)}"${selected}${disabled}>${escapeHtml(device.device_name + suffix)}</option>`
    );
  });

  elements.overrideDevice.innerHTML = options.join("");
}

function setEditorMessage(message = "", isError = false) {
  elements.overrideFormMessage.textContent = message;
  elements.overrideFormMessage.classList.toggle("hidden", !message);
  elements.overrideFormMessage.classList.toggle("error", isError);
  elements.overrideFormMessage.classList.toggle("success", Boolean(message) && !isError);
}

function selectedMonths() {
  return Array.from(document.querySelectorAll('input[name="active-month"]:checked'))
    .map(input => Number(input.value));
}

function setSelectedMonths(months) {
  const selected = new Set(Array.isArray(months) ? months.map(Number) : []);
  document.querySelectorAll('input[name="active-month"]').forEach(input => {
    input.checked = selected.has(Number(input.value));
  });
}

function updateMonthVisibility() {
  elements.overrideMonthsGroup.classList.toggle("hidden", elements.overridePolicy.value !== "seasonal");
}

function openOverrideEditor(deviceId = null) {
  state.editingDeviceId = deviceId;
  const item = deviceId
    ? state.overrides.find(override => override.device_id === deviceId)
    : null;
  const policy = item?.policy || {};

  elements.overrideEditorLabel.textContent = item ? "Edit Device Override" : "New Device Override";
  elements.overrideEditorTitle.textContent = item?.device_name || "Choose a device";
  elements.overrideDevice.disabled = Boolean(item);
  renderDeviceOptions(deviceId || "");
  elements.overridePolicy.value = policy.type || "normal";
  elements.overrideOwnership.value = policy.ownership || "unspecified";
  elements.overridePurpose.value = policy.purpose || "unspecified";
  elements.overrideExpectedOffline.checked = Boolean(policy.expected_offline);
  elements.overrideIgnoreBattery.checked = Boolean(policy.ignore_battery);
  elements.overrideIgnoreStale.checked = Boolean(policy.ignore_stale);
  elements.overrideReason.value = item?.reason || "";
  setSelectedMonths(policy.active_months || []);
  updateMonthVisibility();
  elements.deleteOverrideButton.classList.toggle("hidden", !item);
  setEditorMessage();
  elements.overrideEditor.classList.remove("hidden");
  elements.overrideEditor.scrollIntoView({ behavior: "smooth", block: "start" });
}

function closeOverrideEditor() {
  state.editingDeviceId = null;
  elements.overrideEditor.classList.add("hidden");
  elements.overrideForm.reset();
  setSelectedMonths([]);
  setEditorMessage();
}

async function saveOverride(event) {
  event.preventDefault();
  const deviceId = elements.overrideDevice.value;
  if (!deviceId) {
    setEditorMessage("Choose a device before saving.", true);
    return;
  }

  const device = state.devices.find(item => item.device_id === deviceId);
  const payload = {
    device_id: deviceId,
    device_name: device?.device_name || undefined,
    reason: elements.overrideReason.value.trim(),
    policy: {
      ownership: elements.overrideOwnership.value,
      purpose: elements.overridePurpose.value,
      type: elements.overridePolicy.value,
      expected_offline: elements.overrideExpectedOffline.checked,
      ignore_battery: elements.overrideIgnoreBattery.checked,
      ignore_stale: elements.overrideIgnoreStale.checked,
      active_months: elements.overridePolicy.value === "seasonal" ? selectedMonths() : [],
    },
  };

  elements.saveOverrideButton.disabled = true;
  setEditorMessage("Saving…");
  try {
    await fetchJson(apiUrl("device-overrides"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await loadOverrides();
    closeOverrideEditor();
  } catch (error) {
    setEditorMessage(String(error), true);
  } finally {
    elements.saveOverrideButton.disabled = false;
  }
}

async function deleteOverride() {
  const deviceId = state.editingDeviceId;
  if (!deviceId) return;

  const item = state.overrides.find(override => override.device_id === deviceId);
  const name = item?.device_name || deviceId;
  if (!window.confirm(`Delete the Device Override for "${name}"?`)) return;

  elements.deleteOverrideButton.disabled = true;
  setEditorMessage("Deleting…");
  try {
    await fetchJson(`${apiUrl("device-overrides")}/${encodeURIComponent(deviceId)}`, {
      method: "DELETE",
    });
    await loadOverrides();
    closeOverrideEditor();
  } catch (error) {
    setEditorMessage(String(error), true);
  } finally {
    elements.deleteOverrideButton.disabled = false;
  }
}

async function loadOverrides() {
  elements.overrideError.classList.add("hidden");
  try {
    const payload = await fetchJson(apiUrl("device-overrides"));
    state.overrides = Array.isArray(payload.overrides) ? payload.overrides : [];
    state.overrideFile = payload.file || "";
    renderOverrides();
    if (!elements.overrideEditor.classList.contains("hidden")) {
      renderDeviceOptions(state.editingDeviceId || elements.overrideDevice.value);
    }
  } catch (error) {
    state.overrides = [];
    elements.overrideList.innerHTML = "";
    elements.overrideEmpty.classList.add("hidden");
    elements.overrideError.textContent = String(error);
    elements.overrideError.classList.remove("hidden");
  }
}

function render() {
  const status = state.status;
  if (!status) return;
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
    elements.statusDetail.textContent = status.error || `Exit code ${status.exit_code}`;
    elements.scanButton.textContent = "Retry scan";
  } else {
    elements.statusValue.textContent = "Ready";
    elements.statusValue.className = "card-value success";
    elements.statusDetail.textContent = "HADocs web service is online";
    elements.scanButton.textContent = "Start new scan";
  }

  elements.lastScanValue.textContent = formatDate(status.finished_at || status.started_at);
  elements.reportValue.textContent = status.report_available ? "Available" : "Not generated";
  elements.reportValue.className = status.report_available ? "card-value success" : "card-value";
  elements.reportFrame.classList.toggle("hidden", !status.report_available);
  elements.reportEmpty.classList.toggle("hidden", status.report_available);
  elements.explorerFrame.classList.toggle("hidden", !status.report_available);
  elements.explorerEmpty.classList.toggle("hidden", status.report_available);

  const logText = state.logs.length ? state.logs.join("\n") : "No scan log available.";
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

  renderSummary();
}

async function refresh() {
  try {
    const [status, logPayload, summary] = await Promise.all([
      fetchJson(apiUrl("status")),
      fetchJson(apiUrl("logs")),
      fetchJson(apiUrl("summary")),
    ]);
    state.status = status;
    state.logs = logPayload.logs || [];
    state.summary = summary;
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
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    openView("overview");
  } catch (error) {
    window.alert(String(error));
  }
  await refresh();
}

function reloadFrame(frame, path) {
  frame.src = `${path}?timestamp=${Date.now()}`;
}

document.querySelectorAll(".nav-button").forEach(button => {
  button.addEventListener("click", () => openView(button.dataset.view));
});
document.querySelectorAll("[data-open-view]").forEach(button => {
  button.addEventListener("click", () => openView(button.dataset.openView));
});

elements.scanButton.addEventListener("click", startScan);
elements.reloadReportButton.addEventListener("click", () => reloadFrame(elements.reportFrame, "./report/index.html"));
elements.reloadExplorerButton.addEventListener("click", () => reloadFrame(elements.explorerFrame, "./report/explorer/index.html"));
elements.scrollButton.addEventListener("click", () => {
  elements.fullLog.scrollTop = elements.fullLog.scrollHeight;
});
elements.overrideSearch.addEventListener("input", event => {
  state.overrideQuery = event.target.value;
  renderOverrides();
});

document.querySelectorAll("[data-override-filter]").forEach(button => {
  button.addEventListener("click", () => {
    state.overrideFilter = button.dataset.overrideFilter;
    document.querySelectorAll("[data-override-filter]").forEach(item => {
      item.classList.toggle("active", item === button);
    });
    renderOverrides();
  });
});

elements.addOverrideButton.addEventListener("click", () => openOverrideEditor());
elements.overrideForm.addEventListener("submit", saveOverride);
elements.overridePolicy.addEventListener("change", updateMonthVisibility);
elements.deleteOverrideButton.addEventListener("click", deleteOverride);
elements.cancelOverrideButton.addEventListener("click", closeOverrideEditor);
elements.cancelOverrideButtonBottom.addEventListener("click", closeOverrideEditor);

refresh();
window.setInterval(refresh, 1500);

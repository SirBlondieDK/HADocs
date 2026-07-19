const state = {
  status: null,
  logs: [],
  summary: null,
  overrides: [],
  devices: [],
  overrideFile: "",
  overrideQuery: "",
  overrideFilter: "all",
  editingDeviceId: null,
  devicePickerQuery: "",
  devicePickerOpen: false,
  devicePickerHighlight: 0,
  expandedRootCauses: new Set(),
  expandedRecommendations: new Set(),
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
  reportEmpty: document.getElementById("report-empty"),
  analysisDashboard: document.getElementById("analysis-dashboard"),
  refreshAnalysisButton: document.getElementById("refresh-analysis-button"),
  analysisHealthScore: document.getElementById("analysis-health-score"),
  analysisHealthStatus: document.getElementById("analysis-health-status"),
  analysisHealthDetail: document.getElementById("analysis-health-detail"),
  analysisPotentialScore: document.getElementById("analysis-potential-score"),
  analysisPotentialDetail: document.getElementById("analysis-potential-detail"),
  analysisRootCount: document.getElementById("analysis-root-count"),
  analysisSuppressedCount: document.getElementById("analysis-suppressed-count"),
  analysisTopRecommendation: document.getElementById("analysis-top-recommendation"),
  analysisRecommendations: document.getElementById("analysis-recommendations"),
  analysisRootCauses: document.getElementById("analysis-root-causes"),
  analysisRootSummary: document.getElementById("analysis-root-summary"),
  analysisInventory: document.getElementById("analysis-inventory"),
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
  devicePicker: document.getElementById("device-picker"),
  devicePickerTrigger: document.getElementById("device-picker-trigger"),
  devicePickerTriggerContent: document.getElementById("device-picker-trigger-content"),
  devicePickerPanel: document.getElementById("device-picker-panel"),
  devicePickerSearch: document.getElementById("device-picker-search"),
  devicePickerResults: document.getElementById("device-picker-results"),
  devicePickerEmpty: document.getElementById("device-picker-empty"),
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

  if (name === "report") {
    refresh();
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


function numberValue(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function firstValue(object, keys, fallback = null) {
  for (const key of keys) {
    if (object && object[key] != null) return object[key];
  }
  return fallback;
}

function titleForIssue(item) {
  return firstValue(item, ["title", "root_cause", "key", "name"], "Untitled issue");
}

function issueArray(item, keys) {
  for (const key of keys) {
    const value = item?.[key];
    if (Array.isArray(value)) return value;
  }
  return [];
}

function issueCounts(item) {
  return {
    entities: issueArray(item, ["affected_entities", "entities"]),
    devices: issueArray(item, ["affected_devices", "devices"]),
    integrations: issueArray(item, ["affected_integrations", "integrations"]),
    children: issueArray(item, ["child_incidents", "children"]),
  };
}


function isHassioIssue(item) {
  const root = String(firstValue(item, ["root_cause", "key", "title"], "")).toLowerCase();
  const integrations = issueArray(item, ["affected_integrations", "integrations"]).map(value => String(value).toLowerCase());
  return integrations.some(value => ["hassio", "supervisor", "home_assistant_supervisor"].includes(value))
    || root.includes("supervisor")
    || root === "hassio";
}

function hassioEvidenceHtml(item) {
  if (!isHassioIssue(item)) return "";

  const entityIds = issueArray(item, ["affected_entities", "entities"]).map(value => String(value));
  const centralMarkers = [
    "supervisor",
    "home_assistant_host",
    "home_assistant_core",
    "home_assistant_operating_system",
  ];
  const centralSignals = entityIds.filter(entityId => {
    const lowered = entityId.toLowerCase();
    return centralMarkers.some(marker => lowered.includes(marker));
  });
  const addonSignals = Math.max(0, entityIds.length - centralSignals.length);
  const severity = String(firstValue(item, ["severity"], "maintenance")).toLowerCase();
  const confirmedOutage = severity === "critical";
  const runtimeReview = severity === "warning";
  const assessment = confirmedOutage
    ? "Confirmed central outage signal"
    : runtimeReview
      ? "Central runtime signal unavailable"
      : "No confirmed central outage";
  const confidence = confirmedOutage ? "High" : runtimeReview ? "Medium" : "Low-risk maintenance";

  return `
    <div class="analysis-platform-evidence">
      <div class="analysis-platform-heading">
        <div><span class="card-label">Supervisor assessment</span><strong>${escapeHtml(assessment)}</strong></div>
        <span class="analysis-confidence confidence-${escapeHtml(severity)}">${escapeHtml(confidence)}</span>
      </div>
      <div class="analysis-platform-grid">
        <article><span>Core / Supervisor / Host</span><strong>${confirmedOutage ? "Outage detected" : runtimeReview ? "Review required" : "No confirmed outage"}</strong></article>
        <article><span>Central status signals</span><strong>${centralSignals.length}</strong></article>
        <article><span>Add-on/helper sensors</span><strong>${addonSignals}</strong></article>
        <article><span>Assessment</span><strong>${escapeHtml(displayValue(severity))}</strong></article>
      </div>
      <p>${confirmedOutage
        ? "At least one central Home Assistant runtime signal is unavailable."
        : runtimeReview
          ? "A central status signal is unavailable, but HADocs did not confirm a hard Core, Supervisor, or Host outage."
          : "This finding is based on unknown helper or add-on status sensors. Unknown alone is not treated as a service outage."}</p>
    </div>
  `;
}

function issueDetailHtml(item) {
  const counts = issueCounts(item);
  const recommendation = firstValue(item, ["recommendation", "reason", "description"], "No recommended action documented.");
  const sections = [];

  const listSection = (title, values) => {
    if (!values.length) return;
    const items = values.slice(0, 12).map(value => {
      const label = typeof value === "string" ? value : titleForIssue(value);
      return `<li>${escapeHtml(label)}</li>`;
    }).join("");
    const more = values.length > 12 ? `<li class="muted-text">…and ${values.length - 12} more</li>` : "";
    sections.push(`<div class="analysis-detail-group"><strong>${escapeHtml(title)}</strong><ul>${items}${more}</ul></div>`);
  };

  listSection("Affected devices", counts.devices);
  listSection("Affected entities", counts.entities);
  listSection("Affected integrations", counts.integrations);
  listSection("Child incidents", counts.children);

  return `
    ${hassioEvidenceHtml(item)}
    <div class="analysis-detail-grid">
      <div class="analysis-detail-group"><strong>Recommended action</strong><p>${escapeHtml(recommendation)}</p></div>
      ${sections.join("") || '<div class="analysis-detail-group"><strong>Evidence</strong><p>No additional affected items were included in this scan output.</p></div>'}
    </div>
  `;
}


function stableAnalysisKey(item, prefix = "item") {
  const raw = firstValue(
    item,
    ["incident_id", "recommendation_id", "id", "key", "root_cause", "title", "name"],
    prefix,
  );
  return `${prefix}:${String(raw)}`;
}

function bindAnalysisDisclosureState() {
  document.querySelectorAll("details[data-analysis-kind][data-analysis-key]").forEach(detail => {
    detail.addEventListener("toggle", () => {
      const targetSet = detail.dataset.analysisKind === "root"
        ? state.expandedRootCauses
        : state.expandedRecommendations;
      const key = detail.dataset.analysisKey;
      if (detail.open) targetSet.add(key);
      else targetSet.delete(key);

      const label = detail.querySelector(".analysis-open-label");
      if (label) label.textContent = detail.open ? "Hide evidence" : "View evidence";
    });
  });
}

function recommendationCard(item, rank, potentialGain, primary = false) {
  const claimedGain = numberValue(firstValue(item, ["estimated_score_gain", "score_gain"], 0));
  const gain = Math.min(claimedGain, potentialGain);
  const minutes = numberValue(firstValue(item, ["estimated_repair_minutes", "repair_minutes"], 0));
  const counts = issueCounts(item);
  const title = titleForIssue(item);
  const summary = firstValue(item, ["reason", "recommendation", "description"], "Active recommendation");
  const countParts = [];
  const disclosureKey = stableAnalysisKey(item, primary ? "top-recommendation" : "recommendation");
  const isOpen = state.expandedRecommendations.has(disclosureKey);
  if (counts.devices.length) countParts.push(`${counts.devices.length} device${counts.devices.length === 1 ? "" : "s"}`);
  if (counts.entities.length) countParts.push(`${counts.entities.length} entit${counts.entities.length === 1 ? "y" : "ies"}`);

  return `
    <details class="${primary ? "analysis-primary-recommendation" : "analysis-list-item analysis-action-item"}" data-analysis-kind="recommendation" data-analysis-key="${escapeHtml(disclosureKey)}"${isOpen ? " open" : ""}>
      <summary>
        ${primary ? "" : `<span class="analysis-rank">${rank}</span>`}
        <div class="analysis-action-copy">
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(summary)}</span>
          <small>${escapeHtml(countParts.join(" · ") || "Active finding")}${minutes ? ` · ~${minutes} min` : ""}</small>
        </div>
        <b>${gain ? `+${gain}` : "—"}</b>
        <span class="analysis-chevron" aria-hidden="true">⌄</span>
      </summary>
      ${issueDetailHtml(item)}
    </details>
  `;
}

function renderAnalysis() {
  const summary = state.summary || {};
  const available = Boolean(summary.available);
  elements.reportEmpty.classList.toggle("hidden", available);
  elements.analysisDashboard.classList.toggle("hidden", !available);
  if (!available) return;

  const health = summary.health || {};
  const inventory = summary.inventory || {};
  const incidents = Array.isArray(summary.incidents) ? summary.incidents : [];
  const recommendations = Array.isArray(summary.recommendations) ? summary.recommendations : [];

  const score = numberValue(firstValue(health, ["health_score", "score"], 0));
  const potential = Math.max(score, numberValue(firstValue(health, ["potential_score"], score), score));
  const potentialGain = Math.max(0, potential - score);
  const suppressed = numberValue(firstValue(health, ["suppressed_incident_count", "suppressed_incidents", "filtered_noise", "hidden_noise"], 0));

  elements.analysisHealthScore.textContent = `${score}`;
  elements.analysisHealthStatus.textContent = firstValue(health, ["status", "grade"], score >= 85 ? "Healthy" : "Needs attention");
  elements.analysisHealthDetail.textContent = `${potentialGain} achievable point${potentialGain === 1 ? "" : "s"} remain after active fixes.`;
  elements.analysisPotentialScore.textContent = `${potential}/100`;
  elements.analysisPotentialDetail.textContent = potentialGain ? `+${potentialGain} available` : "No score gain currently available";
  elements.analysisRootCount.textContent = String(incidents.length);
  elements.analysisSuppressedCount.textContent = String(suppressed);

  const top = recommendations[0];
  // Keep the permanent container from index.html. Replacing it with outerHTML
  // detached the cached element reference and caused the next refresh to fail.
  elements.analysisTopRecommendation.innerHTML = top
    ? recommendationCard(top, 1, potentialGain, true)
    : '<div class="analysis-empty-recommendation"><strong>No active recommendation</strong><span>The current scan has no effective fixes to prioritise.</span></div>';

  elements.analysisRecommendations.innerHTML = recommendations.slice(1, 8).map((item, index) =>
    recommendationCard(item, index + 2, potentialGain)
  ).join("");

  const categoryCounts = incidents.reduce((result, item) => {
    const category = String(firstValue(item, ["category", "type"], "issue")).toLowerCase();
    result[category] = (result[category] || 0) + 1;
    return result;
  }, {});
  const categorySummary = Object.entries(categoryCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([category, count]) => `${count} ${displayValue(category)}`)
    .join(" · ");
  elements.analysisRootSummary.textContent = categorySummary || `${incidents.length} active after overrides`;

  elements.analysisRootCauses.innerHTML = incidents.slice(0, 16).map(item => {
    const severity = String(firstValue(item, ["severity"], "maintenance")).toLowerCase();
    const counts = issueCounts(item);
    const category = firstValue(item, ["category", "type"], "issue");
    const disclosureKey = stableAnalysisKey(item, "root");
    const isOpen = state.expandedRootCauses.has(disclosureKey);
    return `
      <details class="analysis-root-card severity-${escapeHtml(severity)}" data-analysis-kind="root" data-analysis-key="${escapeHtml(disclosureKey)}"${isOpen ? " open" : ""}>
        <summary>
          <div class="analysis-root-heading"><strong>${escapeHtml(titleForIssue(item))}</strong><span>${escapeHtml(severity)}</span></div>
          <p>${escapeHtml(firstValue(item, ["title", "reason", "description"], `${displayValue(category)} issue`))}</p>
          <div class="analysis-root-meta">
            <span>${escapeHtml(displayValue(category))}</span>
            <span>${counts.devices.length} device${counts.devices.length === 1 ? "" : "s"}</span>
            <span>${counts.entities.length} entit${counts.entities.length === 1 ? "y" : "ies"}</span>
            <span class="analysis-open-label">${isOpen ? "Hide evidence" : "View evidence"}</span>
          </div>
        </summary>
        ${issueDetailHtml(item)}
      </details>
    `;
  }).join("") || '<p class="muted-text">No active root causes.</p>';

  const inventoryItems = [
    ["Areas", firstValue(inventory, ["areas"], 0)],
    ["Devices", firstValue(inventory, ["devices", "physical_devices"], 0)],
    ["Physical", firstValue(inventory, ["physical_devices"], 0)],
    ["Virtual", firstValue(inventory, ["virtual_devices"], 0)],
    ["System", firstValue(inventory, ["system_devices"], 0)],
    ["Integrations", firstValue(inventory, ["integrations"], 0)],
    ["Entities", firstValue(inventory, ["entities"], 0)],
    ["Labels", firstValue(inventory, ["labels"], 0)],
  ];
  elements.analysisInventory.innerHTML = inventoryItems.map(([label, value]) => `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value ?? 0)}</strong></article>`).join("");
  bindAnalysisDisclosureState();
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

function deviceIntegration(device) {
  return device.integration || device.subtitle || "Unknown integration";
}

function deviceMeta(device) {
  return [device.manufacturer, device.model].filter(Boolean).join(" ");
}

function deviceIcon(device) {
  const classification = String(device.classification || "").toLowerCase();
  if (["container", "server", "service"].includes(classification)) return "▦";

  const domain = String(device.primary_domain || device.domains?.[0] || "").toLowerCase();
  const icons = {
    light: "💡",
    switch: "⌁",
    sensor: "◉",
    binary_sensor: "◇",
    media_player: "▶",
    camera: "◉",
    climate: "♨",
    lock: "▣",
    cover: "▤",
    vacuum: "◒",
    lawn_mower: "✦",
    device_tracker: "⌖",
    person: "●",
    button: "◎",
    update: "↻",
  };
  return icons[domain] || "▣";
}

function deviceCardMarkup(device, { selected = false, highlighted = false } = {}) {
  const integration = deviceIntegration(device);
  const metadata = deviceMeta(device);
  const count = Number(device.entity_count || 0);
  const entityLabel = count === 1 ? "1 entity" : `${count} entities`;
  const healthLabel = deviceHealthLabel(device);
  const classes = ["device-card"];
  if (selected) classes.push("selected");
  if (highlighted) classes.push("highlighted");

  return `
    <span class="device-card-icon" aria-hidden="true">${deviceIcon(device)}</span>
    <span class="device-card-content">
      <span class="device-card-title">${escapeHtml(device.device_name)}</span>
      <span class="device-card-context">
        <span class="integration-badge ${integrationClass(device)}">${escapeHtml(integration)}</span>
        ${device.area ? `<span class="area-badge">⌂ ${escapeHtml(device.area)}</span>` : '<span class="area-badge area-unassigned">⌂ No area</span>'}
      </span>
      <span class="device-card-details">
        ${metadata ? `<span>${escapeHtml(metadata)}</span>` : ""}
        ${device.classification ? `<span>${escapeHtml(displayValue(device.classification))}</span>` : ""}
        <span>${escapeHtml(entityLabel)}</span>
        ${healthLabel ? `<span class="device-health${device.online === false ? " offline" : " warning"}">${escapeHtml(healthLabel)}</span>` : ""}
      </span>
    </span>
    ${selected ? '<span class="device-card-check" aria-hidden="true">✓</span>' : ""}
  `;
}

function integrationClass(device) {
  const value = String(device.platform || device.integration || "unknown")
    .toLowerCase()
    .replaceAll(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return `integration-${value || "unknown"}`;
}

function deviceHealthLabel(device) {
  if (device.online === false) return "Offline";
  if (Number(device.unavailable_count || 0) > 0) return `${device.unavailable_count} unavailable`;
  if (Number(device.unknown_count || 0) > 0) return `${device.unknown_count} unknown`;
  return "";
}

function deviceSearchText(device) {
  return [
    device.device_name,
    device.device_id,
    device.integration,
    device.area,
    device.manufacturer,
    device.model,
    device.subtitle,
    device.classification,
    ...(Array.isArray(device.entity_ids) ? device.entity_ids : []),
    ...(Array.isArray(device.domains) ? device.domains : []),
    ...(Array.isArray(device.platforms) ? device.platforms : []),
  ].filter(Boolean).join(" ").toLowerCase();
}

function selectedDevice() {
  return state.devices.find(device => device.device_id === elements.overrideDevice.value);
}

function renderDeviceTrigger() {
  const device = selectedDevice();
  if (!device) {
    elements.devicePickerTriggerContent.className = "device-picker-placeholder";
    elements.devicePickerTriggerContent.textContent = "Choose a device…";
    return;
  }

  const detail = [deviceIntegration(device), device.area].filter(Boolean).join(" · ");
  elements.devicePickerTriggerContent.className = "device-picker-selected";
  elements.devicePickerTriggerContent.innerHTML = `
    <strong>${escapeHtml(device.device_name)}</strong>
    <span>${escapeHtml(detail || device.device_id)}</span>
  `;
}

function filteredPickerDevices() {
  const overrideIds = new Set(state.overrides.map(item => item.device_id).filter(Boolean));
  const query = state.devicePickerQuery.trim().toLowerCase();
  return state.devices.filter(device => {
    const alreadyConfigured = overrideIds.has(device.device_id) && device.device_id !== state.editingDeviceId;
    return !alreadyConfigured && (!query || deviceSearchText(device).includes(query));
  });
}

function renderDevicePicker() {
  const devices = filteredPickerDevices();
  state.devicePickerHighlight = Math.min(
    Math.max(state.devicePickerHighlight, 0),
    Math.max(devices.length - 1, 0),
  );

  elements.devicePickerResults.innerHTML = devices.map((device, index) => {
    const selected = device.device_id === elements.overrideDevice.value;
    const highlighted = index === state.devicePickerHighlight;
    return `
      <button class="device-picker-option device-card${selected ? " selected" : ""}${highlighted ? " highlighted" : ""}"
              type="button"
              role="option"
              aria-selected="${selected}"
              aria-label="${escapeHtml(device.device_name)}, ${escapeHtml(deviceIntegration(device))}"
              data-picker-device-id="${escapeHtml(device.device_id)}">
        ${deviceCardMarkup(device, { selected, highlighted })}
      </button>
    `;
  }).join("");

  elements.devicePickerEmpty.classList.toggle("hidden", devices.length !== 0);
  elements.devicePickerResults.classList.toggle("hidden", devices.length === 0);

  document.querySelectorAll("[data-picker-device-id]").forEach(button => {
    button.addEventListener("click", () => selectPickerDevice(button.dataset.pickerDeviceId));
  });
  renderDeviceTrigger();
}

function renderDeviceOptions(selectedDeviceId = "") {
  elements.overrideDevice.value = selectedDeviceId || "";
  renderDevicePicker();
}

function openDevicePicker() {
  if (elements.devicePickerTrigger.disabled) return;
  state.devicePickerOpen = true;
  state.devicePickerHighlight = 0;
  elements.devicePickerPanel.classList.remove("hidden");
  elements.devicePickerTrigger.setAttribute("aria-expanded", "true");
  elements.devicePickerSearch.value = state.devicePickerQuery;
  renderDevicePicker();
  window.setTimeout(() => elements.devicePickerSearch.focus(), 0);
}

function closeDevicePicker() {
  state.devicePickerOpen = false;
  elements.devicePickerPanel.classList.add("hidden");
  elements.devicePickerTrigger.setAttribute("aria-expanded", "false");
}

function selectPickerDevice(deviceId) {
  elements.overrideDevice.value = deviceId || "";
  const device = selectedDevice();
  elements.overrideEditorTitle.textContent = device?.device_name || "Choose a device";
  state.devicePickerQuery = "";
  elements.devicePickerSearch.value = "";
  closeDevicePicker();
  renderDevicePicker();
}

function movePickerHighlight(direction) {
  const devices = filteredPickerDevices();
  if (!devices.length) return;
  state.devicePickerHighlight = (state.devicePickerHighlight + direction + devices.length) % devices.length;
  renderDevicePicker();
  elements.devicePickerResults.children[state.devicePickerHighlight]?.scrollIntoView({ block: "nearest" });
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
  elements.devicePickerTrigger.disabled = Boolean(item);
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
  closeDevicePicker();
  elements.devicePickerTrigger.disabled = false;
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
  renderAnalysis();
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
elements.refreshAnalysisButton.addEventListener("click", refresh);
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
elements.devicePickerTrigger.addEventListener("click", () => {
  state.devicePickerOpen ? closeDevicePicker() : openDevicePicker();
});

elements.devicePickerSearch.addEventListener("input", event => {
  state.devicePickerQuery = event.target.value;
  state.devicePickerHighlight = 0;
  renderDevicePicker();
});

elements.devicePickerSearch.addEventListener("keydown", event => {
  if (event.key === "ArrowDown") {
    event.preventDefault();
    movePickerHighlight(1);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    movePickerHighlight(-1);
  } else if (event.key === "Enter") {
    event.preventDefault();
    const device = filteredPickerDevices()[state.devicePickerHighlight];
    if (device) selectPickerDevice(device.device_id);
  } else if (event.key === "Escape") {
    event.preventDefault();
    closeDevicePicker();
    elements.devicePickerTrigger.focus();
  }
});

document.addEventListener("click", event => {
  if (state.devicePickerOpen && !elements.devicePicker.contains(event.target)) {
    closeDevicePicker();
  }
});

elements.overridePolicy.addEventListener("change", updateMonthVisibility);
elements.deleteOverrideButton.addEventListener("click", deleteOverride);
elements.cancelOverrideButton.addEventListener("click", closeOverrideEditor);
elements.cancelOverrideButtonBottom.addEventListener("click", closeOverrideEditor);

refresh();
window.setInterval(refresh, 1500);

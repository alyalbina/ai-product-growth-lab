/* The pipeline writes a self-contained results-data.js for offline/GitHub Pages use.
   Optional report.json loading never manufactures fallback metrics. */
(function () {
  "use strict";
  const localDashboard = document.getElementById("local-dashboard");
  if (localDashboard && location.hostname && !["localhost", "127.0.0.1", "[::1]"].includes(location.hostname)) {
    localDashboard.hidden = true;
  }
  const experimentSection = document.getElementById("experiment");
  if (experimentSection && !experimentSection.textContent.includes("common expiry cutoff")) {
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = "Design limitation: equal grant budgets do not imply equal D7 credit availability. " +
      "The control's seven-day TTL expires at D7; later treatment credits can remain until the start of D11. " +
      "A real pilot should use a common expiry cutoff and assess post-reward D14/D30 before claiming habit formation.";
    experimentSection.appendChild(note);
  }
  const script = document.createElement("script");
  script.src = "results-data.js";
  script.onload = function () {
    if (window.GROWTH_LAB_RESULTS) render(window.GROWTH_LAB_RESULTS);
  };
  document.head.appendChild(script);
  function render(report) {
    const target = document.getElementById("result-summary");
    const summary = report.summary || report.metrics || [];
    const rows = Array.isArray(summary) ? summary : Object.values(summary);
    if (!rows.length) return;
    target.replaceChildren();
    const grid = document.createElement("div");
    grid.className = "result-grid";
    const experiment = report.experiment || report.experiment_report;
    rows.forEach(function (row) {
      const cell = document.createElement("div");
      const label = document.createElement("span");
      label.textContent = row.variant === "control" ? "CONTROL / MEANINGFUL D7" : "TREATMENT / MEANINGFUL D7";
      const value = document.createElement("strong");
      value.textContent = Number.isFinite(row.meaningful_d7) ? (100 * row.meaningful_d7).toFixed(1) + "%" : "Undefined";
      const detail = document.createElement("small");
      const eligible = experiment && experiment.primary ? experiment.primary[row.variant + "_n"] : null;
      detail.textContent = eligible == null ? (row.users || 0).toLocaleString() + " assigned users" : eligible.toLocaleString() + " eligible users for D7";
      cell.append(label, value, detail);
      grid.appendChild(cell);
    });
    if (experiment && experiment.primary) {
      const primary = experiment.primary;
      const effect = document.createElement("div");
      const label = document.createElement("span");
      label.textContent = "ABSOLUTE EFFECT / 95% CI";
      const value = document.createElement("strong");
      value.textContent = pp(primary.effect) + " pp";
      const detail = document.createElement("small");
      detail.textContent = "[" + pp(primary.ci_low) + ", " + pp(primary.ci_high) + "] pp";
      effect.append(label, value, detail);
      grid.appendChild(effect);
    }
    target.appendChild(grid);
    const note = document.createElement("p");
    const findings = document.getElementById("findings");
    const hasExpiryNote = findings && findings.textContent.includes("Critical interpretation:");
    note.className = hasExpiryNote ? "" : "note";
    note.textContent = hasExpiryNote ?
      "Calculated from the published seeded synthetic run. These are model outcomes, not Monolit results. Inspect confidence intervals and exact eligible counts in the dashboard." :
      "Critical interpretation: the seven-day credit TTL expires the control grant at the beginning of D7; later treatment grants can remain available until the start of D11. The large D7 contrast partly reflects credit availability and does not isolate habit formation. Inspect post-reward D14/D30 and align expiry cutoffs in a real pilot. These are model outcomes, not Monolit results.";
    target.appendChild(note);
    if (experiment && experiment.decision) {
      document.getElementById("model-decision").textContent = "Default model decision: " + experiment.decision + ". This decision concerns the simulation only.";
    }
    if (report.scenario_comparison && report.scenario_comparison.length) renderScenarios(report.scenario_comparison);
  }
  function signed(value, digits) {
    return Number.isFinite(value) ? (value >= 0 ? "+" : "") + value.toFixed(digits) : "Undefined";
  }
  function pp(value) {
    return Number.isFinite(value) ? signed(value * 100, 2) : "Undefined";
  }
  function renderScenarios(scenarios) {
    const target = document.getElementById("scenario-results");
    const wrapper = document.createElement("div");
    wrapper.className = "table-scroll";
    const table = document.createElement("table");
    const caption = document.createElement("caption");
    caption.textContent = "Calculated scenario outcomes · synthetic model only · treatment minus control";
    table.appendChild(caption);
    const head = document.createElement("thead");
    const row = document.createElement("tr");
    ["Scenario", "Meaningful D7 effect (95% CI)", "Contribution / user effect (95% CI)", "Model decision"].forEach(function (label) {
      const cell = document.createElement("th");
      cell.scope = "col";
      cell.textContent = label;
      row.appendChild(cell);
    });
    head.appendChild(row);
    table.appendChild(head);
    const body = document.createElement("tbody");
    scenarios.forEach(function (scenario) {
      const experiment = scenario.experiment;
      const primary = experiment.primary;
      const economics = experiment.economics;
      const cells = [scenario.scenario,
        pp(primary.effect) + " pp [" + pp(primary.ci_low) + ", " + pp(primary.ci_high) + "]",
        "$" + signed(economics.effect, 2) + " [" + signed(economics.ci_low, 2) + ", " + signed(economics.ci_high, 2) + "]",
        experiment.decision];
      const row = document.createElement("tr");
      cells.forEach(function (value) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
      });
      body.appendChild(row);
    });
    table.appendChild(body);
    wrapper.appendChild(table);
    target.appendChild(wrapper);
  }
}());

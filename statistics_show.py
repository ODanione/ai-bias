import json
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, make_response

app = Flask(__name__)

DATA_FILE = Path("statistics.json")


def load_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"{DATA_FILE} not found in current directory.")
    with DATA_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("statistics.json must contain a JSON array.")
    return data


@app.route("/data")
def get_data():
    try:
        data = load_data()
        return jsonify(data)
    except Exception as e:
        return make_response({"error": str(e)}, 500)


@app.route("/")
def index():
    # Single-page app with vanilla JS
    html = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Person Statistics Explorer</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <style>
    :root {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background-color: #f3f4f6;
      color: #111827;
    }
    body {
      margin: 0;
      padding: 0;
    }
    .page {
      max-width: 1200px;
      margin: 0 auto;
      padding: 1.5rem;
    }
    h1 {
      margin-top: 0;
      font-size: 1.7rem;
    }
    .top-bar {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 1rem;
      align-items: center;
      margin-bottom: 1rem;
    }
    .pill {
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 999px;
      background: #e5e7eb;
      font-size: 0.85rem;
    }
    .pill strong {
      font-weight: 600;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
      gap: 1.5rem;
    }
    @media (max-width: 900px) {
      .layout {
        grid-template-columns: 1fr;
      }
    }
    .card {
      background: white;
      border-radius: 0.75rem;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      padding: 1rem 1.25rem;
    }
    .card h2 {
      font-size: 1.1rem;
      margin-top: 0;
      margin-bottom: 0.75rem;
    }
    .filters {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      max-height: 70vh;
      overflow-y: auto;
      padding-right: 0.25rem;
    }
    .filter-group {
      border-radius: 0.6rem;
      padding: 0.5rem 0.6rem 0.6rem;
      background: #f9fafb;
      border: 1px solid #e5e7eb;
    }
    .filter-group label {
      font-size: 0.8rem;
      font-weight: 600;
      color: #4b5563;
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 0.25rem;
    }
    .filter-group small {
      font-weight: 400;
      font-size: 0.7rem;
      color: #6b7280;
    }
    .filter-select {
      width: 100%;
      min-height: 2.2rem;
      font-size: 0.9rem;
      border-radius: 0.5rem;
      border: 1px solid #d1d5db;
      padding: 0.25rem 0.4rem;
      background-color: white;
    }
    .filter-select:focus {
      outline: 2px solid #3b82f6;
      outline-offset: 1px;
      border-color: #3b82f6;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 0.25rem;
      margin-top: 0.25rem;
    }
    .chip {
      font-size: 0.7rem;
      padding: 0.1rem 0.4rem;
      border-radius: 999px;
      background: #e5e7eb;
      color: #374151;
    }
    .chip--active {
      background: #bfdbfe;
      color: #1d4ed8;
    }
    .stats-attributes {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1rem;
    }
    .stat-block {
      border-radius: 0.75rem;
      border: 1px solid #e5e7eb;
      background: #f9fafb;
      padding: 0.75rem 0.8rem;
      max-height: 260px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .stat-block h3 {
      font-size: 0.9rem;
      margin: 0 0 0.2rem;
      display: flex;
      justify-content: space-between;
      gap: 0.5rem;
      align-items: baseline;
    }
    .stat-block h3 span {
      font-size: 0.75rem;
      font-weight: 400;
      color: #6b7280;
    }
    .numeric-summary {
      font-size: 0.75rem;
      color: #4b5563;
      margin-bottom: 0.4rem;
    }
    .stat-table-wrap {
      overflow: auto;
      margin: 0.25rem -0.8rem -0.6rem;
      padding: 0 0.8rem 0.6rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8rem;
    }
    th, td {
      padding: 0.15rem 0.1rem;
      text-align: left;
      white-space: nowrap;
    }
    th {
      font-weight: 600;
      color: #6b7280;
      border-bottom: 1px solid #e5e7eb;
    }
    tbody tr:nth-child(even) {
      background: #f3f4f6;
    }
    .value-cell {
      max-width: 160px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .count-cell, .share-cell {
      text-align: right;
      font-variant-numeric: tabular-nums;
      padding-left: 0.5rem;
    }
    .bar-cell {
      width: 60px;
    }
    .bar {
      height: 6px;
      border-radius: 999px;
      background: #d1d5db;
      overflow: hidden;
    }
    .bar-inner {
      height: 100%;
      border-radius: 999px;
      background: #3b82f6;
      width: 0%;
    }
    .muted {
      color: #6b7280;
      font-size: 0.8rem;
    }
    .error {
      color: #b91c1c;
      background: #fee2e2;
      border: 1px solid #fecaca;
      border-radius: 0.75rem;
      padding: 0.75rem 1rem;
      margin-top: 1rem;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.1rem 0.5rem;
      border-radius: 999px;
      background: #e0f2fe;
      color: #0369a1;
      font-size: 0.7rem;
      font-weight: 500;
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="top-bar">
      <div>
        <h1>Person Statistics Explorer</h1>
        <div class="muted">
          Interactively explore attribute distributions and filter the dataset.
        </div>
      </div>
      <div>
        <span class="pill" id="summary-pill">
          <strong>Loading data…</strong>
        </span>
      </div>
    </div>

    <div id="error" class="error" style="display:none;"></div>

    <div class="layout" id="main-layout" style="display:none;">
      <section class="card">
        <h2>Filters</h2>
        <div class="muted" style="margin-bottom:0.5rem;">
          Select one or more values for any attribute to narrow the dataset.
        </div>
        <div class="filters" id="filters"></div>
      </section>

      <section class="card">
        <h2>Attribute statistics</h2>
        <div class="muted" style="margin-bottom:0.5rem;">
          Counts and shares are computed for the <strong>currently filtered subset</strong>.
        </div>
        <div class="stats-attributes" id="stats"></div>
      </section>
    </div>
  </div>

  <script>
    let rawData = [];
    let attributes = [];

    function showError(msg) {
      const el = document.getElementById("error");
      el.textContent = msg;
      el.style.display = "block";
    }

    function setSummary(total, filtered) {
      const pill = document.getElementById("summary-pill");
      pill.innerHTML = "";
      const strong = document.createElement("strong");
      strong.textContent = filtered.toString();
      pill.appendChild(strong);
      pill.append(" persons shown");

      if (filtered !== total) {
        const span = document.createElement("span");
        span.className = "muted";
        span.style.marginLeft = "0.35rem";
        span.textContent = `(of ${total} total)`;
        pill.appendChild(span);
      }
    }

    function toDisplayValue(value) {
      if (value === null || value === undefined) return "(missing)";
      if (typeof value === "boolean") return value ? "true" : "false";
      return String(value);
    }

    function inferAttributes(data) {
      const keys = new Set();
      data.forEach(item => {
        Object.keys(item || {}).forEach(k => keys.add(k));
      });
      return Array.from(keys);
    }

    function buildFilters() {
      const container = document.getElementById("filters");
      container.innerHTML = "";

      attributes.forEach(attr => {
        const group = document.createElement("div");
        group.className = "filter-group";

        const label = document.createElement("label");
        label.textContent = attr;

        const small = document.createElement("small");
        small.textContent = "Multi-select (Ctrl / Cmd + click)";
        label.appendChild(small);

        const select = document.createElement("select");
        select.className = "filter-select";
        select.setAttribute("multiple", "multiple");
        select.dataset.attr = attr;

        const valuesSet = new Set();
        rawData.forEach(p => {
          const v = p ? p[attr] : undefined;
          valuesSet.add(toDisplayValue(v));
        });
        const values = Array.from(valuesSet).sort((a, b) => a.localeCompare(b));

        values.forEach(v => {
          const opt = document.createElement("option");
          opt.value = v;
          opt.textContent = v;
          select.appendChild(opt);
        });

        select.addEventListener("change", () => updateEverything());

        group.appendChild(label);
        group.appendChild(select);

        const chips = document.createElement("div");
        chips.className = "chips";
        chips.dataset.attr = attr;
        group.appendChild(chips);

        container.appendChild(group);
      });
    }

    function getActiveFilters() {
      const selects = document.querySelectorAll(".filter-select");
      const filters = {};

      selects.forEach(select => {
        const attr = select.dataset.attr;
        const selected = Array.from(select.selectedOptions).map(o => o.value);
        if (selected.length > 0) {
          filters[attr] = selected;
        }
      });

      return filters;
    }

    function applyFilters() {
      const filters = getActiveFilters();
      updateFilterChips(filters);

      const filtered = rawData.filter(person => {
        return Object.entries(filters).every(([attr, values]) => {
          const v = toDisplayValue(person[attr]);
          return values.includes(v);
        });
      });

      return filtered;
    }

    function updateFilterChips(filters) {
      attributes.forEach(attr => {
        const chipsContainer = document.querySelector(`.chips[data-attr="${attr}"]`);
        if (!chipsContainer) return;
        chipsContainer.innerHTML = "";

        const values = filters[attr] || [];
        if (values.length === 0) return;

        values.forEach(v => {
          const span = document.createElement("span");
          span.className = "chip chip--active";
          span.textContent = v;
          chipsContainer.appendChild(span);
        });
      });
    }

    function computeStats(data) {
      const stats = {};
      const total = data.length;

      attributes.forEach(attr => {
        const counts = {};
        const numericValues = [];

        data.forEach(person => {
          const rawVal = person[attr];
          const disp = toDisplayValue(rawVal);
          counts[disp] = (counts[disp] || 0) + 1;

          if (typeof rawVal === "number" && !Number.isNaN(rawVal)) {
            numericValues.push(rawVal);
          }
        });

        let numeric = null;
        if (numericValues.length > 0) {
          let sum = 0;
          let min = numericValues[0];
          let max = numericValues[0];
          numericValues.forEach(v => {
            sum += v;
            if (v < min) min = v;
            if (v > max) max = v;
          });
          numeric = {
            count: numericValues.length,
            avg: sum / numericValues.length,
            min,
            max
          };
        }

        stats[attr] = {
          counts,
          total,
          numeric
        };
      });

      return stats;
    }

    function renderStats(data) {
      const statsContainer = document.getElementById("stats");
      statsContainer.innerHTML = "";

      if (!data || data.length === 0) {
        const div = document.createElement("div");
        div.className = "muted";
        div.textContent = "No persons match the current filters.";
        statsContainer.appendChild(div);
        return;
      }

      const stats = computeStats(data);

      attributes.forEach(attr => {
        const { counts, total, numeric } = stats[attr];
        let maxCount = 0;
        Object.values(counts).forEach(c => { if (c > maxCount) maxCount = c; });
        if (maxCount === 0) maxCount = 1;

        const block = document.createElement("div");
        block.className = "stat-block";

        const title = document.createElement("h3");
        const nameSpan = document.createElement("span");
        nameSpan.textContent = attr;
        const badge = document.createElement("span");
        badge.className = "badge";
        badge.textContent = `${Object.keys(counts).length} values`;
        title.appendChild(nameSpan);
        title.appendChild(badge);
        block.appendChild(title);

        if (numeric) {
          const numDiv = document.createElement("div");
          numDiv.className = "numeric-summary";
          numDiv.textContent =
            `Avg: ${numeric.avg.toFixed(2)} · Min: ${numeric.min} · Max: ${numeric.max}`;
          block.appendChild(numDiv);
        }

        const wrap = document.createElement("div");
        wrap.className = "stat-table-wrap";

        const table = document.createElement("table");
        const thead = document.createElement("thead");
        const headRow = document.createElement("tr");

        ["Value", "Count", "Share", ""].forEach((h, i) => {
          const th = document.createElement("th");
          th.textContent = h;
          if (i === 1 || i === 2) th.style.textAlign = "right";
          headRow.appendChild(th);
        });
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        Object.entries(counts)
          .sort((a, b) => b[1] - a[1])
          .forEach(([value, count]) => {
            const row = document.createElement("tr");

            const valueCell = document.createElement("td");
            valueCell.className = "value-cell";
            valueCell.textContent = value;
            row.appendChild(valueCell);

            const countCell = document.createElement("td");
            countCell.className = "count-cell";
            countCell.textContent = count.toString();
            row.appendChild(countCell);

            const shareCell = document.createElement("td");
            shareCell.className = "share-cell";
            const share = total > 0 ? (count / total) * 100 : 0;
            shareCell.textContent = share.toFixed(1) + "%";
            row.appendChild(shareCell);

            const barCell = document.createElement("td");
            barCell.className = "bar-cell";
            const bar = document.createElement("div");
            bar.className = "bar";
            const inner = document.createElement("div");
            inner.className = "bar-inner";
            inner.style.width = ((count / maxCount) * 100).toFixed(0) + "%";
            bar.appendChild(inner);
            barCell.appendChild(bar);
            row.appendChild(barCell);

            tbody.appendChild(row);
          });

        table.appendChild(tbody);
        wrap.appendChild(table);
        block.appendChild(wrap);
        statsContainer.appendChild(block);
      });
    }

    function updateEverything() {
      const filtered = applyFilters();
      setSummary(rawData.length, filtered.length);
      renderStats(filtered);
    }

    async function init() {
      try {
        const resp = await fetch("/data");
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}));
          throw new Error(err.error || `Failed to load data (HTTP ${resp.status})`);
        }
        const data = await resp.json();
        if (!Array.isArray(data)) {
          throw new Error("Data is not an array. statistics.json must contain a JSON array.");
        }
        rawData = data;
        attributes = inferAttributes(data);

        if (rawData.length === 0) {
          showError("statistics.json contains an empty array. Nothing to display.");
          document.getElementById("summary-pill").textContent = "0 persons";
          return;
        }

        document.getElementById("main-layout").style.display = "grid";
        buildFilters();
        updateEverything();
      } catch (e) {
        console.error(e);
        showError(e.message || "Unknown error while loading data.");
        document.getElementById("summary-pill").textContent = "Error loading data";
      }
    }

    window.addEventListener("DOMContentLoaded", init);
  </script>
</body>
</html>
    '''
    return html


def open_browser():
    webbrowser.open("http://127.0.0.1:3333/")


if __name__ == "__main__":
    # Open the browser shortly after the server starts
    threading.Timer(1.0, open_browser).start()
    app.run(debug=False, port=3333)

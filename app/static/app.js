const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const pct = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
let screenerAlerts = { matches: [], bySymbol: new Map() };

function value(v, suffix = "") {
  if (v === null || v === undefined || Number.isNaN(v)) return "n/a";
  return `${fmt.format(v)}${suffix}`;
}

function compact(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return "n/a";
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(v);
}

function escapeHtml(input) {
  return String(input ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || response.statusText);
  return data;
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((panel) => panel.classList.remove("active"));
      button.classList.add("active");
      document.getElementById(button.dataset.tab).classList.add("active");
      if (button.dataset.tab === "fundamentals") loadFundamentals(false);
      if (button.dataset.tab === "sources") loadSources();
    });
  });
}

async function loadWatchlist() {
  const [data, alerts] = await Promise.all([api("/api/watchlist"), loadScreenerAlerts(false)]);
  const rows = data.items
    .map(
      (row) => {
        const alert = alerts.bySymbol.get(row.symbol);
        return `
        <tr class="${alert ? "watchlist-hit" : ""}">
          <td><strong>${escapeHtml(row.symbol)}</strong></td>
          <td>${renderSignalBadge(alert)}</td>
          <td>${escapeHtml(row.name || "")}</td>
          <td>${escapeHtml(row.sector || "")}</td>
          <td>${escapeHtml(row.note || "")}</td>
          <td class="row-actions">
            <a class="link" href="https://finance.yahoo.com/quote/${encodeURIComponent(row.symbol)}" target="_blank" rel="noreferrer">Yahoo</a>
            <a class="link" href="https://newsweb.oslobors.no/search?query=${encodeURIComponent(row.symbol.replace(".OL", ""))}" target="_blank" rel="noreferrer">NewsWeb</a>
            <a class="link" href="https://keresell-coder.github.io/oslo-screener-dashboard/" target="_blank" rel="noreferrer">Screener</a>
            <button class="secondary" data-remove="${escapeHtml(row.symbol)}">Remove</button>
          </td>
        </tr>
      `;
      },
    )
    .join("");
  document.getElementById("watchlist-table").innerHTML = `
    <table>
      <thead><tr><th>Symbol</th><th>Screener</th><th>Name</th><th>Sector</th><th>Note</th><th>Links</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="6">No watchlist items yet.</td></tr>`}</tbody>
    </table>
  `;
  document.querySelectorAll("[data-remove]").forEach((button) => {
    button.addEventListener("click", async () => {
      await api(`/api/watchlist?watchlist=Core%20Watchlist&symbol=${encodeURIComponent(button.dataset.remove)}`, {
        method: "DELETE",
      });
      await loadWatchlist();
    });
  });
}

function renderSignalBadge(alert) {
  if (!alert) return `<span class="muted">No current signal</span>`;
  const klass = signalClass(alert.signal);
  return `
    <div class="signal-cell">
      <span class="signal-badge ${klass}">${escapeHtml(alert.signal || "Signal")}</span>
      <span class="signal-section">${escapeHtml(alert.section || "")}</span>
    </div>
  `;
}

function signalClass(signal) {
  const value = String(signal || "").toLowerCase();
  if (value.includes("sell")) return "signal-sell";
  if (value.includes("buy")) return "signal-buy";
  return "signal-neutral";
}

async function loadScreenerAlerts(refresh = false) {
  const data = await api(`/api/screener-alerts?watchlist=Core%20Watchlist&refresh=${refresh ? "1" : "0"}`);
  const bySymbol = new Map(data.matches.map((item) => [item.symbol, item]));
  screenerAlerts = { ...data, bySymbol };
  renderScreenerAlerts(screenerAlerts);
  return screenerAlerts;
}

function renderScreenerAlerts(alerts) {
  const target = document.getElementById("screener-alerts");
  if (!target) return;
  if (!alerts.matches?.length) {
    target.innerHTML = `
      <div class="alert-card calm">
        <strong>No watchlist stocks are currently in the Oslo Screener output.</strong>
        <span>Checked ${escapeHtml(alerts.screenerCount ?? 0)} screener symbols. Source: published dashboard, ${escapeHtml(alerts.cacheStatus || "unknown")}.</span>
      </div>
    `;
    return;
  }
  target.innerHTML = `
    <div class="alert-card active-alert">
      <div>
        <strong>${alerts.matchCount} watchlist ${alerts.matchCount === 1 ? "stock is" : "stocks are"} in the Oslo Screener</strong>
        <span>Parsed from ${escapeHtml(alerts.screenerCount)} screener cards. ${escapeHtml(alerts.sourceReliability || "")}</span>
      </div>
      <div class="alert-list">
        ${alerts.matches
          .map(
            (item) => `
              <a class="alert-chip ${signalClass(item.signal)}" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">
                <strong>${escapeHtml(item.symbol)}</strong>
                <span>${escapeHtml(item.signal || "Signal")}</span>
              </a>
            `,
          )
          .join("")}
      </div>
    </div>
  `;
}

async function loadFundamentals(refresh = false) {
  const universe = document.getElementById("fundamental-universe").value;
  const data = await api(`/api/fundamentals?universe=${encodeURIComponent(universe)}&refresh=${refresh ? "1" : "0"}`);
  document.getElementById("fundamental-errors").innerHTML = data.errors?.length
    ? `<div class="error-box">${data.errors.map((err) => `${escapeHtml(err.symbol)}: ${escapeHtml(err.error)}`).join("<br>")}</div>`
    : "";
  const rows = data.rows
    .map(
      (row) => `
      <tr>
        <td>
          <strong>${escapeHtml(row.symbol)}</strong><br>
          <span class="muted">${escapeHtml(row.name || "")}</span>
        </td>
        <td>${escapeHtml(row.sector || "")}</td>
        <td class="number">${value(row.price)}</td>
        <td class="number">${value(row.trailingPE)}</td>
        <td class="number">${value(row.forwardPE)}</td>
        <td class="number">${value(row.priceToBook)}</td>
        <td class="number">${value(row.pnAv)}</td>
        <td class="number">${value(row.enterpriseToEbitda)}</td>
        <td class="number">${value(row.evToEbit)}</td>
        <td class="number">${value(row.epsTrailingTwelveMonths)}</td>
        <td class="number">${value(row.dividendYield, "%")}</td>
        <td class="number">${compact(row.marketCap)}</td>
        <td class="number">${value(row.targetMeanPrice)}</td>
        <td class="number">${value(row.targetUpsidePct, "%")}</td>
        <td>
          <span class="tag">${escapeHtml(row.cacheStatus)}</span><br>
          <span class="muted">${escapeHtml(row.fetchedAt || "")}</span>
        </td>
        <td>
          <a class="link" href="${escapeHtml(row.newswebUrl)}" target="_blank" rel="noreferrer">NewsWeb</a><br>
          <a class="link" href="${escapeHtml(row.tradingViewSearchUrl)}" target="_blank" rel="noreferrer">TradingView</a>
        </td>
      </tr>
    `,
    )
    .join("");
  document.getElementById("fundamentals-table").innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Company</th><th>Sector</th><th class="number">Price</th>
          <th class="number">TTM P/E</th><th class="number">Fwd P/E</th>
          <th class="number">P/B</th><th class="number">P/NAV</th>
          <th class="number">EV/EBITDA</th><th class="number">EV/EBIT</th>
          <th class="number">EPS TTM</th><th class="number">Div Yield</th>
          <th class="number">Mkt Cap</th><th class="number">Target</th>
          <th class="number">Upside</th><th>Source</th><th>Links</th>
        </tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="16">No fundamentals loaded.</td></tr>`}</tbody>
    </table>
  `;
}

async function loadSources() {
  const data = await api("/api/sources");
  document.getElementById("sources-content").innerHTML = Object.entries(data)
    .map(
      ([name, item]) => `
        <article class="source-card">
          <h3>${escapeHtml(name)}</h3>
          ${item.url ? `<a class="link" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.url)}</a>` : ""}
          ${Object.entries(item)
            .filter(([key]) => key !== "url")
            .map(([key, val]) => `<p><strong>${escapeHtml(key)}:</strong> ${escapeHtml(val)}</p>`)
            .join("")}
        </article>
      `,
    )
    .join("");
}

async function boot() {
  setupTabs();
  document.getElementById("add-watchlist-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const symbol = document.getElementById("watchlist-symbol").value;
    const note = document.getElementById("watchlist-note").value;
    await api("/api/watchlist", {
      method: "POST",
      body: JSON.stringify({ watchlist: "Core Watchlist", symbol, note }),
    });
    event.target.reset();
    await loadWatchlist();
  });
  document.getElementById("refresh-watchlist").addEventListener("click", loadWatchlist);
  document.getElementById("refresh-screener-alerts").addEventListener("click", async () => {
    await loadScreenerAlerts(true);
    await loadWatchlist();
  });
  document.getElementById("refresh-fundamentals").addEventListener("click", () => loadFundamentals(true));
  document.getElementById("fundamental-universe").addEventListener("change", () => loadFundamentals(false));
  document.getElementById("reload-sources").addEventListener("click", loadSources);

  try {
    await api("/api/health");
    document.getElementById("health").textContent = "Running";
  } catch {
    document.getElementById("health").textContent = "Offline";
  }
  await loadWatchlist();
}

boot();

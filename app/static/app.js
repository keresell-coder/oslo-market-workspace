const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const pct = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
let screenerAlerts = { matches: [], bySymbol: new Map() };
let watchlistItems = [];

function value(v, suffix = "") {
  if (v === null || v === undefined || Number.isNaN(v)) return "n/a";
  return `${fmt.format(v)}${suffix}`;
}

function signedPctValue(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return "n/a";
  return `${v > 0 ? "+" : ""}${pct.format(v)}%`;
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
  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`Expected JSON from ${path}, got ${text.slice(0, 120) || "empty response"}`);
  }
  if (!response.ok) throw new Error(data.error || response.statusText);
  return data;
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      activateTab(button.dataset.tab);
    });
  });
}

function activateTab(tabName, options = {}) {
  const shouldLoad = options.load !== false;
  document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === tabName));
  document.querySelectorAll(".panel").forEach((panel) => panel.classList.toggle("active", panel.id === tabName));
  if (!shouldLoad) return;
  if (tabName === "fundamentals") loadFundamentals(false);
  if (tabName === "benchmarks") loadBenchmarkOptions();
  if (tabName === "sources") loadSources();
}

async function loadWatchlist() {
  const data = await api("/api/watchlist-overview");
  watchlistItems = data.rows;
  if (data.screenerError) {
    renderScreenerAlertError(new Error(data.screenerError));
  } else {
    const matches = data.rows.filter((row) => row.screenerSignal).map((row) => row.screenerSignal);
    const bySymbol = new Map(matches.map((item) => [item.symbol, item]));
    renderScreenerAlerts({
      matches,
      bySymbol,
      matchCount: matches.length,
      screenerCount: matches.length,
      sourceReliability: "Parsed from the published Oslo Screener Dashboard.",
      cacheStatus: "overview",
    });
  }
  const rows = data.rows
    .map(
      (row) => {
        const alert = row.screenerSignal;
        return `
        <tr class="${alert ? "watchlist-hit" : ""}">
          <td>
            <strong>${escapeHtml(row.symbol)}</strong><br>
            <span class="muted">${escapeHtml(row.name || "")}</span>
          </td>
          <td>${escapeHtml(row.sector || "")}</td>
          <td>${renderSignalBadge(alert)}</td>
          <td>${renderConsensusCell(row)}</td>
          <td>${renderEventCell(row.eventAlert)}</td>
          <td class="row-actions">
            <a class="link" href="${escapeHtml(row.links?.yahoo || "#")}" target="_blank" rel="noreferrer">Yahoo</a>
            <a class="link" href="${escapeHtml(row.links?.newsweb || "#")}" target="_blank" rel="noreferrer">NewsWeb</a>
            <a class="link" href="${escapeHtml(row.links?.screener || "#")}" target="_blank" rel="noreferrer">Screener</a>
            <button class="secondary" data-remove="${escapeHtml(row.symbol)}">Remove</button>
          </td>
        </tr>
      `;
      },
    )
    .join("");
  document.getElementById("watchlist-table").innerHTML = `
    <table>
      <thead><tr><th>Ticker / Name</th><th>Sector</th><th>Screener</th><th>Consensus</th><th>Updates</th><th>Links</th></tr></thead>
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
  document.querySelectorAll("[data-open-fundamentals]").forEach((button) => {
    button.addEventListener("click", async () => {
      await openFundamentalsForSymbol(button.dataset.openFundamentals);
    });
  });
}

function renderConsensusCell(row) {
  const rec = row.consensusRecommendation || {};
  const label = rec.label || "n/a";
  const freshness = consensusFreshness(row.consensusSources || []);
  const sourceCount = row.consensusSourceCount ?? 0;
  const targetMethod = row.consensusTargetMethod || "Open the Fundamentals tab to inspect target source details.";
  return `
    <div class="consensus-cell">
      <button class="consensus-target" data-open-fundamentals="${escapeHtml(row.symbol)}" title="${escapeHtml(targetMethod)}">
        <span>Fundamentals target</span>
        <strong>${value(row.consensusTarget)}</strong>
        <em class="${targetUpsideClass(row.targetUpsidePct)}">${signedPctValue(row.targetUpsidePct)} upside</em>
      </button>
      <div class="consensus-meta">
        <span class="signal-badge ${recommendationClass(label)}">Source-count ${escapeHtml(label)}</span>
        <span class="tag">${escapeHtml(row.consensusConfidence || "missing")}</span>
        <span class="tag">${escapeHtml(sourceCount)} source${sourceCount === 1 ? "" : "s"}</span>
        <span class="tag">${escapeHtml(freshness)}</span>
      </div>
      <span class="muted">${row.consensusAnalystCount ? `${fmt.format(row.consensusAnalystCount)} known analyst refs` : "analyst count n/a"}; not verified weighted advice</span>
      <span class="muted">Target source: ${escapeHtml(row.consensusTargetSource || "n/a")}</span>
    </div>
  `;
}

function targetUpsideClass(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "target-upside";
  if (value > 0) return "target-upside target-upside-positive";
  if (value < 0) return "target-upside target-upside-negative";
  return "target-upside";
}

function consensusFreshness(sources) {
  const statuses = sources.map((source) => source.staleStatus).filter(Boolean);
  if (!statuses.length) return "freshness n/a";
  if (statuses.every((status) => status === "fresh")) return "fresh";
  if (statuses.every((status) => status === "stale")) return "stale";
  if (statuses.includes("fresh")) return "mixed freshness";
  return "freshness unknown";
}

async function openFundamentalsForSymbol(symbol) {
  activateTab("fundamentals", { load: false });
  const universe = document.getElementById("fundamental-universe");
  if (universe) universe.value = "watchlist";
  await loadFundamentals(false);
  const target = Array.from(document.querySelectorAll("[data-fundamental-symbol]")).find(
    (row) => row.dataset.fundamentalSymbol === symbol,
  );
  if (!target) return;
  document.querySelectorAll(".row-focus").forEach((row) => row.classList.remove("row-focus"));
  target.classList.add("row-focus");
  target.scrollIntoView({ behavior: "smooth", block: "center" });
}

function recommendationClass(label) {
  const value = String(label || "").toLowerCase();
  if (value.includes("buy")) return "signal-buy";
  if (value.includes("sell")) return "signal-sell";
  if (value.includes("hold")) return "signal-neutral";
  return "";
}

function renderEventCell(alert) {
  if (!alert || alert.count === 0) {
    return `<span class="muted">No significant updates tracked</span>`;
  }
  const klass = alert.level === "high" ? "signal-sell" : "signal-neutral";
  return `
    <div class="signal-cell">
      <span class="signal-badge ${klass}">${escapeHtml(alert.level || "update")}</span>
      <strong>${escapeHtml(alert.label || "Significant update")}</strong>
      <span class="muted">${escapeHtml(alert.count)} tracked update(s)</span>
    </div>
  `;
}

function metricValue(v, unit = "") {
  if (v === null || v === undefined || Number.isNaN(v)) return "n/a";
  return `${fmt.format(v)}${unit && unit !== "x" ? unit : unit}`;
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

function renderScreenerAlertError(error) {
  const target = document.getElementById("screener-alerts");
  if (!target) return;
  screenerAlerts = { matches: [], bySymbol: new Map(), error: error.message };
  target.innerHTML = `
    <div class="alert-card">
      <strong>Screener alerts unavailable</strong>
      <span>${escapeHtml(error.message)}. The watchlist still loads independently.</span>
    </div>
  `;
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
      <tr data-fundamental-symbol="${escapeHtml(row.symbol)}">
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
          <span class="tag">${escapeHtml(row.targetConfidence || "low")}</span><br>
          <span class="muted">${escapeHtml(row.targetStatus || "single-source")} / ${escapeHtml(row.targetSourceCount ?? 0)} source(s)</span>
          <br><span class="muted">${renderConsensusStatus(row.consensus)}</span>
        </td>
        <td>
          <span class="tag">${escapeHtml(row.cacheStatus)}</span><br>
          <span class="muted">${escapeHtml(row.fetchedAt || "")}</span>
          <br><span class="muted">Target: ${escapeHtml(row.targetPriceSource || "Yahoo/yfinance")}</span>
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
          <th class="number">Mkt Cap</th><th class="number">Yahoo Target</th>
          <th class="number">Target Upside</th><th>Consensus quality</th><th>Source</th><th>Links</th>
        </tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="17">No fundamentals loaded.</td></tr>`}</tbody>
    </table>
  `;
}

async function saveConsensusSource(event) {
  event.preventDefault();
  const body = {
    symbol: document.getElementById("consensus-symbol").value,
    source: document.getElementById("consensus-source").value,
    targetMean: document.getElementById("consensus-target").value,
    targetHigh: document.getElementById("consensus-high").value,
    targetLow: document.getElementById("consensus-low").value,
    analystCount: document.getElementById("consensus-analysts").value,
    recommendation: document.getElementById("consensus-recommendation").value,
    confidence: document.getElementById("consensus-confidence").value,
    sourceUrl: document.getElementById("consensus-url").value,
    methodNote: document.getElementById("consensus-note").value,
  };
  const status = document.getElementById("consensus-editor-status");
  try {
    const result = await api("/api/consensus", {
      method: "POST",
      body: JSON.stringify(body),
    });
    status.textContent = `Saved ${result.sourceCount} consensus source(s) for ${result.symbol}.`;
    document.getElementById("consensus-form").reset();
    await loadWatchlist();
    await loadFundamentals(false);
  } catch (error) {
    status.textContent = `Could not save consensus source: ${error.message}`;
  }
}

function renderConsensusStatus(consensus) {
  if (!consensus?.sources?.length) return "consensus: missing";
  return consensus.sources
    .map((source) => `${source.source}: ${source.staleStatus || "unknown"}`)
    .join("; ");
}

async function loadBenchmarkOptions() {
  if (!watchlistItems.length) {
    try {
      const data = await api("/api/watchlist");
      watchlistItems = data.items;
    } catch (error) {
      document.getElementById("benchmark-content").innerHTML = `
        <div class="error-box">Could not load watchlist symbols: ${escapeHtml(error.message)}</div>
      `;
      return;
    }
  }
  const select = document.getElementById("benchmark-symbol");
  if (!select.options.length) {
    select.innerHTML = watchlistItems
      .map((row) => `<option value="${escapeHtml(row.symbol)}">${escapeHtml(row.symbol)} - ${escapeHtml(row.name || "")}</option>`)
      .join("");
  }
  if (!select.options.length) {
    document.getElementById("benchmark-content").innerHTML = `
      <div class="method-card"><strong>No watchlist symbols</strong><span>Add symbols to the watchlist before loading benchmark context.</span></div>
    `;
    return;
  }
  if (select.options.length && !document.getElementById("benchmark-content").innerHTML) {
    await loadBenchmark(false);
  }
}

async function loadBenchmark(refresh = false) {
  const symbol = document.getElementById("benchmark-symbol").value;
  if (!symbol) return;
  const target = document.getElementById("benchmark-content");
  target.innerHTML = `<div class="method-card"><strong>Loading benchmark context...</strong><span>Free sources may be slow or incomplete.</span></div>`;
  try {
    const data = await api(`/api/benchmarks?symbol=${encodeURIComponent(symbol)}&refresh=${refresh ? "1" : "0"}`);
    target.innerHTML = renderBenchmark(data);
  } catch (error) {
    target.innerHTML = `<div class="error-box">Benchmark could not load for ${escapeHtml(symbol)}: ${escapeHtml(error.message)}</div>`;
  }
}

function renderBenchmark(data) {
  if (!data.groups?.length) {
    return `
      <div class="method-card">
        <strong>No peer group configured for ${escapeHtml(data.symbol)}</strong>
        <span>${escapeHtml(data.message || "Add a peer group before drawing relative valuation context.")}</span>
      </div>
      ${renderSectorContext(data.sectorContext)}
      ${renderOwnHistory(data.ownHistory)}
    `;
  }
  return `
    <div class="benchmark-policy">
      <strong>${escapeHtml(data.symbol)}</strong>
      <span>${escapeHtml(data.policy || "Descriptive benchmark context only.")}</span>
    </div>
    ${renderSectorContext(data.sectorContext)}
    ${data.groups.map(renderBenchmarkGroup).join("")}
    ${renderOwnHistory(data.ownHistory)}
  `;
}

function renderSectorContext(sector) {
  if (!sector) return "";
  return `
    <section class="benchmark-group">
      <div class="benchmark-group-head">
        <div>
          <h3>Sector context</h3>
          <p class="muted">${escapeHtml(sector.requirement || "")}</p>
        </div>
        <span class="tag">${escapeHtml(sector.status || "not configured")}</span>
      </div>
      <div class="source-grid compact-grid">
        <article class="source-card">
          <h3>Current classification</h3>
          <p><strong>Sector:</strong> ${escapeHtml(sector.sector || "n/a")}</p>
          <p><strong>Industry:</strong> ${escapeHtml(sector.industry || "n/a")}</p>
        </article>
        <article class="source-card">
          <h3>Sector benchmark</h3>
          <p>${escapeHtml(sector.message || "No sector benchmark configured.")}</p>
        </article>
      </div>
    </section>
  `;
}

function renderBenchmarkGroup(group) {
  const metricRows = group.metricSummaries
    .map(
      (metric) => `
      <tr>
        <td>
          <strong>${escapeHtml(metric.label)}</strong><br>
          <span class="muted">${escapeHtml(metric.positionNote)}</span>
        </td>
        <td class="number">${metricValue(metric.focusValue, metric.unit)}</td>
        <td class="number">${metricValue(metric.peerMedian, metric.unit)}</td>
        <td class="number">${metricValue(metric.peerMin, metric.unit)}</td>
        <td class="number">${metricValue(metric.peerMax, metric.unit)}</td>
        <td class="number">${metricValue(metric.vsPeerMedianPct, "%")}</td>
        <td class="number">${metric.peerCount}</td>
      </tr>
    `,
    )
    .join("");
  const peerRows = group.items
    .map(
      (row) => `
      <tr>
        <td><strong>${escapeHtml(row.symbol)}</strong><br><span class="muted">${escapeHtml(row.name || "")}</span></td>
        <td>${escapeHtml(row.peerRole || "")}</td>
        <td>${escapeHtml(row.peerMarket || "")}</td>
        <td class="number">${metricValue(row.trailingPE, "x")}</td>
        <td class="number">${metricValue(row.priceToBook, "x")}</td>
        <td class="number">${metricValue(row.enterpriseToEbitda, "x")}</td>
        <td class="number">${metricValue(row.dividendYield, "%")}</td>
        <td><span class="tag">${escapeHtml(row.cacheStatus || "")}</span></td>
      </tr>
    `,
    )
    .join("");
  return `
    <section class="benchmark-group">
      <div class="benchmark-group-head">
        <div>
          <h3>${escapeHtml(group.name)}</h3>
          <p class="muted">${escapeHtml(group.description)}</p>
        </div>
        <span class="tag">${escapeHtml(group.confidence)}</span>
      </div>
      <p class="muted">${escapeHtml(group.confidenceReason)}</p>
      ${group.errors?.length ? `<div class="error-box">${group.errors.map((err) => `${escapeHtml(err.symbol)}: ${escapeHtml(err.error)}`).join("<br>")}</div>` : ""}
      <div class="table-wrap benchmark-table">
        <table>
          <thead>
            <tr><th>Metric</th><th class="number">Company</th><th class="number">Peer median</th><th class="number">Peer min</th><th class="number">Peer max</th><th class="number">Vs median</th><th class="number">Peer count</th></tr>
          </thead>
          <tbody>${metricRows}</tbody>
        </table>
      </div>
      <details class="peer-details">
        <summary>Peer data used</summary>
        <div class="table-wrap benchmark-table">
          <table>
            <thead><tr><th>Company</th><th>Role</th><th>Market</th><th class="number">TTM P/E</th><th class="number">P/B</th><th class="number">EV/EBITDA</th><th class="number">Div Yield</th><th>Source</th></tr></thead>
            <tbody>${peerRows}</tbody>
          </table>
        </div>
      </details>
    </section>
  `;
}

function renderOwnHistory(history) {
  if (!history) return "";
  const rows = history.metrics
    .map(
      (metric) => `
      <tr>
        <td>${escapeHtml(metric.label)}</td>
        <td class="number">${metricValue(metric.current, metric.unit)}</td>
        <td class="number">${metricValue(metric.historyMedian, metric.unit)}</td>
        <td class="number">${metricValue(metric.historyMin, metric.unit)}</td>
        <td class="number">${metricValue(metric.historyMax, metric.unit)}</td>
        <td class="number">${metric.observations}</td>
      </tr>
    `,
    )
    .join("");
  return `
    <section class="benchmark-group">
      <div class="benchmark-group-head">
        <div>
          <h3>Own history</h3>
          <p class="muted">${escapeHtml(history.requirement)}</p>
        </div>
        <span class="tag">${escapeHtml(history.status)}</span>
      </div>
      <div class="table-wrap benchmark-table">
        <table>
          <thead><tr><th>Metric</th><th class="number">Current</th><th class="number">History median</th><th class="number">History min</th><th class="number">History max</th><th class="number">Obs.</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </section>
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
  document.getElementById("benchmark-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await loadBenchmark(false);
  });
  document.getElementById("consensus-form").addEventListener("submit", saveConsensusSource);
  document.getElementById("refresh-benchmark").addEventListener("click", () => loadBenchmark(true));
  document.getElementById("refresh-fundamentals").addEventListener("click", () => loadFundamentals(true));
  document.getElementById("fundamental-universe").addEventListener("change", () => loadFundamentals(false));
  document.getElementById("reload-sources").addEventListener("click", loadSources);

  try {
    await api("/api/health");
    document.getElementById("health").textContent = "Running";
  } catch {
    document.getElementById("health").textContent = "Offline";
  }
  try {
    await loadWatchlist();
  } catch (error) {
    document.getElementById("watchlist-table").innerHTML = `<div class="error-box">Watchlist could not load: ${escapeHtml(error.message)}</div>`;
  }
}

boot();

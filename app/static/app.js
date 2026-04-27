const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const pct = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
let screenerAlerts = { matches: [], bySymbol: new Map() };
let watchlistItems = [];
const peerStatuses = ["draft", "reviewed", "trusted"];
const peerRoles = ["focus company", "Oslo peer", "Nordic peer", "European peer", "international peer", "sector index/proxy"];
let loadingDepth = 0;
const technicalIndicatorGuide = [
  {
    key: "rsi14",
    name: "RSI14",
    shows: "14-day momentum oscillator; low values can indicate oversold conditions, high values can indicate overbought conditions.",
    supportive: "30 or lower",
    neutral: "30 to 70",
    notSupportive: "70 or higher",
  },
  {
    key: "rsi6",
    name: "RSI6",
    shows: "Shorter-term RSI; reacts faster than RSI14 and is noisier.",
    supportive: "30 or lower",
    neutral: "30 to 70",
    notSupportive: "70 or higher",
  },
  {
    key: "rsiDirection",
    name: "RSI direction",
    shows: "Recent change in RSI; positive means momentum is improving, negative means it is weakening.",
    supportive: "Above 0",
    neutral: "0",
    notSupportive: "Below 0",
  },
  {
    key: "mfi14",
    name: "MFI14",
    shows: "Money Flow Index combines price and volume; low values can indicate oversold money flow, high values can indicate overbought money flow.",
    supportive: "20 or lower",
    neutral: "20 to 80",
    notSupportive: "80 or higher",
  },
  {
    key: "macdHistogram",
    name: "MACD histogram",
    shows: "Difference between MACD and its signal line; positive values show improving momentum versus the signal line.",
    supportive: "Above 0",
    neutral: "At 0",
    notSupportive: "Below 0",
  },
  {
    key: "sma50",
    name: "SMA50",
    shows: "50-day simple moving average; interpreted here using the current price distance from SMA50.",
    supportive: "Price more than 2% above SMA50",
    neutral: "Within +/-2% of SMA50",
    notSupportive: "Price more than 2% below SMA50",
  },
  {
    key: "pctAboveSma50",
    name: "Vs SMA50",
    shows: "Percentage distance between current price and the 50-day moving average.",
    supportive: "Above +2%",
    neutral: "-2% to +2%",
    notSupportive: "Below -2%",
  },
  {
    key: "adx14",
    name: "ADX14",
    shows: "Trend-strength indicator; it does not say whether the trend is up or down.",
    supportive: "25 or higher",
    neutral: "20 to 25",
    notSupportive: "Below 20",
  },
];

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

function shortDate(value) {
  if (!value) return "date n/a";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
}

function escapeHtml(input) {
  return String(input ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function loadingMarkup(label) {
  return `<span class="loading-spinner" aria-hidden="true"></span><span>${escapeHtml(label)}</span>`;
}

function setGlobalLoading(label) {
  const health = document.getElementById("health");
  loadingDepth += 1;
  if (health) {
    health.classList.add("is-loading");
    health.innerHTML = loadingMarkup(label);
  }
  return () => {
    loadingDepth = Math.max(0, loadingDepth - 1);
    if (loadingDepth === 0 && health) {
      health.classList.remove("is-loading");
      health.textContent = "Running";
    }
  };
}

async function withLoading(label, control, task) {
  const done = setGlobalLoading(label);
  let originalContent = "";
  if (control) {
    originalContent = control.innerHTML;
    control.disabled = true;
    control.classList.add("is-loading");
    control.innerHTML = loadingMarkup(label);
  }
  try {
    return await task();
  } finally {
    if (control) {
      control.disabled = false;
      control.classList.remove("is-loading");
      control.innerHTML = originalContent;
    }
    done();
  }
}

function renderLoadingPanel(label) {
  return `<div class="loading-panel">${loadingMarkup(label)}</div>`;
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
  if (tabName === "technical") loadTechnicalIndicators(false);
  if (tabName === "benchmarks") loadBenchmarkOptions();
  if (tabName === "sources") loadSources();
}

async function loadWatchlist() {
  document.getElementById("watchlist-table").innerHTML = renderLoadingPanel("Loading watchlist");
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
      sourceReliability: "Parsed from the published RSI14 screener dashboard.",
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
            <br><span class="muted">${escapeHtml(row.sector || "")}</span>
          </td>
          <td>${renderPriceCell(row.priceSummary || row)}</td>
          <td>${renderRsiScreenerCell(alert)}</td>
          <td>${renderTechnicalWatchlistCell(row)}</td>
          <td>${renderFundamentalHighlight(row)}</td>
          <td>${renderOwnHistoryWatchlistCell(row)}</td>
          <td>${renderPeerContext(row)}</td>
          <td>${renderConsensusTargetCell(row)}</td>
          <td>${renderConsensusRatingCell(row)}</td>
          <td>${renderEventCell(row.eventAlert)}</td>
          <td>${renderActionsCell(row)}</td>
        </tr>
      `;
      },
    )
    .join("");
  document.getElementById("watchlist-table").innerHTML = `
    <table class="watchlist-synthesis">
      <thead>
        <tr>
          <th>Company</th>
          <th class="number">Last price</th>
          <th>RSI14 screener</th>
          <th>Technical</th>
          <th>Multiples</th>
          <th>Own history</th>
          <th>Peer context</th>
          <th>Target range</th>
          <th>Rating</th>
          <th>Updates</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="11">No watchlist items yet.</td></tr>`}</tbody>
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
  document.querySelectorAll("[data-open-benchmarks]").forEach((button) => {
    button.addEventListener("click", async () => {
      await openBenchmarkForSymbol(button.dataset.openBenchmarks);
    });
  });
  document.querySelectorAll("[data-open-technical]").forEach((button) => {
    button.addEventListener("click", async () => {
      await openTechnicalForSymbol(button.dataset.openTechnical);
    });
  });
}

function renderPriceCell(priceSummary) {
  return `
    <div class="number-stack">
      <strong>${value(priceSummary.price)}</strong>
      <span class="muted">${escapeHtml(priceSummary.currency || "NOK")}</span>
      <span class="muted">${escapeHtml(shortDate(priceSummary.fetchedAt))}</span>
    </div>
  `;
}

function toneClass(tone) {
  if (tone === "warning") return "signal-sell";
  if (tone === "info") return "signal-neutral";
  if (tone === "missing") return "";
  return "signal-buy";
}

function peerStatusClass(status) {
  if (status === "trusted") return "signal-buy";
  if (status === "reviewed") return "signal-neutral";
  if (status === "missing") return "";
  return "signal-draft";
}

function renderFundamentalHighlight(row) {
  const item = row.fundamentalHighlight || {};
  return `
    <button class="summary-button" data-open-fundamentals="${escapeHtml(row.symbol)}">
      <span class="signal-badge ${toneClass(item.tone)}">${escapeHtml(item.label || "Fundamentals")}</span>
      <strong>${escapeHtml(item.detail || "Open Fundamentals")}</strong>
      <span class="muted">${escapeHtml(row.priceSummary?.source || "Yahoo/yfinance")} / ${escapeHtml(shortDate(row.priceSummary?.fetchedAt))}</span>
    </button>
  `;
}

function renderOwnHistoryWatchlistCell(row) {
  const history = row.ownHistorySignal || {};
  let label = history.label || "Own history";
  let detail = "Needs more observations";
  let klass = "signal-draft";
  if (history.status === "available") {
    detail = history.detail || "Signal available";
    klass = "signal-neutral";
  } else if (history.status === "no watchlist signal") {
    detail = "No large gap crossed the threshold.";
    klass = "signal-neutral";
  }
  return `
    <button class="summary-button compact-summary" data-open-fundamentals="${escapeHtml(row.symbol)}">
      <span class="signal-badge ${klass}">${escapeHtml(label)}</span>
      <strong>${escapeHtml(detail)}</strong>
      <span class="muted">${escapeHtml(history.confidence || "source-labeled screening data")}</span>
    </button>
  `;
}

function renderPeerContext(row) {
  const peer = row.peerContext || {};
  const vsMedian = peer.vsPeerMedianPct === null || peer.vsPeerMedianPct === undefined ? "" : ` (${signedPctValue(peer.vsPeerMedianPct)} vs median)`;
  return `
    <button class="summary-button" data-open-benchmarks="${escapeHtml(row.symbol)}">
      <span class="signal-badge ${peerStatusClass(peer.status)}">${escapeHtml(peer.status || "peer context")}</span>
      <strong>${escapeHtml(peer.label || "Peer context")}${escapeHtml(vsMedian)}</strong>
      <span class="muted">${escapeHtml(peer.detail || "Open Benchmarks")}</span>
    </button>
  `;
}

function renderConsensusTargetCell(row) {
  const target = row.consensusTargetSummary || {};
  const method = target.method || "Open the Fundamentals tab to inspect target source details.";
  return `
    <div class="consensus-cell">
      <button class="consensus-target" data-open-fundamentals="${escapeHtml(row.symbol)}" title="${escapeHtml(method)}">
        <span>Consensus target</span>
        <strong>${value(target.target)}</strong>
        <em class="${targetUpsideClass(target.targetUpsidePct)}">${signedPctValue(target.targetUpsidePct)}</em>
      </button>
      <div class="consensus-meta">
        <span class="tag">Low ${value(target.targetLow)}</span>
        <span class="tag">High ${value(target.targetHigh)}</span>
      </div>
      <span class="muted">${escapeHtml(target.providerRows ?? 0)} provider row${target.providerRows === 1 ? "" : "s"}; overlaps not deduped</span>
    </div>
  `;
}

function renderConsensusRatingCell(row) {
  const rating = row.consensusRatingSummary || {};
  const label = rating.label || "n/a";
  const counts = rating.counts || {};
  const countLine = `B/H/S rows ${counts.BUY || 0}/${counts.HOLD || 0}/${counts.SELL || 0}`;
  const analystText = rating.reportedAnalystRefs
    ? `${fmt.format(rating.reportedAnalystRefs)} reported analyst refs`
    : "analyst refs n/a";
  return `
    <div class="signal-cell">
      <span class="signal-badge ${recommendationClass(label)}">${escapeHtml(label)}</span>
      <strong>${escapeHtml(analystText)}</strong>
      <span class="muted">${escapeHtml(countLine)}</span>
      <span class="muted">${escapeHtml(rating.confidence || "low confidence")} / ${escapeHtml(rating.providerRows ?? 0)} provider row${rating.providerRows === 1 ? "" : "s"}</span>
      <span class="muted">Not verified weighted advice</span>
    </div>
  `;
}

function renderActionsCell(row) {
  return `
    <div class="row-actions">
      <a class="link" href="${escapeHtml(row.links?.yahoo || "#")}" target="_blank" rel="noreferrer">Yahoo</a>
      <a class="link" href="${escapeHtml(row.links?.newsweb || "#")}" target="_blank" rel="noreferrer">NewsWeb</a>
      <a class="link" href="${escapeHtml(row.links?.screener || "#")}" target="_blank" rel="noreferrer">RSI14</a>
      <button class="secondary" data-remove="${escapeHtml(row.symbol)}">Remove</button>
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

function historySignalClass(signal) {
  if (!signal || signal.status !== "available") return "signal-draft";
  return "signal-neutral";
}

function renderHistoricalContext(row) {
  const context = row.historicalContext || {};
  const signal = context.watchlistSignal || {};
  const priceWindow = context.priceWindow || {};
  const snapshot = context.snapshotHistory || {};
  const priceRange =
    priceWindow.low !== null && priceWindow.low !== undefined && priceWindow.high !== null && priceWindow.high !== undefined
      ? `${value(priceWindow.low)}-${value(priceWindow.high)} ${priceWindow.currency || row.currency || ""}`
      : "52w range n/a";
  const rangePosition =
    priceWindow.rangePositionPct === null || priceWindow.rangePositionPct === undefined
      ? "n/a"
      : `${pct.format(priceWindow.rangePositionPct)}%`;
  const priceObs = priceWindow.observationCount
    ? `${priceWindow.observationCount} closes`
    : "price obs n/a";
  const snapshotCount = snapshot.snapshotCount ?? 0;
  return `
    <div class="signal-cell history-cell">
      <span class="signal-badge ${historySignalClass(signal)}">${escapeHtml(signal.label || "Own history")}</span>
      <div class="history-summary-grid">
        <span>
          <em>52w position</em>
          <strong>${escapeHtml(rangePosition)}</strong>
          <small>${escapeHtml(priceRange)}</small>
        </span>
        <span>
          <em>Snapshots</em>
          <strong>${escapeHtml(snapshotCount)} obs</strong>
          <small>${escapeHtml(snapshot.status || "history n/a")}</small>
        </span>
      </div>
      <span class="muted">${escapeHtml(priceObs)}; ${escapeHtml(priceWindow.confidence || snapshot.metrics?.[0]?.confidence || "screening-grade")}</span>
      ${renderHistoricalContextDetails(context)}
    </div>
  `;
}

function renderHistoricalContextDetails(context) {
  const priceWindow = context.priceWindow || {};
  const snapshot = context.snapshotHistory || {};
  return `
    <details class="history-details">
      <summary>Price and multiple detail</summary>
      ${renderPriceHistoryDetails(priceWindow)}
      ${renderSnapshotHistoryDetails(snapshot)}
      <p class="muted">${escapeHtml(context.watchlistSignal?.detail || "Needs more dated observations before stronger own-history context is shown.")}</p>
      <p class="muted">${escapeHtml(context.policy || "Descriptive context only.")}</p>
    </details>
  `;
}

function renderPriceHistoryDetails(priceWindow) {
  const quarterRows = (priceWindow.quarterWindows || [])
    .map(
      (quarter) => `
        <tr>
          <td>${escapeHtml(quarter.label)}</td>
          <td class="number">${metricValue(quarter.close, "")}</td>
          <td class="number">${metricValue(quarter.median, "")}</td>
          <td class="number">${metricValue(quarter.low, "")}</td>
          <td class="number">${metricValue(quarter.high, "")}</td>
          <td class="number">${escapeHtml(quarter.observationCount ?? 0)}</td>
        </tr>
      `,
    )
    .join("");
  return `
    <div class="history-subsection">
      <strong>52-week price window</strong>
      <div class="history-range">
        <span>${metricValue(priceWindow.low, "")}</span>
        <meter min="0" max="100" value="${Number(priceWindow.rangePositionPct ?? 0)}"></meter>
        <span>${metricValue(priceWindow.high, "")}</span>
      </div>
      <p class="muted">${escapeHtml(priceWindow.observationCount ?? 0)} daily closes; ${escapeHtml(priceWindow.confidence || "missing")}; ${escapeHtml(priceWindow.source || "source n/a")}; last ${escapeHtml(shortDate(priceWindow.lastObservationAt || priceWindow.fetchedAt))}.</p>
      <div class="mini-table-wrap">
        <table class="mini-table">
          <thead><tr><th>Quarter</th><th class="number">Close</th><th class="number">Median</th><th class="number">Low</th><th class="number">High</th><th class="number">Obs.</th></tr></thead>
          <tbody>${quarterRows || `<tr><td colspan="6">Quarter windows unavailable.</td></tr>`}</tbody>
        </table>
      </div>
    </div>
  `;
}

function renderSnapshotHistoryDetails(snapshot) {
  const gapRows = (snapshot.largestGaps || [])
    .map(
      (metric) => `
        <tr>
          <td>${escapeHtml(metric.label)}</td>
          <td class="number">${metricValue(metric.current, metric.unit)}</td>
          <td class="number">${metricValue(metric.historyMedian, metric.unit)}</td>
          <td class="number">${signedPctValue(metric.vsHistoryMedianPct)}</td>
          <td class="number">${escapeHtml(metric.observations ?? 0)}</td>
        </tr>
      `,
    )
    .join("");
  const metricRows = (snapshot.metrics || [])
    .map(
      (metric) => `
        <tr>
          <td>${escapeHtml(metric.label)}</td>
          <td class="number">${metricValue(metric.current, metric.unit)}</td>
          <td class="number">${metricValue(metric.historyMedian, metric.unit)}</td>
          <td class="number">${metricValue(metric.historyMin, metric.unit)}</td>
          <td class="number">${metricValue(metric.historyMax, metric.unit)}</td>
          <td class="number">${metric.percentileInOwnHistory === null || metric.percentileInOwnHistory === undefined ? "n/a" : `${pct.format(metric.percentileInOwnHistory)}%`}</td>
          <td class="number">${signedPctValue(metric.vsHistoryMedianPct)}</td>
          <td class="number">${escapeHtml(metric.observations ?? 0)}</td>
        </tr>
      `,
    )
    .join("");
  return `
    <div class="history-subsection">
      <strong>Largest own-multiple gaps</strong>
      <div class="mini-table-wrap">
        <table class="mini-table">
          <thead><tr><th>Metric</th><th class="number">Current</th><th class="number">Median</th><th class="number">Gap</th><th class="number">Obs.</th></tr></thead>
          <tbody>${gapRows || `<tr><td colspan="5">Need at least two local snapshots.</td></tr>`}</tbody>
        </table>
      </div>
      <strong>Snapshot history</strong>
      <div class="mini-table-wrap">
        <table class="mini-table wide-mini-table">
          <thead><tr><th>Metric</th><th class="number">Current</th><th class="number">Median</th><th class="number">Min</th><th class="number">Max</th><th class="number">Pctile</th><th class="number">Gap</th><th class="number">Obs.</th></tr></thead>
          <tbody>${metricRows || `<tr><td colspan="8">Snapshot metrics unavailable.</td></tr>`}</tbody>
        </table>
      </div>
      <p class="muted">${escapeHtml(snapshot.requirement || "")}</p>
    </div>
  `;
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

async function openTechnicalForSymbol(symbol) {
  activateTab("technical", { load: false });
  const universe = document.getElementById("technical-universe");
  if (universe) universe.value = "watchlist";
  await loadTechnicalIndicators(false);
  const target = Array.from(document.querySelectorAll("[data-technical-symbol]")).find(
    (row) => row.dataset.technicalSymbol === symbol,
  );
  if (!target) return;
  document.querySelectorAll(".row-focus").forEach((row) => row.classList.remove("row-focus"));
  target.classList.add("row-focus");
  target.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function openBenchmarkForSymbol(symbol) {
  activateTab("benchmarks", { load: false });
  await loadBenchmarkOptions();
  const select = document.getElementById("benchmark-symbol");
  if (select) select.value = symbol;
  await loadBenchmark(false);
  document.getElementById("benchmark-content")?.scrollIntoView({ behavior: "smooth", block: "start" });
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

function renderRsiScreenerCell(alert) {
  if (!alert) {
    return `
      <div class="signal-cell">
        <span class="muted">Not in published output</span>
        <span class="muted">RSI14 source missing for this row</span>
      </div>
    `;
  }
  const klass = signalClass(alert.signal);
  const rsi = alert.rsi14 === null || alert.rsi14 === undefined ? "RSI n/a" : `RSI ${value(alert.rsi14)}`;
  return `
    <div class="signal-cell">
      <span class="signal-badge ${klass}">${escapeHtml(alert.signal || "Signal")}</span>
      <strong>${escapeHtml(rsi)}</strong>
      <span class="signal-section">${escapeHtml(alert.section || "Published screener output")}</span>
    </div>
  `;
}

function renderTechnicalWatchlistCell(row) {
  const item = row.technicalSignal;
  if (!item) {
    return `
      <div class="signal-cell">
        <span class="muted">Not in latest.csv</span>
        <span class="muted">Technical source missing for this row</span>
      </div>
    `;
  }
  const dashboard = item.inDashboardScreener ? `<span class="tag dashboard-tag">Dashboard alert</span>` : "";
  return `
    <button class="summary-button compact-summary" data-open-technical="${escapeHtml(row.symbol)}">
      <span class="signal-badge ${signalClass(item.signal)}">${escapeHtml(item.signal || "NEUTRAL")}</span>
      <strong>RSI14 ${renderTechnicalValue("rsi14", item.rsi14)} / RSI6 ${renderTechnicalValue("rsi6", item.rsi6)}</strong>
      <span class="muted">MACD hist ${renderTechnicalValue("macdHistogram", item.macdHistogram)}; ${renderTechnicalValue("pctAboveSma50", item.pctAboveSma50, { suffix: "%", signed: true })} vs SMA50</span>
      <span class="muted">${escapeHtml(item.date || "date n/a")} / ${escapeHtml(item.risk || "risk n/a")}</span>
      ${dashboard}
    </button>
  `;
}

function technicalIndicatorStatus(key, value, row = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "missing";
  if (key === "rsi14" || key === "rsi6") {
    if (value <= 30) return "supportive";
    if (value >= 70) return "not-supportive";
    return "neutral";
  }
  if (key === "mfi14") {
    if (value <= 20) return "supportive";
    if (value >= 80) return "not-supportive";
    return "neutral";
  }
  if (key === "rsiDirection" || key === "macdHistogram") {
    if (value > 0) return "supportive";
    if (value < 0) return "not-supportive";
    return "neutral";
  }
  if (key === "sma50" || key === "pctAboveSma50") {
    const pctFromSma = key === "pctAboveSma50" ? value : row.pctAboveSma50;
    if (pctFromSma === null || pctFromSma === undefined || Number.isNaN(pctFromSma)) return "missing";
    if (pctFromSma > 2) return "supportive";
    if (pctFromSma < -2) return "not-supportive";
    return "neutral";
  }
  if (key === "adx14") {
    if (value >= 25) return "supportive";
    if (value < 20) return "not-supportive";
    return "neutral";
  }
  return "neutral";
}

function technicalStatusLabel(status) {
  if (status === "supportive") return "Supportive";
  if (status === "not-supportive") return "Not supportive";
  if (status === "missing") return "Missing";
  return "Neutral";
}

function renderStatusDot(status) {
  return `<span class="indicator-dot indicator-${escapeHtml(status)}" title="${escapeHtml(technicalStatusLabel(status))}" aria-label="${escapeHtml(technicalStatusLabel(status))}"></span>`;
}

function formatTechnicalValue(value, options = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  const formatted = options.signed ? `${value > 0 ? "+" : ""}${fmt.format(value)}` : fmt.format(value);
  return `${formatted}${options.suffix || ""}`;
}

function renderTechnicalValue(key, value, options = {}, row = {}) {
  const status = technicalIndicatorStatus(key, value, row);
  return `<span class="indicator-value">${escapeHtml(formatTechnicalValue(value, options))}${renderStatusDot(status)}</span>`;
}

function signalClass(signal) {
  const value = String(signal || "").toLowerCase();
  if (value.includes("sell")) return "signal-sell";
  if (value.includes("buy")) return "signal-buy";
  return "signal-neutral";
}

async function loadScreenerAlerts(refresh = false) {
  const target = document.getElementById("screener-alerts");
  if (target) target.innerHTML = renderLoadingPanel("Loading RSI14 screener");
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
      <strong>RSI14 screener unavailable</strong>
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
        <strong>No watchlist stocks are currently in the published RSI14 screener output.</strong>
        <span>Checked ${escapeHtml(alerts.screenerCount ?? 0)} published screener cards. Source: published dashboard, ${escapeHtml(alerts.cacheStatus || "unknown")}.</span>
      </div>
    `;
    return;
  }
  target.innerHTML = `
    <div class="alert-card active-alert">
      <div>
        <strong>${alerts.matchCount} watchlist ${alerts.matchCount === 1 ? "stock is" : "stocks are"} in the RSI14 screener output</strong>
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

async function loadTechnicalIndicators(refresh = false) {
  const universe = document.getElementById("technical-universe").value;
  document.getElementById("technical-table").innerHTML = renderLoadingPanel(
    refresh ? "Refreshing technical indicators" : "Loading technical indicators",
  );
  const data = await api(`/api/technical-indicators?universe=${encodeURIComponent(universe)}&refresh=${refresh ? "1" : "0"}`);
  document.getElementById("technical-errors").innerHTML = data.screenerError
    ? `<div class="error-box">Dashboard highlight unavailable: ${escapeHtml(data.screenerError)}</div>`
    : "";
  renderTechnicalSummary(data);
  renderTechnicalGuide();
  const rows = data.rows
    .map(
      (row) => `
        <tr data-technical-symbol="${escapeHtml(row.symbol)}" class="${row.inDashboardScreener ? "watchlist-hit" : ""}">
          <td>
            <strong>${escapeHtml(row.symbol)}</strong><br>
            <span class="muted">${escapeHtml(row.date || "date n/a")}</span>
            ${row.inDashboardScreener ? `<br><span class="tag dashboard-tag">Dashboard alert</span>` : ""}
          </td>
          <td><span class="signal-badge ${signalClass(row.signal)}">${escapeHtml(row.signal || "NEUTRAL")}</span></td>
          <td class="number">${value(row.close)}</td>
          <td>${renderTechnicalMetricGroup([
            ["RSI14", "rsi14", row.rsi14],
            ["RSI6", "rsi6", row.rsi6],
            ["RSI dir", "rsiDirection", row.rsiDirection, { signed: true }],
            ["MFI14", "mfi14", row.mfi14],
          ], row)}</td>
          <td>${renderTechnicalMetricGroup([
            ["MACD hist", "macdHistogram", row.macdHistogram],
            ["SMA50", "sma50", row.sma50],
            ["Vs SMA50", "pctAboveSma50", row.pctAboveSma50, { suffix: "%", signed: true }],
            ["ADX14", "adx14", row.adx14],
          ], row)}</td>
          <td>${renderMetricGroup([
            ["Primary count", value(row.primaryCount)],
            ["Risk", row.risk || "n/a"],
            ["Stop loss", value(row.stopLossPct, "%")],
            ["Position", value(row.positionPct, "%")],
          ])}</td>
        </tr>
      `,
    )
    .join("");
  document.getElementById("technical-table").innerHTML = `
    <table class="technical-table">
      <thead>
        <tr>
          <th>Company</th>
          <th>Signal</th>
          <th class="number">Close</th>
          <th>Momentum</th>
          <th>Trend</th>
          <th>Risk / sizing</th>
        </tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="6">No technical indicator rows loaded.</td></tr>`}</tbody>
    </table>
  `;
}

function renderTechnicalMetricGroup(items, row) {
  return `
    <div class="metric-group">
      ${items
        .map(
          ([label, key, rawValue, options = {}]) => `
            <span class="metric-line">
              <span>${escapeHtml(label)}</span>
              <b class="${rawValue === null || rawValue === undefined || Number.isNaN(rawValue) ? "metric-missing" : ""}">${renderTechnicalValue(key, rawValue, options, row)}</b>
            </span>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderTechnicalGuide() {
  const target = document.getElementById("technical-guide");
  if (!target) return;
  target.innerHTML = `
    <section class="technical-guide">
      <div class="benchmark-group-head">
        <div>
          <h3>Technical Indicator Guide</h3>
          <p class="muted">Common screening thresholds. Status wording is supportive, neutral, or not supportive; these are not trading instructions.</p>
        </div>
        <div class="indicator-legend">
          <span>${renderStatusDot("supportive")} Supportive</span>
          <span>${renderStatusDot("neutral")} Neutral</span>
          <span>${renderStatusDot("not-supportive")} Not supportive</span>
        </div>
      </div>
      <div class="table-wrap technical-guide-table">
        <table>
          <thead>
            <tr>
              <th>Indicator</th>
              <th>What it shows</th>
              <th>Supportive</th>
              <th>Neutral</th>
              <th>Not supportive</th>
            </tr>
          </thead>
          <tbody>
            ${technicalIndicatorGuide
              .map(
                (item) => `
                  <tr>
                    <td><strong>${escapeHtml(item.name)}</strong></td>
                    <td>${escapeHtml(item.shows)}</td>
                    <td>${escapeHtml(item.supportive)}</td>
                    <td>${escapeHtml(item.neutral)}</td>
                    <td>${escapeHtml(item.notSupportive)}</td>
                  </tr>
                `,
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function renderTechnicalSummary(data) {
  const target = document.getElementById("technical-summary");
  if (!target) return;
  const dashboardCount = data.rows.filter((row) => row.inDashboardScreener).length;
  target.innerHTML = `
    <div class="alert-card calm">
      <div>
        <strong>${escapeHtml(data.count ?? 0)} rows in latest.csv; showing ${escapeHtml(data.rows.length)} ${escapeHtml(data.universe || "watchlist")} row${data.rows.length === 1 ? "" : "s"}</strong>
        <span>Source date ${escapeHtml(data.sourceDate || "n/a")}; generated ${escapeHtml(shortDate(data.sourceGeneratedAt))}; fetched ${escapeHtml(shortDate(data.fetchedAt))}; ${escapeHtml(data.cacheStatus || "unknown")}.</span>
        <span>${escapeHtml(data.sourceReliability || "Technical screening context only.")}</span>
      </div>
      <div class="alert-list">
        <span class="alert-chip signal-buy"><strong>BUY</strong><span>${countTechnicalSignals(data.rows, "buy")}</span></span>
        <span class="alert-chip signal-sell"><strong>SELL</strong><span>${countTechnicalSignals(data.rows, "sell")}</span></span>
        <span class="alert-chip signal-neutral"><strong>Dashboard</strong><span>${dashboardCount}</span></span>
      </div>
    </div>
  `;
}

function countTechnicalSignals(rows, signal) {
  return rows.filter((row) => String(row.signal || "").toLowerCase().includes(signal)).length;
}

function signedValue(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return "n/a";
  return `${v > 0 ? "+" : ""}${fmt.format(v)}`;
}

async function loadFundamentals(refresh = false) {
  const universe = document.getElementById("fundamental-universe").value;
  document.getElementById("fundamentals-table").innerHTML = renderLoadingPanel(
    refresh ? "Refreshing fundamentals" : "Loading fundamentals",
  );
  const data = await api(`/api/fundamentals?universe=${encodeURIComponent(universe)}&refresh=${refresh ? "1" : "0"}`);
  document.getElementById("fundamental-errors").innerHTML = data.errors?.length
    ? `<div class="error-box">${data.errors.map((err) => `${escapeHtml(err.symbol)}: ${escapeHtml(err.error)}`).join("<br>")}</div>`
    : "";
  const rows = data.rows
    .map(
      (row) => `
      <tr data-fundamental-symbol="${escapeHtml(row.symbol)}">
        <td>${renderFundamentalCompany(row)}</td>
        <td>${renderFundamentalPriceSize(row)}</td>
        <td>${renderMetricGroup([
          ["TTM P/E", value(row.trailingPE, "x")],
          ["Fwd P/E", value(row.forwardPE, "x")],
          ["P/B", value(row.priceToBook, "x")],
          ["P/NAV", value(row.pnAv, "x")],
          ["EV/EBITDA", value(row.enterpriseToEbitda, "x")],
          ["EV/EBIT", value(row.evToEbit, "x")],
        ])}</td>
        <td>${renderMetricGroup([
          ["EPS TTM", value(row.epsTrailingTwelveMonths)],
          ["Div yield", value(row.dividendYield, "%")],
        ])}</td>
        <td>${renderHistoricalContext(row)}</td>
        <td>${renderFundamentalConsensus(row)}</td>
        <td>${renderFundamentalSource(row)}</td>
        <td>${renderFundamentalLinks(row)}</td>
      </tr>
    `,
    )
    .join("");
  document.getElementById("fundamentals-table").innerHTML = `
    <table class="fundamentals-table">
      <colgroup>
        <col class="fund-col-company">
        <col class="fund-col-price">
        <col class="fund-col-multiples">
        <col class="fund-col-earnings">
        <col class="fund-col-history">
        <col class="fund-col-consensus">
        <col class="fund-col-source">
        <col class="fund-col-links">
      </colgroup>
      <thead>
        <tr>
          <th>Company</th>
          <th>Price & size</th>
          <th>Valuation multiples</th>
          <th>Earnings & yield</th>
          <th>Own history</th>
          <th>Consensus refs</th>
          <th>Source</th>
          <th>Links</th>
        </tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="8">No fundamentals loaded.</td></tr>`}</tbody>
    </table>
  `;
}

function renderFundamentalCompany(row) {
  return `
    <div class="fund-cell">
      <strong>${escapeHtml(row.symbol)}</strong>
      <span class="muted">${escapeHtml(row.name || "Name missing")}</span>
      <span class="muted">${escapeHtml(row.sector || "Sector missing")}</span>
    </div>
  `;
}

function renderFundamentalPriceSize(row) {
  const currency = row.currency ? ` ${row.currency}` : "";
  return `
    <div class="fund-cell">
      <strong>${value(row.price)}${escapeHtml(currency)}</strong>
      <span class="metric-line"><span>Market cap</span><b>${compact(row.marketCap)}</b></span>
      <span class="muted">Last cached price from free source.</span>
    </div>
  `;
}

function renderMetricGroup(items) {
  return `
    <div class="metric-group">
      ${items
        .map(
          ([label, formatted]) => `
            <span class="metric-line">
              <span>${escapeHtml(label)}</span>
              <b class="${formatted === "n/a" ? "metric-missing" : ""}">${escapeHtml(formatted)}</b>
            </span>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderFundamentalConsensus(row) {
  const consensus = row.consensus || {};
  const recommendation = consensus.recommendationSummary?.label || row.recommendationKey || "n/a";
  const freshness = consensus.sources?.length ? consensusFreshness(consensus.sources) : "freshness n/a";
  return `
    <div class="fund-cell">
      <span class="metric-line"><span>Target</span><b>${value(row.targetMeanPrice)}</b></span>
      <span class="metric-line"><span>Vs price</span><b>${signedPctValue(row.targetUpsidePct)}</b></span>
      <span class="metric-line"><span>Reported refs</span><b>${value(consensus.reportedAnalystRefs ?? row.numberOfAnalystOpinions)}</b></span>
      <span class="tag">${escapeHtml(row.targetConfidence || "low")}</span>
      <span class="muted">${escapeHtml(row.targetStatus || "single-provider")}; ${escapeHtml(row.targetSourceCount ?? 0)} provider row(s)</span>
      <span class="muted">Source rec: ${escapeHtml(recommendation)}; ${escapeHtml(freshness)}</span>
    </div>
  `;
}

function renderFundamentalSource(row) {
  return `
    <div class="fund-cell">
      <span class="tag">${escapeHtml(row.cacheStatus || "cache n/a")}</span>
      <span class="muted">${escapeHtml(shortDate(row.fetchedAt))}</span>
      <span class="muted">${escapeHtml(row.source || "Source missing")}</span>
      <details class="compact-details">
        <summary>Limits</summary>
        <p class="muted">Fetched: ${escapeHtml(row.fetchedAt || "timestamp n/a")}</p>
        <p class="muted">${escapeHtml(row.sourceReliability || "Open/free data; verify against primary sources.")}</p>
        <p class="muted">Target source: ${escapeHtml(row.targetPriceSource || "Yahoo/yfinance")}</p>
      </details>
    </div>
  `;
}

function renderFundamentalLinks(row) {
  return `
    <div class="link-stack">
      <a class="link" href="${escapeHtml(row.newswebUrl)}" target="_blank" rel="noreferrer">NewsWeb</a>
      <a class="link" href="${escapeHtml(row.tradingViewSearchUrl)}" target="_blank" rel="noreferrer">TradingView</a>
    </div>
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
  const currentValue = select.value;
  select.innerHTML = watchlistItems
    .map((row) => `<option value="${escapeHtml(row.symbol)}">${escapeHtml(row.symbol)} - ${escapeHtml(row.name || "")}</option>`)
    .join("");
  if (currentValue && watchlistItems.some((row) => row.symbol === currentValue)) {
    select.value = currentValue;
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
  target.innerHTML = renderLoadingPanel(refresh ? "Refreshing benchmark" : "Loading benchmark");
  try {
    const data = await api(`/api/benchmarks?symbol=${encodeURIComponent(symbol)}&refresh=${refresh ? "1" : "0"}`);
    target.innerHTML = renderBenchmark(data);
    bindPeerEditors();
    bindDraftPeerGroupActions();
  } catch (error) {
    target.innerHTML = `<div class="error-box">Benchmark could not load for ${escapeHtml(symbol)}: ${escapeHtml(error.message)}</div>`;
  }
}

function renderBenchmark(data) {
  if (!data.groups?.length) {
    return `
      <div class="method-card missing-peer-card">
        <strong>No peer group configured for ${escapeHtml(data.symbol)}</strong>
        <span>${escapeHtml(data.message || "Add a peer group before drawing relative valuation context.")}</span>
        <span>Use a draft group for new watchlist companies. If the symbol already belongs to an existing group, the app will reuse that group instead.</span>
        <div class="actions">
          <button data-create-draft-peer-group="${escapeHtml(data.symbol)}">Create draft peer group</button>
          <span class="muted" data-draft-peer-status></span>
        </div>
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
        <td>${escapeHtml(row.peerNote || "")}</td>
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
        <span class="signal-badge ${peerStatusClass(group.status)}">${escapeHtml(group.status || "draft")}</span>
      </div>
      <p class="muted">${escapeHtml(group.confidenceReason)} Source: ${escapeHtml(group.source || "manual")}; updated ${escapeHtml(shortDate(group.updated_at || group.created_at))}.</p>
      ${group.curator_note ? `<p class="muted">${escapeHtml(group.curator_note)}</p>` : ""}
      ${renderPeerGroupEditor(group)}
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
            <thead><tr><th>Company</th><th>Role</th><th>Market</th><th>Peer note</th><th class="number">TTM P/E</th><th class="number">P/B</th><th class="number">EV/EBITDA</th><th class="number">Div Yield</th><th>Source</th></tr></thead>
            <tbody>${peerRows}</tbody>
          </table>
        </div>
      </details>
    </section>
  `;
}

function renderPeerGroupEditor(group) {
  const rows = [...(group.configuredItems || group.items || []), {}, {}, {}]
    .map((row) => renderPeerEditorRow(row))
    .join("");
  return `
    <details class="peer-editor">
      <summary>Edit peer group</summary>
      <form class="peer-group-form" data-group-key="${escapeHtml(group.group_key)}">
        <div class="editor-grid peer-group-fields">
          <label>
            <span>Name</span>
            <input name="name" value="${escapeHtml(group.name || "")}" />
          </label>
          <label>
            <span>Status</span>
            <select name="status">${peerStatuses.map((status) => `<option value="${status}" ${status === group.status ? "selected" : ""}>${status}</option>`).join("")}</select>
          </label>
          <label>
            <span>Description</span>
            <textarea name="description" rows="2">${escapeHtml(group.description || "")}</textarea>
          </label>
          <label>
            <span>Curation note</span>
            <textarea name="curatorNote" rows="2">${escapeHtml(group.curator_note || "")}</textarea>
          </label>
        </div>
        <div class="table-wrap peer-edit-table">
          <table>
            <thead><tr><th>Symbol</th><th>Role</th><th>Market</th><th>Peer note</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
        <div class="actions peer-editor-actions">
          <button type="submit">Save peer group</button>
          <span class="muted" data-peer-editor-status></span>
        </div>
      </form>
    </details>
  `;
}

function renderPeerEditorRow(row) {
  const role = row.peerRole || row.role || "";
  const market = row.peerMarket || row.market || "";
  const note = row.peerNote || row.note || "";
  return `
    <tr data-peer-edit-row>
      <td><input data-peer-symbol value="${escapeHtml(row.symbol || "")}" placeholder="Ticker" /></td>
      <td><select data-peer-role>${peerRoles.map((option) => `<option value="${option}" ${option === role ? "selected" : ""}>${option}</option>`).join("")}</select></td>
      <td><input data-peer-market value="${escapeHtml(market)}" placeholder="Oslo, Nordic, International" /></td>
      <td><input data-peer-note value="${escapeHtml(note)}" placeholder="Why this peer belongs or needs review" /></td>
    </tr>
  `;
}

function bindPeerEditors() {
  document.querySelectorAll(".peer-group-form").forEach((form) => {
    form.addEventListener("submit", savePeerGroup);
  });
}

function bindDraftPeerGroupActions() {
  document.querySelectorAll("[data-create-draft-peer-group]").forEach((button) => {
    button.addEventListener("click", createDraftPeerGroup);
  });
}

async function createDraftPeerGroup(event) {
  const button = event.currentTarget;
  const status = document.querySelector("[data-draft-peer-status]");
  const symbol = button.dataset.createDraftPeerGroup;
  button.disabled = true;
  if (status) status.textContent = "Creating draft group...";
  try {
    const result = await api("/api/peer-groups/draft", {
      method: "POST",
      body: JSON.stringify({ symbol }),
    });
    if (status) {
      status.textContent =
        result.action === "reused"
          ? "Existing peer group reused."
          : `Draft group created with ${result.candidateCount || 0} candidate peer${result.candidateCount === 1 ? "" : "s"}.`;
    }
    await loadBenchmark(false);
    await loadWatchlist();
  } catch (error) {
    button.disabled = false;
    if (status) status.textContent = `Could not create draft group: ${error.message}`;
  }
}

async function savePeerGroup(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const status = form.querySelector("[data-peer-editor-status]");
  status.textContent = "Saving...";
  const items = [...form.querySelectorAll("[data-peer-edit-row]")]
    .map((row) => ({
      symbol: row.querySelector("[data-peer-symbol]").value.trim(),
      role: row.querySelector("[data-peer-role]").value,
      market: row.querySelector("[data-peer-market]").value.trim(),
      note: row.querySelector("[data-peer-note]").value.trim(),
    }))
    .filter((row) => row.symbol);
  try {
    const payload = {
      groupKey: form.dataset.groupKey,
      name: form.elements.name.value,
      status: form.elements.status.value,
      description: form.elements.description.value,
      curatorNote: form.elements.curatorNote.value,
      items,
    };
    await api("/api/peer-groups", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    status.textContent = "Saved.";
    await loadBenchmark(false);
    await loadWatchlist();
  } catch (error) {
    status.textContent = `Could not save peer group: ${error.message}`;
  }
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
  document.querySelectorAll("[data-start-watchlist]").forEach((button) => {
    button.addEventListener("click", () => activateTab("watchlist"));
  });
  document.getElementById("add-watchlist-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await withLoading("Adding symbol", event.submitter, async () => {
      const symbol = document.getElementById("watchlist-symbol").value;
      const note = document.getElementById("watchlist-note").value;
      await api("/api/watchlist", {
        method: "POST",
        body: JSON.stringify({ watchlist: "Core Watchlist", symbol, note }),
      });
      event.target.reset();
      await loadWatchlist();
    });
  });
  document.getElementById("refresh-watchlist").addEventListener("click", async (event) => {
    await withLoading("Refreshing watchlist", event.currentTarget, loadWatchlist);
  });
  document.getElementById("refresh-screener-alerts").addEventListener("click", async () => {
    await withLoading("Refreshing RSI14", document.getElementById("refresh-screener-alerts"), async () => {
      await loadScreenerAlerts(true);
      await loadWatchlist();
    });
  });
  document.getElementById("benchmark-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await withLoading("Loading benchmark", event.submitter, () => loadBenchmark(false));
  });
  document.getElementById("consensus-form").addEventListener("submit", saveConsensusSource);
  document.getElementById("refresh-benchmark").addEventListener("click", async (event) => {
    await withLoading("Refreshing benchmark", event.currentTarget, () => loadBenchmark(true));
  });
  document.getElementById("refresh-fundamentals").addEventListener("click", async (event) => {
    await withLoading("Refreshing fundamentals", event.currentTarget, () => loadFundamentals(true));
  });
  document.getElementById("fundamental-universe").addEventListener("change", async () => {
    await withLoading("Loading fundamentals", null, () => loadFundamentals(false));
  });
  document.getElementById("refresh-technical").addEventListener("click", async (event) => {
    await withLoading("Refreshing technical indicators", event.currentTarget, async () => {
      await loadTechnicalIndicators(true);
      await loadWatchlist();
    });
  });
  document.getElementById("technical-universe").addEventListener("change", async () => {
    await withLoading("Loading technical indicators", null, () => loadTechnicalIndicators(false));
  });
  document.getElementById("reload-sources").addEventListener("click", async (event) => {
    await withLoading("Reloading sources", event.currentTarget, loadSources);
  });

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

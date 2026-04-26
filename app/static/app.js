const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const pct = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

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
  const data = await api("/api/watchlist");
  const rows = data.items
    .map(
      (row) => `
        <tr>
          <td><strong>${escapeHtml(row.symbol)}</strong></td>
          <td>${escapeHtml(row.name || "")}</td>
          <td>${escapeHtml(row.sector || "")}</td>
          <td>${escapeHtml(row.note || "")}</td>
          <td class="row-actions">
            <a class="link" href="https://finance.yahoo.com/quote/${encodeURIComponent(row.symbol)}" target="_blank" rel="noreferrer">Yahoo</a>
            <a class="link" href="https://newsweb.oslobors.no/search?query=${encodeURIComponent(row.symbol.replace(".OL", ""))}" target="_blank" rel="noreferrer">NewsWeb</a>
            <button class="secondary" data-remove="${escapeHtml(row.symbol)}">Remove</button>
          </td>
        </tr>
      `,
    )
    .join("");
  document.getElementById("watchlist-table").innerHTML = `
    <table>
      <thead><tr><th>Symbol</th><th>Name</th><th>Sector</th><th>Note</th><th>Links</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="5">No watchlist items yet.</td></tr>`}</tbody>
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

function flagClass(flag) {
  if (!flag) return "";
  if (flag.includes("expensive")) return "flag-expensive";
  if (flag.includes("cheap")) return "flag-cheap";
  if (flag.includes("insufficient")) return "flag-insufficient";
  return "";
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
        <td><span class="${flagClass(row.valuationFlag)}">${escapeHtml(row.valuationFlag)}</span></td>
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
          <th class="number">Upside</th><th>Flag</th><th>Source</th><th>Links</th>
        </tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="17">No fundamentals loaded.</td></tr>`}</tbody>
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


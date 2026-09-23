const byId = id => document.getElementById(id);

export function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function safeUrl(value) {
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? escapeHtml(url.href) : '';
  } catch {
    return '';
  }
}

function sentimentArrow(sentiment) {
  if (sentiment === 'bullish') return '↑';
  if (sentiment === 'bearish') return '↓';
  return '→';
}

function timeAgo(unixTime) {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - unixTime));
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function renderChips(tickers, activeTickers, onToggle) {
  const row = byId('tickerRow');
  row.replaceChildren();
  tickers.forEach(ticker => {
    const button = document.createElement('button');
    button.className = `chip${activeTickers.has(ticker) ? ' on' : ''}`;
    button.textContent = `$${ticker}`;
    button.addEventListener('click', () => onToggle(ticker));
    row.appendChild(button);
  });
}

export function setLive(active, label) {
  byId('liveDot').className = `live-dot${active ? ' on' : ''}`;
  byId('liveLabel').textContent = label;
}

export function setProgress(percent, log, title = '') {
  byId('progressWrap').style.display = 'block';
  byId('progressBar').style.width = `${percent}%`;
  byId('progressPct').textContent = `${percent}%`;
  byId('progressLog').textContent = log;
  if (title) byId('progressTitle').textContent = title;
}

export function hideProgress() {
  byId('progressWrap').style.display = 'none';
}

export function showError(message) {
  const banner = byId('errBanner');
  banner.textContent = `Error: ${message}`;
  banner.style.display = 'block';
}

export function hideError() {
  byId('errBanner').style.display = 'none';
}

export function setBusy(busy) {
  byId('fetchBtn').disabled = busy;
}

export function showSkeletons() {
  byId('feedWrap').innerHTML = `<div class="feed">${Array(5).fill(0).map(() => `
    <div class="skel-card">
      <div class="skel" style="width:56px;height:26px;flex-shrink:0"></div>
      <div style="flex:1">
        <div class="skel" style="width:68%;height:14px;margin-bottom:9px"></div>
        <div class="skel" style="width:44%;height:12px"></div>
      </div>
    </div>`).join('')}</div>`;
}

export function renderStats(articles) {
  byId('stTotal').textContent = articles.length;
  byId('stBull').textContent = articles.filter(a => a.sentiment === 'bullish').length;
  byId('stBear').textContent = articles.filter(a => a.sentiment === 'bearish').length;
  byId('stHold').textContent = articles.filter(a => a.sentiment === 'neutral').length;
  byId('statsbar').style.display = 'flex';
}

export function renderFeed(articles, filter) {
  byId('countLbl').textContent = `${articles.length} shown`;
  if (!articles.length) {
    renderEmpty(`No ${filter === 'all' ? '' : `${filter} `}articles`, 'Try a different filter or fetch more tickers.');
    return;
  }

  const cards = articles.map((article, index) => {
    const url = safeUrl(article.url);
    const headline = escapeHtml(article.headline);
    return `
      <article class="card" style="animation-delay:${index * 30}ms">
        <div class="card-left">
          <div class="ticker-badge">$${escapeHtml(article.ticker)}</div>
          <div class="sent-arrow ${article.sentiment}">${sentimentArrow(article.sentiment)}</div>
        </div>
        <div class="card-body">
          <div class="headline">${url ? `<a href="${url}" target="_blank" rel="noopener noreferrer">${headline}</a>` : headline}</div>
          <div class="summary">${escapeHtml(article.summary)}</div>
          <div class="meta">
            <span class="source-tag">${escapeHtml(article.source)}</span>
            <span class="sent-pill ${article.sentiment}">${escapeHtml(article.sentiment)}</span>
          </div>
          ${article.reason ? `<div class="reason">${escapeHtml(article.reason)}</div>` : ''}
        </div>
        <div class="card-right"><div class="time-lbl">${article.datetime ? timeAgo(article.datetime) : '?'}</div></div>
      </article>`;
  }).join('');
  byId('feedWrap').innerHTML = `<div class="feed">${cards}</div>`;
}

export function renderEmpty(title, message) {
  byId('feedWrap').innerHTML = `
    <div class="empty">
      <div class="empty-glyph">◈</div>
      <div class="empty-h">${escapeHtml(title)}</div>
      <div class="empty-p">${escapeHtml(message)}</div>
    </div>`;
}

export function showResultsChrome() {
  byId('filterbar').style.display = 'flex';
}

export function hideResultsChrome() {
  byId('statsbar').style.display = 'none';
  byId('filterbar').style.display = 'none';
}

export function selectFilterButton(filter) {
  document.querySelectorAll('.ftag').forEach(button => {
    button.classList.toggle('on', button.dataset.filter === filter);
  });
}

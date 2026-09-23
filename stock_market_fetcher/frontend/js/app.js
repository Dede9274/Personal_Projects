import {analyseNews, fetchHealth, fetchNews} from './api.js';
import {
  DEFAULT_TICKERS,
  addTicker,
  clearResults,
  getFilteredArticles,
  getState,
  setArticles,
  setFilter,
  toggleTicker,
} from './state.js';
import {
  hideError,
  hideProgress,
  hideResultsChrome,
  renderChips,
  renderEmpty,
  renderFeed,
  renderStats,
  selectFilterButton,
  setBusy,
  setLive,
  setProgress,
  showError,
  showResultsChrome,
  showSkeletons,
} from './ui.js';

function refreshChips() {
  const {activeTickers} = getState();
  renderChips(DEFAULT_TICKERS, activeTickers, ticker => {
    toggleTicker(ticker);
    refreshChips();
  });
}

function refreshFeed() {
  const {filter} = getState();
  selectFilterButton(filter);
  renderFeed(getFilteredArticles(), filter);
}

function addCustomTicker(event) {
  if (event.key !== 'Enter') return;
  const ticker = event.target.value.trim().toUpperCase();
  if (!/^[A-Z][A-Z0-9.-]{0,9}$/.test(ticker)) {
    showError('Enter a valid ticker symbol.');
    return;
  }
  addTicker(ticker);
  if (!DEFAULT_TICKERS.includes(ticker)) DEFAULT_TICKERS.push(ticker);
  event.target.value = '';
  hideError();
  refreshChips();
}

function clearDashboard() {
  clearResults();
  hideProgress();
  hideError();
  hideResultsChrome();
  setLive(false, 'idle');
  selectFilterButton('all');
  renderEmpty('No articles loaded', 'Select tickers and fetch the latest news.');
}

async function loadDashboard() {
  const tickers = [...getState().activeTickers];
  if (!tickers.length) {
    showError('Select at least one ticker.');
    return;
  }

  hideError();
  hideResultsChrome();
  setArticles([]);
  setBusy(true);
  setLive(true, 'fetching…');
  showSkeletons();

  try {
    setProgress(5, 'Checking backend configuration…', 'Step 1 — Backend');
    const health = await fetchHealth();
    const missing = Object.entries(health.services)
      .filter(([, configured]) => !configured)
      .map(([service]) => service);
    if (missing.length) {
      throw new Error(`Server configuration is missing: ${missing.join(', ')}.`);
    }

    const rawArticles = [];
    for (let index = 0; index < tickers.length; index += 1) {
      const ticker = tickers[index];
      const percent = 10 + Math.round((index / tickers.length) * 50);
      setProgress(percent, `Fetching news for $${ticker}…`, 'Step 2 — Finnhub');
      rawArticles.push(...await fetchNews(ticker));
    }
    if (!rawArticles.length) {
      throw new Error('Finnhub returned no articles for the selected tickers.');
    }

    setProgress(65, `Analysing ${rawArticles.length} headlines…`, 'Step 3 — Sentiment');
    const analysedArticles = await analyseNews(rawArticles);
    setArticles(analysedArticles);

    setProgress(100, `Done — ${analysedArticles.length} articles loaded`);
    renderStats(analysedArticles);
    showResultsChrome();
    refreshFeed();
    setLive(true, `${analysedArticles.length} articles · ${tickers.length} tickers`);
    window.setTimeout(hideProgress, 350);
  } catch (error) {
    hideProgress();
    showError(error.message);
    setLive(false, 'error');
    renderEmpty('Could not load news', error.message);
  } finally {
    setBusy(false);
  }
}

document.getElementById('addInput').addEventListener('keydown', addCustomTicker);
document.getElementById('fetchBtn').addEventListener('click', loadDashboard);
document.getElementById('clearBtn').addEventListener('click', clearDashboard);
document.querySelectorAll('.ftag').forEach(button => {
  button.addEventListener('click', () => {
    setFilter(button.dataset.filter);
    refreshFeed();
  });
});

refreshChips();

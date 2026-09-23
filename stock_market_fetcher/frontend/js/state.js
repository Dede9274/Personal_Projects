export const DEFAULT_TICKERS = [
  'TSM', 'CCJ', 'HXSCL', 'SPY', 'SLV', 'BWXT', 'UEC', 'NVDA', 'AMZN',
];

const state = {
  activeTickers: new Set(DEFAULT_TICKERS),
  articles: [],
  filter: 'all',
};

export function getState() {
  return state;
}

export function toggleTicker(ticker) {
  if (state.activeTickers.has(ticker)) {
    state.activeTickers.delete(ticker);
  } else {
    state.activeTickers.add(ticker);
  }
}

export function addTicker(ticker) {
  state.activeTickers.add(ticker);
}

export function setArticles(articles) {
  state.articles = articles;
}

export function setFilter(filter) {
  state.filter = filter;
}

export function clearResults() {
  state.articles = [];
  state.filter = 'all';
}

export function getFilteredArticles() {
  if (state.filter === 'all') return state.articles;
  return state.articles.filter(article => article.sentiment === state.filter);
}

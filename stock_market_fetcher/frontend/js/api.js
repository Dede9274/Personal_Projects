async function requestJson(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error('Cannot reach the PulseStock server.');
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Server request failed (${response.status}).`);
  }
  return payload;
}

export function fetchHealth() {
  return requestJson('/api/health');
}

export function fetchNews(ticker) {
  return requestJson(`/api/news/${encodeURIComponent(ticker)}`);
}

export async function analyseNews(articles) {
  const payload = await requestJson('/api/analyse-news', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({articles}),
  });
  return payload.articles;
}

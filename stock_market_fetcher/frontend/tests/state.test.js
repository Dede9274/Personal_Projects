import test from 'node:test';
import assert from 'node:assert/strict';

import {
  clearResults,
  getFilteredArticles,
  setArticles,
  setFilter,
} from '../js/state.js';


test('bullish filter returns only bullish articles', () => {
  setArticles([
    {headline: 'Up', sentiment: 'bullish'},
    {headline: 'Down', sentiment: 'bearish'},
    {headline: 'Flat', sentiment: 'neutral'},
  ]);
  setFilter('bullish');

  assert.deepEqual(getFilteredArticles(), [
    {headline: 'Up', sentiment: 'bullish'},
  ]);
  clearResults();
});

test('all filter returns every article', () => {
  const articles = [
    {headline: 'Up', sentiment: 'bullish'},
    {headline: 'Down', sentiment: 'bearish'},
  ];
  setArticles(articles);
  setFilter('all');

  assert.deepEqual(getFilteredArticles(), articles);
  clearResults();
});

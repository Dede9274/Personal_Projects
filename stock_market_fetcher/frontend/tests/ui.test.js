import test from 'node:test';
import assert from 'node:assert/strict';

import {escapeHtml, safeUrl} from '../js/ui.js';


test('escapeHtml escapes markup and attribute delimiters', () => {
  assert.equal(
    escapeHtml(`<script data-value="'&">alert(1)</script>`),
    '&lt;script data-value=&quot;&#39;&amp;&quot;&gt;alert(1)&lt;/script&gt;',
  );
});

test('safeUrl rejects javascript URLs', () => {
  assert.equal(safeUrl('javascript:alert(1)'), '');
});

test('safeUrl rejects malformed URLs', () => {
  assert.equal(safeUrl('not a URL'), '');
});

test('safeUrl permits and escapes HTTPS URLs', () => {
  assert.equal(
    safeUrl('https://example.com/news?first=1&second=2'),
    'https://example.com/news?first=1&amp;second=2',
  );
});

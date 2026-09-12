import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const prototype=readFileSync(new URL('../../../COBECO_figma_RF01_RF17_v2.html',import.meta.url),'utf8');
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const css=readFileSync(new URL('../css/style.css',import.meta.url),'utf8');

test('approved Figma stylesheet and screens are preserved',()=>{
  assert.ok(css.startsWith(prototype.match(/<style>([\s\S]*?)<\/style>/)[1]));
  for(const id of ['landing','builder','register','login','recover','lists','providers','results','profile','modalback','confirmBack'])assert.ok(html.includes(`id="${id}"`),id);
});

test('prototype demo authentication and inline scripts are replaced by application modules',()=>{
  assert.ok(html.includes('type="module" src="/js/app.js"'));
  assert.ok(!/\son(?:click|input)=/.test(html));
  assert.ok(!html.includes('cobeco_users'));
  assert.ok(!/<script>/.test(html));
  assert.ok(!/\sstyle=/.test(html));
});

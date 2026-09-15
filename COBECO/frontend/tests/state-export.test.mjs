import test from 'node:test';
import assert from 'node:assert/strict';

const saved=new Map();
globalThis.sessionStorage={getItem:key=>saved.get(key)||null,setItem:(key,value)=>saved.set(key,value)};
globalThis.localStorage={removeItem:key=>saved.delete(key)};
globalThis.window=new EventTarget();
const {state,changed,payload,resetDraft,session,setCategories}=await import('../js/state.js');
const {csvText}=await import('../js/export.js');

test('CSV preserves accents, BOM, delimiters, quoting and protects formula cells',()=>{
  const text=csvText({name:'Compras; setembro',items:[{name:'Café "especial"',quantity:2,unit:'un'},{name:'=SUM(A1)',quantity:1,unit:'kg'}]});
  assert.equal(text.charCodeAt(0),0xFEFF);
  assert.ok(text.includes('"Compras; setembro";"Café ""especial""";"2";"un"'));
  assert.ok(text.includes('"\'=SUM(A1)"'));
  assert.ok(text.includes('\r\n'));
});

test('draft updates invalidate comparisons and persist independently of authentication',()=>{
  state.draft={name:' Mercado ',items:[{product_id:2,name:'Feijão',quantity:3,unit:'kg'}]};
  state.result={rows:[]};const previous=state.revision;changed();
  assert.equal(state.result,null);assert.equal(state.revision,previous+1);
  assert.deepEqual(payload(),{name:'Mercado',items:[{product_id:2,quantity:3}],category_ids:[]});
  assert.equal(JSON.parse(saved.get('cobeco:draft')).items[0].name,'Feijão');
  session({user:{id:1},access_token:'secret'});
  assert.ok(!saved.get('cobeco:draft').includes('secret'));
  session(null);assert.equal(state.token,null);assert.equal(state.draft.items.length,1);
  resetDraft();assert.equal(state.draft.items.length,0);
});

test('category union is transient and invalidates suppliers and stale comparisons',()=>{
  state.draft={name:'Antiga',items:[{product_id:1,name:'Arroz',quantity:2}]};changed();
  state.selected=new Set([1,2]);state.suppliers=[{supplier_id:1}];state.result={rows:[]};
  const revision=state.revision;
  setCategories([2,1,2]);
  assert.deepEqual(payload().category_ids,[1,2]);
  assert.equal(state.selected.size,0);assert.deepEqual(state.suppliers,[]);assert.equal(state.result,null);
  assert.ok(state.revision>revision);
  assert.ok(!saved.get('cobeco:draft').includes('category'));
  assert.equal(state.draft.items.length,1);
  session({user:{id:1},access_token:'secret'});
  assert.deepEqual(payload().category_ids,[1,2]);
  resetDraft();assert.deepEqual(state.categoryIds,[]);
});

test('CSV neutralizes formulas preceded by whitespace or control characters',()=>{
  for(const name of ['\t=1+1','\r=1+1','\n=1+1','  +1','\u0000@SUM(A1)']){
    assert.ok(csvText({name,items:[{name:'Produto',quantity:1,unit:'un'}]}).includes(`"'${name}"`));
  }
});

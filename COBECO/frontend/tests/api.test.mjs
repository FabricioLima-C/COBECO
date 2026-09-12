import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.sessionStorage={getItem:()=>null,setItem:()=>{}};
globalThis.localStorage={removeItem:()=>{}};
globalThis.window=new EventTarget();
const {api}=await import('../js/api.js');
const {state,session}=await import('../js/state.js');

test('private request renews once after 401 and uses only in-memory token',async()=>{
  const calls=[];session({user:{id:1},access_token:'old'});
  globalThis.fetch=async(url,options)=>{
    calls.push([url,options]);
    if(url==='/api/auth/refresh')return Response.json({user:{id:1},access_token:'new'});
    return options.headers.Authorization==='Bearer new'?Response.json({id:1}):Response.json({}, {status:401});
  };
  assert.deepEqual(await api('/profile'),{id:1});
  assert.equal(calls.length,3);assert.equal(state.token,'new');
});

test('unauthenticated public comparison neither refreshes nor redirects',async()=>{
  session(null);let calls=0;
  globalThis.fetch=async(url,options)=>{calls++;assert.equal(options.headers.Authorization,undefined);return Response.json({rows:[]});};
  assert.deepEqual(await api('/compare',{method:'POST',body:{items:[]}}),{rows:[]});
  assert.equal(calls,1);
});

test('network failure and server error expose useful feedback',async()=>{
  globalThis.fetch=async()=>{throw new TypeError('Network');};
  await assert.rejects(api('/categories'),/conectar/);
  globalThis.fetch=async()=>Response.json({error:{message:'Aguarde'}},{status:429});
  await assert.rejects(api('/categories'),/Aguarde/);
});

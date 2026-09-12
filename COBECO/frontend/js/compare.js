import {api} from './api.js';
import {state,payload} from './state.js';
import {$,escape,money,toast,go} from './ui.js';
let availabilityController,compareController,requestVersion=0;
const cache=new Map();
function invalidate(){state.revision++;state.result=null;compareController?.abort();cache.clear();$('resultsWrap').classList.add('hidden');}
const visible=()=>state.suppliers.filter(s=>s.coverage>=state.minimum);
export function renderSuppliers(){
  const rows=visible(),valid=new Set(rows.map(s=>s.supplier_id));state.selected=new Set([...state.selected].filter(id=>valid.has(id)));
  $('selectedCount').textContent=`${state.selected.size} selecionados · ${rows.length} fornecedores`;$('providerCompareBtn').disabled=state.selected.size<2;
  $('providerGrid').innerHTML=rows.length?rows.map(s=>`<article class="provider ${state.selected.has(s.supplier_id)?'selected':''}"><label class="provider-title"><h3>${escape(s.supplier_name)}</h3><input type="checkbox" value="${s.supplier_id}" ${state.selected.has(s.supplier_id)?'checked':''} aria-label="Selecionar ${escape(s.supplier_name)}"></label><div class="muted">${s.coverage}% da lista disponível</div><div class="availability"><progress max="100" value="${s.coverage}" aria-label="Disponibilidade de ${escape(s.supplier_name)}"></progress></div></article>`).join(''):'<div class="empty">Nenhum fornecedor atende ao filtro.</div>';
  $('providerGrid').querySelectorAll('input').forEach(input=>input.onchange=()=>{if(input.checked)state.selected.add(Number(input.value));else state.selected.delete(Number(input.value));invalidate();renderSuppliers();});
  $('providerGrid').querySelectorAll('article').forEach(card=>card.onclick=event=>{if(event.target.closest('label'))return;const input=card.querySelector('input');input.click();});
}
export async function loadAvailability(){
  const version=++requestVersion;availabilityController?.abort();const controller=new AbortController();availabilityController=controller;
  invalidate();state.suppliers=[];$('providerCompareBtn').disabled=true;$('providerGrid').innerHTML='<div class="loading"><span class="spinner"></span><p>Consultando fornecedores…</p></div>';
  if(!state.draft.items.length){state.selected.clear();renderSuppliers();return;}
  try{
    const rows=await api('/suppliers/availability',{method:'POST',body:{items:payload().items,category_id:state.category},signal:controller.signal});if(version!==requestVersion)return;
    state.suppliers=rows;renderSuppliers();
  }catch(error){if(version===requestVersion&&!controller.signal.aborted){state.selected.clear();$('providerGrid').innerHTML=`<div class="empty">${escape(error.message)}</div>`;$('selectedCount').textContent='Não foi possível consultar os fornecedores.';}}
}
export function filterProviders(){state.minimum=Number($('range').value);$('rangeVal').textContent=state.minimum+'%';invalidate();renderSuppliers();}
export function selectAll(){state.selected=new Set(visible().slice(0,10).map(s=>s.supplier_id));invalidate();renderSuppliers();}
export function clearSelection(){state.selected.clear();invalidate();renderSuppliers();}
function renderResults(result){
  $('compareLoading').classList.add('hidden');$('resultsWrap').classList.remove('hidden');
  $('resultSummary').textContent=`${state.draft.name||'Minha lista'} · ${state.draft.items.length} produtos · ${result.rows.length} fornecedores`;
  $('resultBody').innerHTML=result.rows.map(row=>{const best=result.best_supplier_ids.includes(row.supplier_id);return `<tr class="${best?'best':''}"><td><strong>${escape(row.supplier_name)}</strong>${best?' <span class="badge green">Melhor oferta</span>':''}</td><td><span class="badge ${row.coverage===100?'green':'blue'}">${row.coverage}%</span></td><td>${row.available_items.length}/${state.draft.items.length}</td><td>${row.missing_items.length?`<span class="tooltip" tabindex="0" data-tip="${escape(row.missing_items.join(', '))}" aria-label="Itens ausentes: ${escape(row.missing_items.join(', '))}">i</span> ${row.missing_items.length}<span class="print-only">${row.missing_items.map(escape).join(', ')}</span>`:'0'}</td><td class="price">${money(row.total)}${row.partial?`<span class="partial-note">${row.total===null?'Sem ofertas':'Total parcial'}</span>`:''}</td></tr>`;}).join('');
  let policy=$('resultPolicy');if(!policy){policy=document.createElement('p');policy.id='resultPolicy';policy.className='result-policy';$('resultsWrap').append(policy);}
  policy.textContent='Melhor oferta: maior disponibilidade e, entre essas opções, menor preço. '+(result.tied?'Há empate entre as melhores ofertas.':'');
}
export async function calculate(){
  if(state.selected.size<2)return toast('Selecione pelo menos dois fornecedores.',true);
  const revision=state.revision,data={items:payload().items,supplier_ids:[...state.selected].sort((a,b)=>a-b)},key=JSON.stringify(data),cached=cache.get(key);
  go('results');if(cached&&cached.expires>Date.now()){state.result=cached.result;renderResults(cached.result);return;}
  compareController?.abort();const controller=new AbortController();compareController=controller;$('compareLoading').classList.remove('hidden');$('resultsWrap').classList.add('hidden');
  try{const result=await api('/compare',{method:'POST',body:data,signal:controller.signal});if(revision!==state.revision)return;cache.set(key,{result,expires:Date.now()+300000});state.result=result;renderResults(result);}
  catch(error){if(!controller.signal.aborted){toast(error.message,true);go('providers');}}
  finally{if(compareController===controller)$('compareLoading').classList.add('hidden');}
}
export async function initCompare(){
  $('category').onchange=()=>{state.category=Number($('category').value)||null;loadAvailability();};
  window.addEventListener('draft-changed',()=>{invalidate();state.suppliers=[];if(state.screen==='providers')loadAvailability();});
  window.addEventListener('screen-changed',event=>{if(event.detail==='providers')loadAvailability();});
  try{const categories=await api('/categories');$('category').innerHTML='<option value="">Todas as categorias</option>'+categories.map(c=>`<option value="${c.id}">${escape(c.name)}</option>`).join('');}catch(error){toast(error.message,true);}
}

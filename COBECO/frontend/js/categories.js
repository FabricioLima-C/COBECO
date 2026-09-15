import {api} from './api.js';
import {state,setCategories} from './state.js';
import {$,escape,go} from './ui.js';

let catalog=[],controller,version=0,loading=false,loaded=false;
function summary(){
  const names=catalog.filter(c=>state.categoryIds.includes(c.id)).map(c=>c.name);
  const label=names.length?names.join(' · '):'Nenhuma categoria selecionada';
  $('builderCategories').textContent=label;
  $('providerCategories').textContent=label;
  $('continueCategories').disabled=loading||!state.categoryIds.length;
  $('continueCategories').textContent=state.categoryReturn==='providers'?'Continuar para fornecedores':'Continuar para a lista';
}
async function preview(){
  const current=++version;controller?.abort();controller=new AbortController();
  const signal=controller.signal;summary();
  if(!state.categoryIds.length){$('categorySuppliers').textContent='Selecione ao menos uma categoria para consultar fornecedores.';return;}
  $('categorySuppliers').textContent='Consultando fornecedores…';
  try{
    const suppliers=await api('/suppliers/search',{method:'POST',body:{category_ids:[...state.categoryIds]},signal});
    if(current!==version)return;
    $('categorySuppliers').textContent=suppliers.length?`${suppliers.length} fornecedores: ${suppliers.map(s=>s.name).join(', ')}. A disponibilidade será calculada após montar a lista.`:'Nenhum fornecedor nestas categorias. Você pode escolher outras categorias.';
  }catch(error){if(current===version&&!signal.aborted)$('categorySuppliers').textContent=error.message;}
}
async function load(){
  if(loading)return;loading=true;summary();
  $('categoryOptions').textContent='Carregando categorias…';
  try{
    catalog=await api('/categories');loaded=true;
    $('categoryOptions').innerHTML=catalog.length?catalog.map(c=>`<label class="category-option"><input type="checkbox" value="${c.id}" ${state.categoryIds.includes(c.id)?'checked':''}><span>${escape(c.name)}</span></label>`).join(''):'Nenhuma categoria cadastrada.';
    $('categoryOptions').querySelectorAll('input').forEach(input=>input.onchange=()=>setCategories([...$('categoryOptions').querySelectorAll('input:checked')].map(node=>Number(node.value))));
    const valid=new Set(catalog.map(c=>c.id));
    if(state.categoryIds.some(id=>!valid.has(id)))setCategories(state.categoryIds.filter(id=>valid.has(id)));
  }catch(error){$('categoryOptions').textContent=error.message;}
  finally{loading=false;summary();}
}
export function editCategories(){state.categoryReturn=state.screen==='providers'?'providers':'builder';go('categories');}
export function continueCategories(){if(state.categoryIds.length)go(state.categoryReturn||'builder');}
export function initCategories(){
  $('retryCategories').onclick=load;
  window.addEventListener('categories-changed',()=>{
    $('categoryOptions').querySelectorAll('input').forEach(input=>{input.checked=state.categoryIds.includes(Number(input.value));});
    preview();
  });
  window.addEventListener('screen-changed',event=>{if(event.detail==='categories'){if(!loaded)load();preview();}});
  summary();load();
}

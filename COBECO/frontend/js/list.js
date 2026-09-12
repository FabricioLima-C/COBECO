import {api} from './api.js';
import {state,changed,payload,resetDraft,persist} from './state.js';
import {$,escape,toast,confirm,busy,go} from './ui.js';
import {showAuth,updateAuthUI} from './auth.js';
let selectedProduct=null,searchTimer,searchController,searchVersion=0,savedPage=1,savedVersion=0;
const productCache=new Map();
export function renderItems(){
  $('listName').value=state.draft.name;updateAuthUI();
  const total=state.draft.items.reduce((sum,item)=>sum+item.quantity,0);$('count').textContent=`${state.draft.items.length} produtos · ${total} unidades`;$('compareBtn').disabled=!state.draft.items.length;
  $('itemsWrap').innerHTML=state.draft.items.length?`<div class="table-scroller"><table class="table"><thead><tr><th>Produto</th><th>Unidade</th><th>Qtd.</th><th class="no-print">Ações</th></tr></thead><tbody>${state.draft.items.map(item=>`<tr><td><strong>${escape(item.name)}</strong>${item.active===false||item.active===0?'<div class="small-note unavailable">Produto indisponível</div>':''}</td><td>${escape(item.unit||'un')}</td><td><input class="input quantity-input" type="number" min="1" max="9999" step="1" value="${item.quantity}" data-quantity="${item.product_id}" aria-label="Quantidade de ${escape(item.name)}"></td><td class="no-print"><button class="danger" data-remove="${item.product_id}">Remover</button></td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">Sua lista ainda está vazia. Adicione ao menos 1 item.</div>';
  $('itemsWrap').querySelectorAll('[data-quantity]').forEach(input=>input.onchange=()=>{
    const item=state.draft.items.find(i=>i.product_id===Number(input.dataset.quantity));const quantity=Number(input.value);
    if(!Number.isInteger(quantity)||quantity<1||quantity>9999){input.value=item.quantity;return toast('Quantidade deve ser um inteiro entre 1 e 9999.',true);}item.quantity=quantity;changed();
  });
  $('itemsWrap').querySelectorAll('[data-remove]').forEach(button=>button.onclick=async()=>{
    const item=state.draft.items.find(i=>i.product_id===Number(button.dataset.remove));
    if(await confirm(`Deseja remover “${item.name}” da lista?`,{title:'Remover item',accept:'Remover'})){state.draft.items=state.draft.items.filter(i=>i.product_id!==item.product_id);changed();}
  });
}
export function addItem(){
  if(!selectedProduct)return toast('Selecione um produto existente no catálogo.',true);
  const quantity=Number($('qty').value);if(!Number.isInteger(quantity)||quantity<1||quantity>9999)return toast('Quantidade deve ser um inteiro entre 1 e 9999.',true);
  const item=state.draft.items.find(i=>i.product_id===selectedProduct.id);
  if(item&&item.quantity+quantity>9999)return toast('A soma excede a quantidade máxima de 9999.',true);
  if(!item&&state.draft.items.length>=100)return toast('Limite de 100 produtos por lista.',true);
  if(item)item.quantity+=quantity;else state.draft.items.push({product_id:selectedProduct.id,name:selectedProduct.name,unit:selectedProduct.unit,quantity});
  selectedProduct=null;$('search').value='';$('qty').value='1';$('menu').classList.remove('open');changed();$('search').focus();
}
async function searchProducts(){
  const q=$('search').value.trim(),version=++searchVersion;searchController?.abort();const controller=new AbortController();searchController=controller;
  if(q.length<2){$('menu').classList.remove('open');return;}
  $('menu').classList.add('open');$('menu').innerHTML='<div class="search-status">Buscando produtos…</div>';
  try{
    const cached=productCache.get(q.toLowerCase());const products=cached&&cached.expires>Date.now()?cached.data:await api(`/products?q=${encodeURIComponent(q)}`,{signal:controller.signal});if(version!==searchVersion)return;
    if(productCache.size>100)productCache.clear();productCache.set(q.toLowerCase(),{data:products,expires:Date.now()+300000});
    $('menu').innerHTML=products.length?products.map(p=>`<button type="button" data-product="${p.id}"><strong>${escape(p.name)}</strong><br><small>${escape(p.unit)}</small></button>`).join(''):'<div class="search-status">Nenhum produto encontrado.</div>';
    $('menu').querySelectorAll('button').forEach(button=>button.onclick=()=>{selectedProduct=products.find(p=>p.id===Number(button.dataset.product));$('search').value=selectedProduct.name;$('menu').classList.remove('open');$('qty').focus();});
  }catch(error){if(version===searchVersion&&!controller.signal.aborted)$('menu').innerHTML=`<div class="search-status">${escape(error.message)}</div>`;}
}
export async function saveList(){
  if(!state.draft.items.length||!state.draft.name.trim())return toast('Informe o nome e adicione ao menos um produto.',true);
  if(!state.user)return showAuth();
  const button=document.querySelector('[data-action="saveList()"]');
  await busy(button,async()=>{try{
    const userId=state.user.id,revision=state.revision;const owned=state.draft.id&&state.draft.owner_id===userId;
    const list=await api(owned?`/lists/${state.draft.id}`:'/lists',{method:owned?'PUT':'POST',body:payload()});
    if(revision===state.revision&&state.user?.id===userId){state.draft={...list,owner_id:userId};persist();renderItems();}toast('Lista salva com sucesso.');
  }catch(error){toast(error.message,true);}});
}
const date=value=>new Date(value.endsWith('Z')?value:value+'Z').toLocaleDateString('pt-BR');
export async function loadSaved(page=savedPage){
  if(!state.user)return;const version=++savedVersion,userId=state.user.id;$('listsWrap').innerHTML='<div class="loading"><span class="spinner"></span><p>Carregando listas…</p></div>';
  try{
    const data=await api(`/lists?page=${page}&q=${encodeURIComponent($('savedQuery').value)}`);if(version!==savedVersion||state.user?.id!==userId)return;savedPage=data.page;
    $('listsWrap').innerHTML=data.items.length?`<div class="table-scroller"><table class="table"><thead><tr><th>Nome</th><th>Itens</th><th>Criada em</th><th>Atualizada em</th><th>Ações</th></tr></thead><tbody>${data.items.map(list=>`<tr><td><strong>${escape(list.name)}</strong></td><td>${list.item_count}</td><td>${date(list.created_at)}</td><td>${date(list.updated_at)}</td><td><div class="row-actions"><button class="secondary" data-open="${list.id}">Abrir</button><button class="secondary" data-open="${list.id}">Editar</button><button class="danger" data-delete="${list.id}">Excluir</button></div></td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">Nenhuma lista salva encontrada.</div>';
    const pages=Math.max(1,Math.ceil(data.total/20));$('pagination').innerHTML=`<button id="previousPage" ${data.page===1?'disabled':''} aria-label="Página anterior">‹</button><button class="active" aria-current="page">${data.page}</button><span class="count">de ${pages}</span><button id="nextPage" ${data.page>=pages?'disabled':''} aria-label="Próxima página">›</button>`;
    $('previousPage').onclick=()=>loadSaved(savedPage-1);$('nextPage').onclick=()=>loadSaved(savedPage+1);
    $('listsWrap').querySelectorAll('[data-open]').forEach(button=>button.onclick=async()=>{
      if(state.draft.items.length&&!await confirm('Substituir o rascunho atual por esta lista?',{title:'Abrir lista',accept:'Abrir'}))return;
      try{const list=await api(`/lists/${button.dataset.open}`);if(state.user?.id!==userId)return;state.draft={...list,owner_id:userId};state.selected.clear();changed();go('builder');}catch(error){toast(error.message,true);}
    });
    $('listsWrap').querySelectorAll('[data-delete]').forEach(button=>button.onclick=async()=>{
      const list=data.items.find(i=>i.id===Number(button.dataset.delete));
      if(!await confirm('Esta lista será removida das suas listas salvas.',{title:'Excluir lista',name:list.name,accept:'Excluir'}))return;
      try{await api(`/lists/${list.id}`,{method:'DELETE'});if(state.draft.id===list.id){state.draft.id=null;state.draft.owner_id=null;changed();}await loadSaved();toast('Lista excluída.');}catch(error){toast(error.message,true);}
    });
  }catch(error){if(version===savedVersion)$('listsWrap').innerHTML=`<div class="empty">${escape(error.message)}</div>`;}
}
export async function startNewList(){if(!state.draft.items.length||await confirm('Começar uma nova lista? Seu rascunho atual será substituído.',{accept:'Nova lista'})){resetDraft();go('builder');$('listName').focus();}}
export function initList(){
  renderItems();$('listName').oninput=()=>{state.draft.name=$('listName').value;state.revision++;persist();};
  $('search').oninput=()=>{selectedProduct=null;clearTimeout(searchTimer);searchController?.abort();searchVersion++;$('menu').classList.remove('open');searchTimer=setTimeout(searchProducts,300);};
  $('search').onkeydown=event=>{if(event.key==='Escape')$('menu').classList.remove('open');if(event.key==='ArrowDown'){$('menu').querySelector('button')?.focus();event.preventDefault();}};
  $('qty').onkeydown=event=>{if(event.key==='Enter')addItem();};
  document.addEventListener('click',event=>{if(!event.target.closest('.autocomplete'))$('menu').classList.remove('open');});
  let queryTimer;$('savedQuery').oninput=()=>{clearTimeout(queryTimer);savedVersion++;queryTimer=setTimeout(()=>loadSaved(1),300);};
  window.addEventListener('draft-changed',renderItems);window.addEventListener('save-requested',saveList);
  window.addEventListener('screen-changed',event=>{if(event.detail==='lists')loadSaved();});
}

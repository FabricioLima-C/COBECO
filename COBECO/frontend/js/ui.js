import {state} from './state.js';
export const $=id=>document.getElementById(id);
export const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const money=value=>value==null?'N/D':new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(value));
export function toast(message,error=false){const element=document.createElement('div');element.className='toast'+(error?' error':'');element.textContent=message;$('toastWrap').append(element);setTimeout(()=>element.remove(),5000);}
export function message(id,text,type='err'){const node=$(id);node.className='msg'+(text?' show '+type:'');node.textContent=text;node.setAttribute('role','alert');}
export function go(screen){
  if(['lists','profile'].includes(screen)&&!state.user){screen='login';toast('Faça login para acessar esta área.');}
  if(screen==='providers'&&!state.draft.items.length){screen='builder';toast('Adicione ao menos um produto.');}
  document.querySelectorAll('.screen').forEach(node=>node.classList.toggle('active',node.id===screen));
  document.querySelectorAll('.nav button').forEach(node=>node.classList.toggle('active',node.id==='n-'+screen));
  state.screen=screen;window.dispatchEvent(new CustomEvent('screen-changed',{detail:screen}));
  window.scrollTo({top:0,behavior:'smooth'});
}
const returnFocus=new Map();
export function openModal(id){returnFocus.set(id,document.activeElement);$(id).classList.add('open');$(id).querySelector('input:not([readonly]),button')?.focus();}
export function closeModal(id){$(id).classList.remove('open');returnFocus.get(id)?.focus();}
let confirmResolve=null;
export function finishConfirm(value){closeModal('confirmBack');const done=confirmResolve;confirmResolve=null;done?.(value);}
export function confirm(text,{title='Confirmar',name=null,accept='Confirmar'}={}){
  return new Promise(resolve=>{confirmResolve=resolve;$('confirmTitle').textContent=title;$('confirmText').textContent=text;$('confirmTyping').classList.toggle('hidden',name===null);$('confirmInput').value='';$('confirmActionBtn').textContent=accept;$('confirmActionBtn').disabled=name!==null;$('confirmInput').oninput=()=>{$('confirmActionBtn').disabled=$('confirmInput').value!==name;};$('confirmActionBtn').onclick=()=>finishConfirm(true);openModal('confirmBack');});
}
export async function busy(button,operation,label='Aguarde…'){
  if(button.disabled)return;const text=button.textContent;button.disabled=true;button.textContent=label;
  try{return await operation();}finally{button.disabled=false;button.textContent=text;}
}
export function initModals(){
  document.addEventListener('keydown',event=>{
    const modal=[...document.querySelectorAll('.modalback.open')].at(-1);if(!modal)return;
    if(event.key==='Escape'){if(modal.id==='confirmBack')finishConfirm(false);else closeModal(modal.id);}
    if(event.key==='Tab'){const nodes=[...modal.querySelectorAll('button:not(:disabled),input:not(:disabled),select')].filter(n=>n.offsetParent!==null);const first=nodes[0],last=nodes.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}}
  });
  $('modalback').addEventListener('click',event=>{if(event.target===$('modalback'))closeModal('modalback');});
}

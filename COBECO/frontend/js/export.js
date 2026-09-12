import {state} from './state.js';
import {toast} from './ui.js';
export function csvText(draft) {
  const cell = value => {let text=String(value); if(/^[=+@-]/.test(text)) text="'"+text;return `"${text.replaceAll('"','""')}"`;};
  const rows=[['Lista','Produto','Quantidade','Unidade'],...draft.items.map(i => [draft.name,i.name,i.quantity,i.unit])];
  return '\uFEFF'+rows.map(row=>row.map(cell).join(';')).join('\r\n');
}
export function exportList() {
  if(!state.draft.items.length) return toast('Adicione pelo menos um produto.',true);
  const now=new Date(); const day=[now.getFullYear(),String(now.getMonth()+1).padStart(2,'0'),String(now.getDate()).padStart(2,'0')].join('');
  const url=URL.createObjectURL(new Blob([csvText(state.draft)],{type:'text/csv;charset=utf-8'}));
  const link=document.createElement('a');link.href=url;link.download=`lista_${day}.csv`;document.body.append(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export function printList() { if(!state.draft.items.length) return toast('Adicione produtos antes de imprimir.',true); document.getElementById(state.screen==='results'?'results':'builder').classList.add('print-active');window.print(); }

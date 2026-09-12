import {renew,api} from './api.js';
import {initAuth,doLogin,registerUser,updatePasswordRules,handleAuthNav,recoverFind,recoverValidate,recoverReset,saveProfile,showReset} from './auth.js';
import {initList,addItem,saveList,startNewList} from './list.js';
import {initCompare,filterProviders,selectAll,clearSelection,calculate} from './compare.js';
import {exportList,printList} from './export.js';
import {$,toast,go,closeModal,finishConfirm,initModals} from './ui.js';
const actions={
  'handleAuthNav()':handleAuthNav,'addItem()':addItem,'saveList()':saveList,'exportCSV()':exportList,
  'registerUser()':registerUser,'doLogin(false)':()=>doLogin(false),'doLogin(true)':()=>doLogin(true),
  'recoverFind()':recoverFind,'recoverValidate()':recoverValidate,'recoverReset()':recoverReset,
  'startNewList()':startNewList,'compare()':calculate,'window.print()':printList,'saveProfile()':saveProfile,
  'closeLoginModal()':()=>closeModal('modalback'),'closeConfirm()':()=>finishConfirm(false),
  'goRegisterFromModal()':()=>{closeModal('modalback');go('register');},
  'goRecoverFromModal()':()=>{closeModal('modalback');go('recover');},'selectAll()':selectAll,'clearSelection()':clearSelection,
};
for(const screen of ['landing','builder','lists','providers','profile','login','register','recover'])actions[`go('${screen}')`]=()=>go(screen);
document.querySelectorAll('button[data-action]').forEach(button=>{const handler=actions[button.dataset.action];if(handler)button.addEventListener('click',handler);});
$('regPass').addEventListener('input',updatePasswordRules);$('range').addEventListener('input',filterProviders);
initModals();initAuth();initList();initCompare();
window.addEventListener('beforeprint',()=>document.getElementById(document.getElementById('results').classList.contains('active')?'results':'builder').classList.add('print-active'));
window.addEventListener('afterprint',()=>document.querySelectorAll('.print-active').forEach(node=>node.classList.remove('print-active')));
window.addEventListener('storage-error',()=>toast('Não foi possível preservar o rascunho. Mantenha esta aba aberta.',true));
await renew();
if(location.hash.startsWith('#reset?')){const params=new URLSearchParams(location.hash.slice(7));try{const config=await api('/config');if(config.recovery_mode==='log')showReset(params.get('username')||'','log','',params.get('token')||'');}catch(error){toast(error.message,true);}history.replaceState(null,'',location.pathname);}

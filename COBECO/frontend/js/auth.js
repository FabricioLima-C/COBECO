import {api} from './api.js';
import {state,session} from './state.js';
import {$,toast,message,go,confirm,busy,openModal,closeModal} from './ui.js';
const value=id=>$(id).value;
const attempts=new Map();
let recovery={username:'',token:null,mode:'code'};
let recoveryMode='code';
export function showRecoveryCode(code){$('recoveryCodeValue').value=code;openModal('recoveryCodeBack');}
export function downloadRecoveryCode(){
  const code=value('recoveryCodeValue');if(!code)return;
  const url=URL.createObjectURL(new Blob(['COBECO — código de recuperação\n'+code+'\nGuarde em local seguro. Uso único.'],{type:'text/plain;charset=utf-8'}));
  const link=document.createElement('a');link.href=url;link.download='cobeco-codigo-recuperacao.txt';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export async function rotateRecoveryCode(){
  if(!value('profOldPass'))return message('profileMsg','Informe sua senha atual para gerar um novo código.');
  if(!await confirm('O código anterior e os pedidos de recuperação pendentes deixarão de funcionar.',{title:'Gerar novo código?',accept:'Gerar código'}))return;
  await busy($('rotateRecoveryBtn'),async()=>{try{const result=await api('/profile/recovery-code',{method:'POST',body:{current_password:value('profOldPass')}});$('profOldPass').value='';showRecoveryCode(result.recovery_code);}catch(error){message('profileMsg',error.message);}});
}
export function showAuth(){message('loginMsg','');openModal('modalback');}
function loginState(number,text='',type='error'){
  for(let i=1;i<=5;i++)$('stateDot'+i).classList.toggle('on',i<=number);
  $('loginPageMsg').className=text?'inline-alert '+type:'';$('loginPageMsg').textContent=text;
}
export async function doLogin(fromModal=false){
  const username=value(fromModal?'modalUser':'loginUser').trim();const password=value(fromModal?'modalPass':'loginPass');
  if(!username||!password){if(fromModal)message('loginMsg','Informe username e senha.');else loginState(3,'Informe username e senha.');return;}
  const button=$(fromModal?'modalLoginBtn':'loginPageBtn');
  await busy(button,async()=>{
    if(!fromModal)loginState(2);else message('loginMsg','');
    try{
      const result=await api('/auth/login',{method:'POST',body:{username,password}});session(result);attempts.delete(username);closeModal('modalback');$('loginPass').value='';$('modalPass').value='';go('builder');toast('Login realizado com sucesso.');loginState(1);
      if(state.draft.items.length&&await confirm('Deseja salvar sua lista atual na sua conta?',{title:'Salvar este rascunho?',accept:'Salvar lista'}))window.dispatchEvent(new CustomEvent('save-requested'));
    }catch(error){
      const count=(attempts.get(username)||0)+(error.status===401?1:0);attempts.set(username,count);
      const text=error.status===429?`Acesso temporariamente bloqueado. ${error.message}`:error.message;
      if(fromModal)message('loginMsg',text,error.status===429?'warn':'err');else loginState(error.status===429?5:count>=5?4:3,text,error.status===429||count>=5?'warn':'error');
    }
  },'Entrando…');
}
export function updatePasswordRules(){
  const password=value('regPass');const checks={len:password.length>=8,upper:/[A-Z]/.test(password),num:/\d/.test(password),spec:/[^A-Za-z0-9]/.test(password)};
  Object.entries(checks).forEach(([name,ok])=>document.querySelector(`[data-rule="${name}"]`).className='rule '+(ok?'ok':'no'));
}
export async function registerUser(){
  const data={username:value('regUser').trim(),name:value('regName').trim(),email:value('regEmail').trim(),password:value('regPass'),confirm_password:value('regPass2'),security_question:value('regQuestion'),security_answer:value('regAnswer').trim()};
  if(recoveryMode!=='question'){delete data.security_question;delete data.security_answer;}
  const button=document.querySelector('[data-action="registerUser()"]');
  await busy(button,async()=>{message('regMsg','');try{const result=await api('/auth/register',{method:'POST',body:data});$('loginUser').value=data.username;$('regPass').value='';$('regPass2').value='';$('regAnswer').value='';go('login');toast('Conta criada. Entre para salvar suas listas.');showRecoveryCode(result.recovery_code);}catch(error){message('regMsg',error.message);}});
}
export async function logout(){
  await busy($('authBtn'),async()=>{try{await api('/auth/logout',{method:'POST'});session(null);go('landing');toast('Sessão encerrada. Seu rascunho foi preservado.');}catch(error){toast(error.message,true);}});
  updateAuthUI();
}
export function handleAuthNav(){if(state.user)logout();else go('login');}
export function updateAuthUI(){$('authBtn').textContent=state.user?'Sair':'Entrar';$('memoryBadge').textContent=state.draft.id?'Lista carregada':state.user?'Conta autenticada':'Em memória';}
export function resetRecovery(){
  recovery={username:'',token:null,mode:recoveryMode};for(let i=1;i<=3;i++){$('recoverStep'+i).classList.toggle('hidden',i!==1);$('s'+i).classList.toggle('active',i===1);}
  message('recoverMsg','');$('recAnswer').value='';$('recPass').value='';$('recPass2').value='';
}
export async function recoverFind(){
  await busy(document.querySelector('[data-action="recoverFind()"]'),async()=>{try{
    const username=value('recUser').trim();const result=await api('/auth/recovery',{method:'POST',body:{username}});recovery={username,mode:result.mode,token:null};
    $('recQuestion').value=result.question||'Cole o token do link registrado no log de desenvolvimento.';
    document.querySelector('label[for="recAnswer"]').textContent=result.mode==='code'?'Código de recuperação':result.mode==='log'?'Token':'Resposta';$('recoverStep1').classList.add('hidden');$('recoverStep2').classList.remove('hidden');$('s2').classList.add('active');message('recoverMsg',result.message||'',result.message?'ok':'err');
  }catch(error){message('recoverMsg',error.message);}});
}
export async function recoverValidate(){
  await busy(document.querySelector('[data-action="recoverValidate()"]'),async()=>{try{
    if(recovery.mode!=='log'){const result=await api('/auth/recovery/verify',{method:'POST',body:{username:recovery.username,answer:value('recAnswer')}});recovery.token=result.token;}
    else{if(!value('recAnswer').trim())throw new Error('Informe o token.');recovery.token=value('recAnswer').trim();}
    $('recAnswer').value='';$('recoverStep2').classList.add('hidden');$('recoverStep3').classList.remove('hidden');$('s3').classList.add('active');message('recoverMsg','');
  }catch(error){message('recoverMsg',error.message,error.status===429?'warn':'err');}});
}
export async function recoverReset(){
  await busy(document.querySelector('[data-action="recoverReset()"]'),async()=>{try{
    await api('/auth/reset',{method:'POST',body:{username:recovery.username,token:recovery.token,new_password:value('recPass'),confirm_password:value('recPass2')}});session(null);resetRecovery();go('login');toast('Senha alterada. Entre e gere um novo código de recuperação no perfil.');
  }catch(error){message('recoverMsg',error.message);}});
}
export function showReset(username,mode,question='',token=''){
  go('recover');recovery={username,mode,token};$('recUser').value=username;
  if(token){$('recoverStep1').classList.add('hidden');$('recoverStep3').classList.remove('hidden');$('s2').classList.add('active');$('s3').classList.add('active');}
}
export function renderProfile(){
  if(!state.user)return;const user=state.user;$('profUser').value=user.username;$('profName').value=user.name;$('profEmail').value=user.email;$('profileAvatar').textContent=user.name.slice(0,1).toUpperCase();$('profOldPass').value='';$('profNewPass').value='';$('profNewPass2').value='';message('profileMsg','');
}
export async function saveProfile(){
  if(value('profNewPass')!==value('profNewPass2'))return message('profileMsg','A confirmação da nova senha não corresponde.');
  const data={name:value('profName').trim(),email:value('profEmail').trim(),current_password:value('profOldPass')};if(value('profNewPass'))data.new_password=value('profNewPass');
  await busy(document.querySelector('[data-action="saveProfile()"]'),async()=>{try{
    const user=await api('/profile',{method:'PATCH',body:data});
    if(data.new_password){session(null);go('login');toast('Senha alterada. Entre e gere um novo código de recuperação no perfil.');}
    else{session({user,access_token:state.token});renderProfile();message('profileMsg','Perfil atualizado com sucesso.','ok');}
  }catch(error){message('profileMsg',error.message);}});
}
export function initAuth(){
  api('/config').then(config=>{recoveryMode=config.recovery_mode;for(const id of ['regQuestion','regAnswer'])$(id).closest('.field').classList.toggle('hidden',recoveryMode!=='question');$('recoveryHint').textContent=recoveryMode==='code'?'Use o código que você guardou ao cadastrar sua conta ou no perfil.':recoveryMode==='question'?'Informe sua resposta de segurança cadastrada.':'Use o token de recuperação fornecido no ambiente de desenvolvimento.';}).catch(error=>toast(error.message,true));
  window.addEventListener('session-changed',()=>{updateAuthUI();if(!state.user&&['profile','lists'].includes(state.screen))go('login');});
  window.addEventListener('screen-changed',event=>{if(event.detail==='profile')renderProfile();if(event.detail==='recover')resetRecovery();if(event.detail==='login')loginState(1);});
  [['loginPass',()=>doLogin(false)],['modalPass',()=>doLogin(true)],['regAnswer',registerUser],['recUser',recoverFind],['recAnswer',recoverValidate],['recPass2',recoverReset]].forEach(([id,action])=>$(id).addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();action();}}));
  session(null);
}

import {state, session} from './state.js';
let renewing = null;
export async function renew() {
  if (!renewing) renewing = fetch('/api/auth/refresh', {method:'POST', credentials:'same-origin'})
    .then(async r => { if (!r.ok) { session(null); return false; } session(await r.json()); return true; })
    .catch(() => { session(null); return false; }).finally(() => { renewing = null; });
  return renewing;
}
export async function api(path, {method='GET', body, signal, retry=true} = {}) {
  const timeout = AbortSignal.timeout(10000);
  const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;
  let response;
  try {
    response = await fetch(`/api${path}`, {method, credentials:'same-origin', signal:combined,
      headers:{...(body ? {'Content-Type':'application/json'} : {}), ...(state.token ? {Authorization:`Bearer ${state.token}`} : {})},
      ...(body ? {body:JSON.stringify(body)} : {})});
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new Error(timeout.aborted ? 'Tempo esgotado. Tente novamente.' : 'Não foi possível conectar. Verifique sua conexão.');
  }
  if (response.status === 401 && retry && !path.startsWith('/auth/')) {
    if (await renew()) return api(path,{method,body,signal,retry:false});
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || `Não foi possível concluir (${response.status}).`);
    error.status = response.status; throw error;
  }
  return response.status === 204 ? null : response.json();
}

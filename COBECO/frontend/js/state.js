const EMPTY = () => ({id: null, owner_id: null, name: '', items: []});
let draft;
try {
  const stored = JSON.parse(sessionStorage.getItem('cobeco:draft'));
  draft = stored && typeof stored.name === 'string' && Array.isArray(stored.items) ? stored : EMPTY();
  draft.items = draft.items.filter(i => Number.isInteger(i.product_id) && i.product_id > 0 && Number.isInteger(i.quantity) && i.quantity >= 1 && i.quantity <= 9999 && typeof i.name === 'string').slice(0, 100);
} catch { draft = EMPTY(); }
export const state = {draft, user: null, token: null, selected: new Set(), category: null, minimum: 0, suppliers: [], result: null, revision: 0};
export function persist() {
  try { sessionStorage.setItem('cobeco:draft', JSON.stringify(state.draft)); }
  catch { window.dispatchEvent(new CustomEvent('storage-error')); }
}
export function changed() {
  state.revision += 1;
  state.result = null;
  persist();
  window.dispatchEvent(new CustomEvent('draft-changed'));
}
export function resetDraft() {
  state.draft = EMPTY(); state.selected.clear(); changed();
}
export function session(data) {
  state.user = data?.user || null; state.token = data?.access_token || null;
  // Legacy clients persisted bearer tokens. Remove these once on upgrade/logout.
  try { localStorage.removeItem('accessToken'); localStorage.removeItem('user'); } catch { /* Storage may be disabled. */ }
  window.dispatchEvent(new CustomEvent('session-changed'));
}
export function payload() { return {name: state.draft.name.trim(), items: state.draft.items.map(({product_id,quantity}) => ({product_id,quantity}))}; }

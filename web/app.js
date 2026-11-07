const loginArea = document.getElementById('login-area');
const dashboard = document.getElementById('dashboard');
const notice = document.getElementById('notice');
const list = document.getElementById('documents');
let timer = null;

async function request(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', ...options });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Erro HTTP ${response.status}`);
  }
  return response;
}
function message(text) { notice.textContent = text; }
function showLogin(active) { loginArea.hidden = !active; dashboard.hidden = active; }
function statusLabel(status) { return ({ queued: 'Na fila', processing: 'Processando', ready: 'Pronto', error: 'Erro' })[status] || status; }

async function refresh() {
  try {
    const docs = await (await request('/documents')).json();
    list.replaceChildren();
    for (const doc of docs) {
      const card = document.createElement('article');
      card.className = 'rounded-xl bg-white p-4 shadow';
      const title = document.createElement('strong'); title.textContent = doc.name;
      const state = document.createElement('p'); state.textContent = `${statusLabel(doc.status)} — ${doc.stage}`;
      card.append(title, state);
      if (doc.error) { const error = document.createElement('p'); error.textContent = doc.error; card.append(error); }
      const rename = document.createElement('button'); rename.textContent = 'Renomear'; rename.className = 'mr-4 underline';
      rename.onclick = async () => {
        const name = prompt('Novo nome', doc.name);
        if (!name) return;
        try { await request(`/documents/${doc.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json', Origin: location.origin }, body: JSON.stringify({ name }) }); await refresh(); }
        catch (error) { message(error.message); }
      };
      card.append(rename);
      if (doc.status === 'ready') {
        const link = document.createElement('a'); link.href = `/documents/${doc.id}/json`; link.textContent = 'Baixar JSON'; link.className = 'underline'; card.append(link);
      }
      list.append(card);
    }
    if (timer) clearTimeout(timer);
    if (docs.some(doc => ['queued', 'processing'].includes(doc.status))) timer = setTimeout(refresh, 2000);
  } catch (error) { message(error.message); }
}
document.getElementById('login-form').onsubmit = async event => {
  event.preventDefault();
  try {
    await request('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json', Origin: location.origin }, body: JSON.stringify({ email: document.getElementById('email').value, password: document.getElementById('password').value }) });
    document.getElementById('password').value = ''; showLogin(false); await refresh();
  } catch (error) { message(error.message); }
};
document.getElementById('logout').onclick = async () => {
  try { await request('/auth/logout', { method: 'POST', headers: { Origin: location.origin } }); if (timer) clearTimeout(timer); showLogin(true); list.replaceChildren(); }
  catch (error) { message(error.message); }
};
document.getElementById('upload-form').onsubmit = async event => {
  event.preventDefault();
  const form = new FormData(); form.append('file', document.getElementById('file').files[0]); form.append('document_type', 'Texto');
  const name = document.getElementById('doc-name').value.trim(); if (name) form.append('name', name);
  try { await request('/documents', { method: 'POST', headers: { Origin: location.origin }, body: form }); message('Documento recebido. Acompanhe o status abaixo.'); await refresh(); }
  catch (error) { message(error.message); }
};
request('/auth/me').then(() => { showLogin(false); refresh(); }).catch(() => showLogin(true));

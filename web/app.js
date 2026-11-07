const $ = id => document.getElementById(id);
let timer = null, folders = [], documents = [], identity = null;
const sharedToken = new URLSearchParams(location.hash.slice(1)).get('share');
const labels = { queued: 'Na fila', processing: 'Processando', ready: 'Pronto', error: 'Não convertido' };
function message(text) { $('notice').textContent = text; }
async function request(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', ...options });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (response.status === 401) showLogin(true);
    throw new Error(typeof body.detail === 'string' ? body.detail : `Confira os campos. Erro HTTP ${response.status}`);
  }
  return response;
}
const json = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
function showLogin(active) { $('login-area').hidden = !active; $('dashboard').hidden = active; if (active && timer) clearTimeout(timer); }
function option(value, label) { const node = document.createElement('option'); node.value = value; node.textContent = label; return node; }
function link(parent, url, label) { const a = document.createElement('a'); a.href = url; a.textContent = label; a.target = '_blank'; a.rel = 'noopener noreferrer'; parent.append(a); }
function button(parent, label, handler) { const b = document.createElement('button'); b.textContent = label; b.className = 'secondary'; b.onclick = () => Promise.resolve().then(handler).catch(error => message(error.message)); parent.append(b); }
function render() {
  const list = $('documents'); list.replaceChildren();
  const filter = $('folder-filter').value;
  const shown = documents.filter(doc => filter === 'all' || (doc.folder_id || '') === filter);
  if (!shown.length) { const p = document.createElement('p'); p.textContent = 'Nenhum documento nesta pasta.'; list.append(p); }
  for (const doc of shown) {
    const card = document.createElement('article');
    const title = document.createElement('h3'); title.textContent = doc.name;
    const state = document.createElement('span'); state.className = 'badge'; state.textContent = `${labels[doc.status] || doc.status} · ${doc.document_type || 'Texto'}`;
    card.append(title, state);
    if (doc.error) { const p = document.createElement('p'); p.className = 'error'; p.textContent = doc.error; card.append(p); }
    const actions = document.createElement('div'); actions.className = 'actions';
    link(actions, `/documents/${doc.id}/original`, 'Abrir original');
    if (doc.status === 'ready') {
      link(actions, `/documents/${doc.id}/pdf`, 'Ver / salvar PDF');
      link(actions, `/documents/${doc.id}/json`, 'Baixar FHIR JSON');
      button(actions, 'Compartilhar', async () => {
        const email = prompt('Email da conta destinatária cadastrada', identity.email === 'demo1@sauva.example' ? 'demo2@sauva.example' : 'demo1@sauva.example');
        if (!email) return;
        const result = await (await request(`/documents/${doc.id}/shares`, json('POST', { email }))).json();
        $('share-url').value = location.origin + result.url; $('share-code').value = result.password;
        $('share-output').hidden = false; $('share-output').scrollIntoView({ behavior: 'smooth' });
      });
    }
    button(actions, 'Renomear', async () => {
      const name = prompt('Novo nome', doc.name); if (!name) return;
      await request(`/documents/${doc.id}`, json('PATCH', { name })); await refresh();
    });
    if (['ready', 'error'].includes(doc.status)) {
      button(actions, 'Excluir', async () => {
        if (!confirm(`Excluir definitivamente "${doc.name}"? O original, os dados processados e os acessos compartilhados serão removidos. Esta ação não pode ser desfeita.`)) return;
        await request(`/documents/${doc.id}`, { method: 'DELETE' });
        $('share-output').hidden = true; $('share-url').value = ''; $('share-code').value = '';
        message('Documento excluído.');
        await refresh();
      });
    }
    const move = document.createElement('select'); move.setAttribute('aria-label', 'Mover documento para pasta');
    move.append(option('', 'Sem pasta'), ...folders.map(f => option(f.id, f.name))); move.value = doc.folder_id || '';
    move.onchange = async () => { try { await request(`/documents/${doc.id}/folder`, json('PATCH', { folder_id: move.value || null })); await refresh(); } catch (error) { move.value = doc.folder_id || ''; message(error.message); } };
    actions.append(move); card.append(actions); list.append(card);
  }
}
async function refresh() {
  if (timer) clearTimeout(timer);
  try {
    const [folderResponse, docResponse] = await Promise.all([request('/folders'), request('/documents')]);
    folders = await folderResponse.json(); documents = await docResponse.json();
    const filter = $('folder-filter'), previous = filter.value;
    filter.replaceChildren(option('all', 'Todos os documentos'), option('', 'Sem pasta'), ...folders.map(f => option(f.id, f.name)));
    filter.value = [...filter.options].some(o => o.value === previous) ? previous : 'all';
    render();
    if (documents.some(doc => ['queued', 'processing'].includes(doc.status))) timer = setTimeout(refresh, 2500);
  } catch (error) { message(error.message); }
}
async function signedIn(user) {
  identity = user; $('identity').textContent = user.email; showLogin(false);
  $('shared-area').hidden = !sharedToken; await refresh();
}
$('login-form').onsubmit = async event => {
  event.preventDefault();
  try {
    const user = await (await request('/auth/login', json('POST', { email: $('email').value, password: $('password').value }))).json();
    $('password').value = ''; await signedIn(user); message('Sessão iniciada.');
  } catch (error) { message(error.message); }
};
$('logout').onclick = async () => {
  try { await request('/auth/logout', { method: 'POST' }); showLogin(true); $('documents').replaceChildren(); $('shared-result').replaceChildren(); $('share-output').hidden = true; $('share-url').value = ''; $('share-code').value = ''; }
  catch (error) { message(error.message); }
};
$('upload-form').onsubmit = async event => {
  event.preventDefault(); const control = $('upload-button'); control.disabled = true;
  const form = new FormData(); form.append('file', $('file').files[0]); form.append('document_type', $('document-type').value);
  const name = $('doc-name').value.trim(); if (name) form.append('name', name);
  try { await request('/documents', { method: 'POST', body: form }); message('Documento recebido. Acompanhe o status abaixo.'); $('upload-form').reset(); await refresh(); }
  catch (error) { message(error.message); } finally { control.disabled = false; }
};
$('new-folder').onclick = async () => {
  const name = prompt('Nome da pasta'); if (!name) return;
  try { await request('/folders', json('POST', { name })); await refresh(); } catch (error) { message(error.message); }
};
$('redeem-form').onsubmit = async event => {
  event.preventDefault();
  try {
    const result = await (await request('/shares/redeem', json('POST', { token: sharedToken, password: $('share-password').value }))).json();
    history.replaceState(null, '', location.pathname);
    $('share-password').value = ''; $('redeem-form').hidden = true;
    const output = $('shared-result'); output.replaceChildren();
    const p = document.createElement('p'); p.textContent = `${result.name} — acesso até ${new Date(result.expires_at).toLocaleTimeString('pt-BR')}.`; output.append(p);
    for (const [kind, label] of [['original', 'Abrir original'], ['pdf', 'Ver / salvar PDF'], ['json', 'Baixar FHIR JSON']]) link(output, `/shared/${result.grant}/${kind}`, label);
    message('Resgate concluído. Você pode visualizar e baixar este documento por dez minutos.');
  } catch (error) { message(error.message); }
};
$('folder-filter').onchange = render;
$('refresh').onclick = refresh;
$('close-share').onclick = () => { $('share-output').hidden = true; $('share-url').value = ''; $('share-code').value = ''; };
request('/auth/me').then(response => response.json()).then(signedIn).catch(() => showLogin(true));

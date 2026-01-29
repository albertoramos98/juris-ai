import { API } from "./config.js";
import { logout as doLogout } from "./auth.js";

function getToken(){ return localStorage.getItem("token"); }
function authHeaders(extra = {}){
  const t = getToken();
  return { ...(t ? { Authorization:`Bearer ${t}` } : {}), ...extra };
}
function escapeHtml(str){
  return String(str ?? "").replace(/[&<>"']/g,(s)=>({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[s]));
}
async function readError(res){
  try{
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")){
      const d = await res.json();
      return d?.detail || JSON.stringify(d);
    }
    return await res.text();
  }catch{ return "Erro desconhecido"; }
}
async function apiFetch(path, options = {}){
  let res;
  try{
    res = await fetch(`${API}${path}`, { ...options, headers: authHeaders(options.headers || {}) });
  }catch(e){
    console.error(e);
    alert("Falha de rede. Confere o backend.");
    return null;
  }
  if (res.status === 401){
    doLogout();
    window.location.href="index.html";
    return null;
  }
  if (res.status === 423){
    let payload = {};
    try{
      const data = await res.json();
      payload = data?.detail || data || {};
    }catch{ payload = { message: "Office blocked." }; }
    localStorage.setItem("juris_block_info", JSON.stringify(payload));
    window.location.href="dashboard.html";
    return null;
  }
  return res;
}

const el = {
  processSelect: document.getElementById("processSelect"),
  processMeta: document.getElementById("processMeta"),
  btnRefresh: document.getElementById("btnRefresh"),

  deadlineDesc: document.getElementById("deadline-desc"),
  deadlineDate: document.getElementById("deadline-date"),
  deadlineResp: document.getElementById("deadline-resp"),
  deadlineCritical: document.getElementById("deadline-critical"),
  btnCreateDeadline: document.getElementById("btnCreateDeadline"),

  docCategory: document.getElementById("docCategory"),
  docFile: document.getElementById("docFile"),
  btnUploadDoc: document.getElementById("btnUploadDoc"),

  deadlinesList: document.getElementById("deadlinesList"),
  docsList: document.getElementById("docsList"),
};

let state = { processes:[], selected:null, deadlines:[], docs:[] };

window.logout = function(){
  doLogout();
  window.location.href="index.html";
};

function enableActions(ok){
  el.btnCreateDeadline.disabled = !ok;
  el.btnUploadDoc.disabled = !ok;
}

function renderProcesses(){
  if (!state.processes.length){
    el.processSelect.innerHTML = `<option value="">Nenhum processo</option>`;
    enableActions(false);
    return;
  }
  el.processSelect.innerHTML =
    `<option value="">Selecione</option>` +
    state.processes.map(p=>{
      const label = p.number ? `Processo ${p.number}` : `Processo #${p.id}`;
      return `<option value="${p.id}">${escapeHtml(label)}</option>`;
    }).join("");
}

function renderDeadlines(){
  if (!state.selected){
    el.deadlinesList.innerHTML = `<p class="muted">Selecione um processo.</p>`;
    return;
  }
  const list = state.deadlines.filter(d => Number(d.process_id) === Number(state.selected.id));

  if (!list.length){
    el.deadlinesList.innerHTML = `<p class="muted">Nenhum prazo nesse processo.</p>`;
    return;
  }

  el.deadlinesList.innerHTML = list.map(d=>{
    const badge = d.is_critical
      ? `<span class="badge badge-danger">CRÍTICO</span>`
      : `<span class="badge badge-muted">NORMAL</span>`;

    return `
      <div class="deadline-item" style="margin-bottom:10px;">
        <div class="deadline-left">
          <div class="deadline-title">${badge}<span>${escapeHtml(d.description)}</span></div>
          <div class="deadline-meta">Vence: ${escapeHtml(d.due_date)} • Resp: ${escapeHtml(d.responsible)}</div>
        </div>
        <div class="deadline-right" style="display:flex; gap:8px;">
          <button class="secondary btn-small" data-sync="${d.id}">📅 Calendar</button>
          ${(!d.completed && d.is_critical) ? `<button class="btn-small" data-complete="${d.id}">✅ Concluir</button>` : ``}
        </div>
      </div>
    `;
  }).join("");

  // handlers
  el.deadlinesList.querySelectorAll("[data-sync]").forEach(btn=>{
    btn.addEventListener("click", async ()=>{
      const id = btn.getAttribute("data-sync");
      const res = await apiFetch(`/deadlines/${id}/sync_calendar`, { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify({}) });
      if (!res) return;
      if (!res.ok){ alert(await readError(res)); return; }
      const data = await res.json();
      const link = data.openLink || data.htmlLink;
      if (link) window.open(link, "_blank");
      else alert("Evento criado.");
    });
  });

  el.deadlinesList.querySelectorAll("[data-complete]").forEach(btn=>{
    btn.addEventListener("click", async ()=>{
      const id = btn.getAttribute("data-complete");
      const res = await apiFetch(`/deadlines/${id}/complete`, { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify({}) });
      if (!res) return;
      if (!res.ok){ alert(await readError(res)); return; }
      await loadDeadlines();
      alert("Concluído ✅");
    });
  });
}

function renderDocs(){
  if (!state.selected){
    el.docsList.innerHTML = `<p class="muted">Selecione um processo.</p>`;
    return;
  }
  if (!state.docs.length){
    el.docsList.innerHTML = `<p class="muted">Sem documentos.</p>`;
    return;
  }

  el.docsList.innerHTML = state.docs.map(d=>{
    const link = d.drive_web_view_link
      ? `<a href="${escapeHtml(d.drive_web_view_link)}" target="_blank"><button class="secondary btn-small">Abrir</button></a>`
      : `<span class="muted">sem link</span>`;

    return `
      <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;
                  padding:12px;border:1px solid rgba(255,255,255,.08);border-radius:14px;
                  background: rgba(255,255,255,.04);margin-bottom:10px;">
        <div style="min-width:0;">
          <div style="font-weight:800;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
            ${escapeHtml(d.file_name)}
          </div>
          <div class="muted" style="margin-top:4px;">
            ${escapeHtml(d.category)} • ${escapeHtml(d.status)}
          </div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">${link}</div>
      </div>
    `;
  }).join("");
}

async function loadProcesses(){
  const res = await apiFetch(`/processes/`);
  if (!res) return;
  if (!res.ok){ alert(await readError(res)); return; }
  state.processes = await res.json();
  renderProcesses();
}

async function loadDeadlines(){
  const res = await apiFetch(`/deadlines/`);
  if (!res) return;
  if (!res.ok){ alert(await readError(res)); return; }
  state.deadlines = await res.json();
  renderDeadlines();
}

async function loadDocs(pid){
  el.docsList.innerHTML = `<p class="muted">Carregando...</p>`;
  const res = await apiFetch(`/processes/${pid}/documents`);
  if (!res) return;
  if (!res.ok){ alert(await readError(res)); return; }
  state.docs = await res.json();
  renderDocs();
}

async function createDeadlineForProcess(){
  if (!state.selected) return;

  const description = (el.deadlineDesc.value || "").trim();
  const due_date = el.deadlineDate.value || "";
  const responsible = (el.deadlineResp.value || "").trim();
  const is_critical = !!el.deadlineCritical.checked;

  if (!description || !due_date || !responsible) return alert("Preencha descrição, data e responsável.");

  const res = await apiFetch(`/deadlines/`, {
    method:"POST",
    headers:{ "Content-Type":"application/json" },
    body: JSON.stringify({
      description,
      due_date,
      responsible,
      process_id: state.selected.id,
      is_critical
    })
  });

  if (!res) return;
  if (!res.ok){ alert(await readError(res)); return; }

  el.deadlineDesc.value = "";
  el.deadlineDate.value = "";
  el.deadlineResp.value = "";
  el.deadlineCritical.checked = false;

  await loadDeadlines();
  alert("Prazo criado ✅");
}

async function uploadDocForProcess(){
  if (!state.selected) return;
  const file = el.docFile.files?.[0];
  if (!file) return alert("Selecione um arquivo.");

  const fd = new FormData();
  fd.append("category", el.docCategory.value);
  fd.append("file", file);

  const res = await apiFetch(`/processes/${state.selected.id}/documents/upload`, { method:"POST", body: fd });
  if (!res) return;
  if (!res.ok){ alert(await readError(res)); return; }

  el.docFile.value = "";
  await loadDocs(state.selected.id);
  alert("Upload concluído ✅");
}

function onProcessChange(){
  const id = Number(el.processSelect.value || 0);
  state.selected = state.processes.find(p=>p.id === id) || null;

  if (!state.selected){
    el.processMeta.innerText = "";
    enableActions(false);
    state.docs = [];
    renderDeadlines();
    renderDocs();
    return;
  }

  enableActions(true);
  el.processMeta.innerText = `ID: ${state.selected.id} • Vara: ${state.selected.court || "—"} • Tipo: ${state.selected.type || "—"} • Nº: ${state.selected.number || "—"}`;

  loadDeadlines();
  loadDocs(state.selected.id);
}

el.processSelect.addEventListener("change", onProcessChange);
el.btnRefresh.addEventListener("click", async ()=>{
  await loadProcesses();
  if (state.selected?.id){
    await loadDeadlines();
    await loadDocs(state.selected.id);
  }
});
el.btnCreateDeadline.addEventListener("click", createDeadlineForProcess);
el.btnUploadDoc.addEventListener("click", uploadDocForProcess);

(function init(){
  if (!getToken()){ window.location.href="index.html"; return; }
  loadProcesses();
})();

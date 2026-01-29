import { API } from "./config.js";
import { logout as doLogout } from "./auth.js";

function getToken(){ return localStorage.getItem("token"); }
function authHeaders(extra = {}){
  const t = getToken();
  return { ...(t ? { Authorization:`Bearer ${t}` } : {}), ...extra };
}
function escapeHtml(str){
  return String(str ?? "").replace(/[&<>"']/g, (s)=>({
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
    alert("Falha de rede. Confere o backend (127.0.0.1:8000).");
    return null;
  }

  if (res.status === 401){
    doLogout();
    window.location.href = "index.html";
    return null;
  }

  if (res.status === 423){
    let payload = {};
    try{
      const data = await res.json();
      payload = data?.detail || data || {};
    }catch{ payload = { message: "Office blocked." }; }
    localStorage.setItem("juris_block_info", JSON.stringify(payload));
    window.location.href = "dashboard.html";
    return null;
  }

  return res;
}

window.logout = function(){
  doLogout();
  window.location.href = "index.html";
};

const el = {
  processSelect: document.getElementById("processSelect"),
  processMeta: document.getElementById("processMeta"),
  subject: document.getElementById("subject"),
  body: document.getElementById("body"),

  btnRefresh: document.getElementById("btnRefresh"),
  btnTemplate: document.getElementById("btnTemplate"),
  btnSend: document.getElementById("btnSend"),

  searchInput: document.getElementById("searchInput"),
  filterStatus: document.getElementById("filterStatus"),
  logsList: document.getElementById("logsList"),

  mailDot: document.getElementById("mailDot"),
  mailSub: document.getElementById("mailSub"),
  stProcess: document.getElementById("stProcess"),
  stLogs: document.getElementById("stLogs"),
  stErr: document.getElementById("stErr"),
};

let state = {
  processes: [],
  selected: null,
  logs: [],
  err: 0,
};

function setOk(msg){
  el.mailDot.className = "dot dot-green";
  if (msg) el.mailSub.innerText = msg;
}
function setWarn(msg){
  el.mailDot.className = "dot dot-yellow";
  if (msg) el.mailSub.innerText = msg;
}
function setError(msg){
  state.err += 1;
  el.stErr.innerText = String(state.err);
  el.mailDot.className = "dot dot-red";
  el.mailSub.innerText = msg || "Erro";
}

function enableSend(ok){
  el.btnSend.disabled = !ok;
}

function renderProcesses(){
  if (!state.processes.length){
    el.processSelect.innerHTML = `<option value="">Nenhum processo</option>`;
    enableSend(false);
    return;
  }

  el.processSelect.innerHTML =
    `<option value="">Selecione um processo</option>` +
    state.processes.map(p=>{
      const label = p.number ? `Processo ${p.number}` : `Processo #${p.id}`;
      return `<option value="${p.id}">${escapeHtml(label)}</option>`;
    }).join("");
}

async function loadProcesses(){
  const res = await apiFetch(`/processes/`);
  if (!res) return;
  if (!res.ok){ setError(await readError(res)); return; }
  const data = await res.json();
  state.processes = Array.isArray(data) ? data : [];
  renderProcesses();
  setOk("Processos carregados.");
}

async function loadLogs(pid){
  el.logsList.innerHTML = `<p class="muted">Carregando...</p>`;
  const res = await apiFetch(`/emails/logs?process_id=${encodeURIComponent(pid)}`);
  if (!res) return;
  if (!res.ok){
    setError(await readError(res));
    el.logsList.innerHTML = `<p class="muted">Falha ao carregar logs.</p>`;
    return;
  }
  state.logs = await res.json();
  renderLogs();
  setOk("Logs carregados.");
}

function renderLogs(){
  if (!state.selected){
    el.logsList.innerHTML = `<p class="muted">Selecione um processo.</p>`;
    el.stLogs.innerText = "0";
    return;
  }

  const q = (el.searchInput.value || "").trim().toLowerCase();
  const st = el.filterStatus.value || "";

  const filtered = (state.logs || []).filter(l=>{
    const okSt = !st || l.status === st;
    const s = `${l.subject || ""} ${l.status || ""}`.toLowerCase();
    const okQ = !q || s.includes(q);
    return okSt && okQ;
  });

  el.stLogs.innerText = String(filtered.length);

  if (!filtered.length){
    el.logsList.innerHTML = `<p class="muted">Nenhum log encontrado.</p>`;
    return;
  }

  el.logsList.innerHTML = filtered.map(l=>{
    const badge = l.status === "sent"
      ? `<span class="pill" style="background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.25);">sent</span>`
      : `<span class="pill danger">failed</span>`;

    const when = l.created_at ? escapeHtml(l.created_at) : "";
    const err = l.error ? `<div class="muted" style="margin-top:6px;color:rgba(255,80,80,.85);">Erro: ${escapeHtml(l.error)}</div>` : "";

    return `
      <div style="padding:12px;border:1px solid rgba(255,255,255,.08);border-radius:14px;
                  background: rgba(255,255,255,.04);margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">
          <div style="min-width:0;">
            <div style="font-weight:800;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
              ${escapeHtml(l.subject)}
            </div>
            <div class="muted" style="margin-top:4px;">
              Para: ${escapeHtml(l.to_email)} • ${when}
            </div>
          </div>
          <div style="display:flex;gap:8px;align-items:center;">${badge}</div>
        </div>
        ${err}
      </div>
    `;
  }).join("");
}

function onProcessChange(){
  const id = Number(el.processSelect.value || 0);
  const proc = state.processes.find(p=>p.id === id) || null;
  state.selected = proc;

  if (!proc){
    el.stProcess.innerText = "—";
    el.processMeta.innerText = "";
    enableSend(false);
    state.logs = [];
    renderLogs();
    setOk("Selecione um processo.");
    return;
  }

  el.stProcess.innerText = proc.number || String(proc.id);
  el.processMeta.innerText = `ID: ${proc.id} • Vara: ${proc.court || "—"} • Tipo: ${proc.type || "—"}`;
  enableSend(true);
  loadLogs(proc.id);
}

function applyTemplate(){
  if (!state.selected){
    alert("Selecione um processo primeiro.");
    return;
  }
  const p = state.selected;
  el.subject.value = `Solicitação de documentos — Processo ${p.number || p.id}`;
  el.body.value =
`Olá! Tudo bem?

Estamos dando andamento ao processo ${p.number || p.id}.
Para prosseguirmos, precisamos que você envie os documentos abaixo:

- (1) Documento de identificação (RG/CPF)
- (2) Comprovante de residência
- (3) Documentos relacionados ao caso (contratos, prints, comprovantes, etc.)

Assim que recebermos, confirmamos por aqui.

Atenciosamente,
Equipe`;
  setOk("Template aplicado.");
}

async function sendEmail(){
  if (!state.selected) return alert("Selecione um processo.");
  const subject = (el.subject.value || "").trim();
  const body = (el.body.value || "").trim();

  if (!subject) return alert("Preencha o assunto.");
  if (!body) return alert("Preencha a mensagem.");

  el.btnSend.disabled = true;
  el.btnSend.innerText = "Enviando...";
  setWarn("Enviando e-mail...");

  const res = await apiFetch(`/emails/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      process_id: state.selected.id,
      subject,
      body
    })
  });

  el.btnSend.innerText = "Enviar";
  el.btnSend.disabled = false;

  if (!res) return;

  if (!res.ok){
    setError(await readError(res));
    return;
  }

  const data = await res.json();

  if (data.status === "failed"){
    setError("Falhou (veja o log).");
  } else {
    setOk("Enviado ✅");
  }

  await loadLogs(state.selected.id);
}

el.processSelect.addEventListener("change", onProcessChange);
el.btnTemplate.addEventListener("click", applyTemplate);
el.btnSend.addEventListener("click", sendEmail);
el.btnRefresh.addEventListener("click", async ()=>{
  await loadProcesses();
  if (state.selected?.id) await loadLogs(state.selected.id);
});
el.searchInput.addEventListener("input", renderLogs);
el.filterStatus.addEventListener("change", renderLogs);

(function init(){
  if (!getToken()){ window.location.href="index.html"; return; }
  loadProcesses();
})();

// attacks.js
import { API } from "./config.js";
import { logout as doLogout } from "./auth.js";

function getToken(){ return localStorage.getItem("token"); }
function authHeaders(extra = {}){
  const t = getToken();
  return { ...(t ? { Authorization:`Bearer ${t}` } : {}), ...extra };
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
    const data = await res.json().catch(()=> ({}));
    localStorage.setItem("juris_block_info", JSON.stringify(data.detail || data));
    window.location.href="dashboard.html";
    return null;
  }
  return res;
}

window.logout = function(){
  doLogout();
  window.location.href="index.html";
};

const el = {
  processSelect: document.getElementById("processSelect"),
  thesis: document.getElementById("thesis"),
  goal: document.getElementById("goal"),
  risk: document.getElementById("risk"),
  refDocs: document.getElementById("refDocs"),
  template: document.getElementById("template"),
  draft: document.getElementById("draft"),
  status: document.getElementById("status"),

  btnNew: document.getElementById("btnNew"),
  btnSave: document.getElementById("btnSave"),
  btnCopy: document.getElementById("btnCopy"),
  btnExport: document.getElementById("btnExport"),
};

let processes = [];
let selectedId = null;

// ===== helpers =====
function escapeHtml(str){
  return String(str ?? "").replace(/[&<>"']/g, (s)=>({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[s]));
}

function setStatus(msg){
  if (el.status) el.status.innerText = msg || "";
}

// storage local (até ter API)
function key(){
  return selectedId ? `juris_attackdef_${selectedId}` : null;
}

function loadLocal(){
  const k = key();
  if (!k) return;
  const raw = localStorage.getItem(k);
  if (!raw) return;
  try{
    const d = JSON.parse(raw);
    el.thesis.value = d.thesis || "";
    el.goal.value = d.goal || "";
    el.risk.value = d.risk || "";
    el.refDocs.value = d.refDocs || "";
    el.template.value = d.template || "contestacao";
    el.draft.value = d.draft || "";
    setStatus("Carregado do localStorage ✅");
  }catch{}
}

function saveLocal(){
  const k = key();
  if (!k) return;
  const payload = {
    thesis: el.thesis.value,
    goal: el.goal.value,
    risk: el.risk.value,
    refDocs: el.refDocs.value,
    template: el.template.value,
    draft: el.draft.value,
    updated_at: new Date().toISOString(),
  };
  localStorage.setItem(k, JSON.stringify(payload));
  setStatus("Salvo localmente ✅");
}

function clearForm(){
  el.thesis.value = "";
  el.goal.value = "";
  el.risk.value = "";
  el.refDocs.value = "";
  el.template.value = "contestacao";
  el.draft.value = "";
}

// ===== docs integration =====
async function loadDocsForProcess(pid){
  const res = await apiFetch(`/processes/${pid}/documents`);
  if (!res) return [];
  if (!res.ok){
    // não mata a page por causa disso, só avisa
    console.warn("Falha ao carregar docs:", await readError(res));
    return [];
  }
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

function applyDocsToRefDocs(docs){
  // Se refDocs for textarea, dá pra listar multi-linha.
  // Se for input, vamos resumir e deixar um formato “copiável”.
  if (!docs.length){
    // só não sobrescreve se o usuário já digitou algo
    if (!el.refDocs.value) el.refDocs.value = "";
    return;
  }

  const lines = docs.map(d=>{
    const name = d.file_name || "arquivo";
    const cat = d.category || "outros";
    const link = d.drive_web_view_link || "";
    // formato de referência “bonito” e copiável
    return `- [${cat}] ${name}${link ? ` (${link})` : ""}`;
  });

  const isTextarea = (el.refDocs?.tagName || "").toLowerCase() === "textarea";

  if (isTextarea){
    // preenche “Anexos úteis” automaticamente, mas sem apagar se user já escreveu muito:
    if (!el.refDocs.value.trim()){
      el.refDocs.value = lines.join("\n");
    } else {
      // se já tem conteúdo, só adiciona uma seção
      el.refDocs.value =
        el.refDocs.value.trim() +
        "\n\n" +
        "— Docs do processo (auto) —\n" +
        lines.join("\n");
    }
  } else {
    // input: faz um resumo curto (pra não estourar)
    const short = docs.slice(0, 3).map(d => d.file_name).filter(Boolean).join(" | ");
    const more = docs.length > 3 ? ` (+${docs.length - 3})` : "";
    if (!el.refDocs.value.trim()){
      el.refDocs.value = `Docs: ${short}${more}`;
    } else {
      // não sobrescreve — só indica no status
      setStatus(`Docs carregados (${docs.length}).`);
    }
  }
}

// ===== processes =====
async function loadProcesses(){
  const res = await apiFetch(`/processes/`);
  if (!res) return;
  if (!res.ok){ alert(await readError(res)); return; }
  processes = await res.json();

  el.processSelect.innerHTML =
    `<option value="">Selecione um processo</option>` +
    processes.map(p=>{
      const label = p.number ? `Processo ${p.number}` : `Processo #${p.id}`;
      return `<option value="${p.id}">${escapeHtml(label)}</option>`;
    }).join("");
}

// ===== events =====
el.processSelect.addEventListener("change", async ()=>{
  selectedId = Number(el.processSelect.value || 0) || null;

  clearForm();

  if (!selectedId){
    setStatus("Selecione um processo.");
    return;
  }

  // 1) carrega rascunho local
  loadLocal();

  // 2) puxa docs do processo e preenche anexos úteis
  setStatus("Carregando docs do processo...");
  const docs = await loadDocsForProcess(selectedId);
  applyDocsToRefDocs(docs);

  // 3) se não tinha nada no local e a gente preencheu anexos, salva
  if (docs.length) saveLocal();

  setStatus(`Processo selecionado ✅ (docs: ${docs.length})`);
});

el.btnNew.addEventListener("click", ()=>{
  clearForm();
  setStatus("Novo rascunho.");
});

el.btnSave.addEventListener("click", async ()=>{
  if (!selectedId) return alert("Selecione um processo.");
  saveLocal();

  // FUTURO: plugar API
});

el.btnCopy.addEventListener("click", async ()=>{
  await navigator.clipboard.writeText(el.draft.value || "");
  setStatus("Copiado ✅");
});

el.btnExport.addEventListener("click", ()=>{
  const text = el.draft.value || "";
  const blob = new Blob([text], { type:"text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `ataque_defesa_${selectedId || "sem_processo"}.txt`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  setStatus("Exportado ✅");
});

// autosave local quando digitando (leve)
let t = null;
["input","change"].forEach(evt=>{
  document.addEventListener(evt, ()=>{
    if (!selectedId) return;
    clearTimeout(t);
    t = setTimeout(saveLocal, 600);
  }, true);
});

(function init(){
  if (!getToken()){ window.location.href="index.html"; return; }
  loadProcesses();
  setStatus("Pronto.");
})();

// documents.js
import { API } from "./config.js";
import { logout as doLogout } from "./auth.js";

function getToken() { return localStorage.getItem("token"); }

function authHeaders(extra = {}) {
  const t = getToken();
  return { ...(t ? { Authorization: `Bearer ${t}` } : {}), ...extra };
}

function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (s) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[s]));
}

async function readError(res) {
  try {
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const d = await res.json();
      return d?.detail || JSON.stringify(d);
    }
    return await res.text();
  } catch {
    return "Erro desconhecido";
  }
}

async function apiFetch(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API}${path}`, {
      ...options,
      headers: authHeaders(options.headers || {})
    });
  } catch (e) {
    console.error(e);
    alert("Falha de rede. Confere o backend (127.0.0.1:8000).");
    return null;
  }

  if (res.status === 401) {
    doLogout();
    window.location.href = "index.html";
    return null;
  }

  if (res.status === 423) {
    let payload = {};
    try {
      const data = await res.json();
      payload = data?.detail || data || {};
    } catch {
      payload = { message: "Office blocked." };
    }
    localStorage.setItem("juris_block_info", JSON.stringify(payload));
    window.location.href = "dashboard.html";
    return null;
  }

  return res;
}

const el = {
  processSelect: document.getElementById("processSelect"),
  processMeta: document.getElementById("processMeta"),
  btnUpload: document.getElementById("btnUpload"),
  btnLoad: document.getElementById("btnLoad"),
  btnRefresh: document.getElementById("btnRefresh"),
  btnLogout: document.getElementById("btnLogout"),

  docCategory: document.getElementById("docCategory"),
  docFile: document.getElementById("docFile"),
  uploadHint: document.getElementById("uploadHint"),

  docsList: document.getElementById("docsList"),
  searchInput: document.getElementById("searchInput"),
  filterCategory: document.getElementById("filterCategory"),

  stProcess: document.getElementById("stProcess"),
  stTotal: document.getElementById("stTotal"),
  stErr: document.getElementById("stErr"),

  docsDot: document.getElementById("docsDot"),
  docsSub: document.getElementById("docsSub"),
};

let state = { processes: [], selected: null, docs: [], err: 0 };

function setError(msg) {
  state.err += 1;
  el.stErr.innerText = String(state.err);
  el.docsDot.className = "dot dot-red";
  el.docsSub.innerText = msg || "Erro";
}

function setOk(msg) {
  el.docsDot.className = "dot dot-green";
  if (msg) el.docsSub.innerText = msg;
}

function resetErrors() {
  state.err = 0;
  el.stErr.innerText = "0";
}

function enableActions(ok) {
  el.btnUpload.disabled = !ok;
  el.btnLoad.disabled = !ok;
  el.uploadHint.innerText = ok
    ? "Escolha arquivo + categoria e faça upload."
    : "Escolha um processo primeiro.";
}

function renderDocs() {
  const q = (el.searchInput.value || "").trim().toLowerCase();
  const cat = (el.filterCategory.value || "").toLowerCase();

  const filtered = state.docs.filter(d => {
    const name = (d.file_name || "").toLowerCase();
    const c = (d.category || "").toLowerCase();
    const okCat = !cat || c === cat;
    const okQ = !q || name.includes(q) || c.includes(q);
    return okCat && okQ;
  });

  // Total = total carregado do processo (não o filtrado)
  el.stTotal.innerText = String(state.docs.length);

  if (!state.selected) {
    el.docsList.innerHTML = `<p class="muted">Selecione um processo.</p>`;
    return;
  }

  // Status útil: mostrando X/Y
  el.docsSub.innerText = `Docs carregados. Mostrando ${filtered.length}/${state.docs.length}.`;

  if (!filtered.length) {
    el.docsList.innerHTML = `<p class="muted">Nenhum doc encontrado.</p>`;
    return;
  }

  el.docsList.innerHTML = filtered.map(d => {
    const link = d.drive_web_view_link
      ? `<a href="${escapeHtml(d.drive_web_view_link)}" target="_blank" rel="noreferrer"><button class="secondary btn-small">Abrir</button></a>`
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
            ${escapeHtml(d.category)} • ${escapeHtml(d.status)} • ${escapeHtml(d.created_at || "")}
          </div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">${link}</div>
      </div>
    `;
  }).join("");
}

function renderProcesses() {
  if (!state.processes.length) {
    el.processSelect.innerHTML = `<option value="">Nenhum processo</option>`;
    enableActions(false);
    return;
  }

  el.processSelect.innerHTML =
    `<option value="">Selecione um processo</option>` +
    state.processes.map(p => {
      const label = p.number ? `Processo ${p.number}` : `Processo #${p.id}`;
      return `<option value="${p.id}">${escapeHtml(label)}</option>`;
    }).join("");
}

async function loadProcesses() {
  const res = await apiFetch(`/processes/`);
  if (!res) return;
  if (!res.ok) { setError(await readError(res)); return; }

  const data = await res.json();
  state.processes = Array.isArray(data) ? data : [];
  renderProcesses();
  setOk("Processos carregados.");
}

async function loadDocs(pid) {
  el.docsList.innerHTML = `<p class="muted">Carregando...</p>`;

  const res = await apiFetch(`/processes/${pid}/documents`);
  if (!res) return;

  if (!res.ok) {
    setError(await readError(res));
    el.docsList.innerHTML = `<p class="muted">Falha ao carregar.</p>`;
    return;
  }

  state.docs = await res.json();
  resetErrors();
  setOk("Docs carregados.");
  renderDocs();
}

async function uploadDoc(pid) {
  const file = el.docFile.files?.[0];
  const category = el.docCategory.value;

  if (!file) return alert("Selecione um arquivo.");

  const fd = new FormData();
  fd.append("category", category);
  fd.append("file", file);

  el.btnUpload.disabled = true;
  el.btnUpload.innerText = "Enviando...";

  const res = await apiFetch(`/processes/${pid}/documents/upload`, {
    method: "POST",
    body: fd
  });

  el.btnUpload.innerText = "Upload";
  el.btnUpload.disabled = false;

  if (!res) return;
  if (!res.ok) { setError(await readError(res)); return; }

  el.docFile.value = "";
  setOk("Upload concluído ✅");
  await loadDocs(pid);
}

function onProcessChange() {
  const id = Number(el.processSelect.value || 0);
  const proc = state.processes.find(p => p.id === id) || null;
  state.selected = proc;

  resetErrors();

  if (!proc) {
    el.stProcess.innerText = "—";
    el.processMeta.innerText = "";
    enableActions(false);
    state.docs = [];
    renderDocs();
    return;
  }

  el.stProcess.innerText = proc.number || String(proc.id);
  el.processMeta.innerText = `ID: ${proc.id} • Vara: ${proc.court || "—"} • Tipo: ${proc.type || "—"}`;
  enableActions(true);
  loadDocs(proc.id);
}

// Listeners
el.processSelect.addEventListener("change", onProcessChange);

el.btnUpload.addEventListener("click", () => {
  if (!state.selected) return;
  uploadDoc(state.selected.id);
});

el.btnLoad.addEventListener("click", () => {
  if (!state.selected) return;
  loadDocs(state.selected.id);
});

el.btnRefresh.addEventListener("click", async () => {
  await loadProcesses();
  if (state.selected?.id) await loadDocs(state.selected.id);
});

el.searchInput.addEventListener("input", renderDocs);
el.filterCategory.addEventListener("change", renderDocs);

el.btnLogout?.addEventListener("click", () => {
  doLogout();
  window.location.href = "index.html";
});

// Init
(function init() {
  if (!getToken()) { window.location.href = "index.html"; return; }
  loadProcesses();
})();

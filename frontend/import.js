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

function esc(s){
  return String(s ?? "").replace(/[&<>"']/g, ch => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[ch]));
}

const el = {
  btnLogout: document.getElementById("btnLogout"),
  btnRefresh: document.getElementById("btnRefresh"),
  btnReset: document.getElementById("btnReset"),

  csvFile: document.getElementById("csvFile"),
  btnPreview: document.getElementById("btnPreview"),
  btnCommit: document.getElementById("btnCommit"),

  impDot: document.getElementById("impDot"),
  impSub: document.getElementById("impSub"),

  stRows: document.getElementById("stRows"),
  stValid: document.getElementById("stValid"),
  stErr: document.getElementById("stErr"),

  previewBox: document.getElementById("previewBox"),
  errorsBox: document.getElementById("errorsBox"),
  reportBox: document.getElementById("reportBox"),
  modeHint: document.getElementById("modeHint"),
};

let state = {
  lastPreview: null,
  lastFile: null,
};

function setOk(msg){
  el.impDot.className = "dot dot-green";
  el.impSub.textContent = msg || "";
}
function setWarn(msg){
  el.impDot.className = "dot dot-yellow";
  el.impSub.textContent = msg || "";
}
function setErr(msg){
  el.impDot.className = "dot dot-red";
  el.impSub.textContent = msg || "";
}

function getMode(){
  const v = document.querySelector('input[name="mode"]:checked')?.value || "create_only";
  return v;
}

function renderModeHint(){
  const m = getMode();
  el.modeHint.textContent =
    m === "upsert"
      ? "upsert: se já existir, atualiza."
      : "create_only: se já existir, vira erro.";
}

function resetUI(){
  state.lastPreview = null;
  state.lastFile = null;
  el.btnCommit.disabled = true;

  el.stRows.textContent = "0";
  el.stValid.textContent = "0";
  el.stErr.textContent = "0";

  el.previewBox.innerHTML = `<p class="muted">Faça o preview para ver as linhas e erros.</p>`;
  el.errorsBox.innerHTML = `<p class="muted">Nenhum erro exibido.</p>`;
  el.reportBox.innerHTML = `<p class="muted">Sem relatório ainda.</p>`;

  setOk("Envie um CSV para pré-visualizar.");
}

function renderPreview(preview){
  const cols = preview.columns || [];
  const sample = preview.sample || [];

  el.stRows.textContent = String(preview.total_rows ?? 0);
  el.stValid.textContent = String(preview.valid_rows ?? 0);
  el.stErr.textContent = String((preview.errors || []).filter(e => e.row !== 0).length);

  if (!sample.length){
    el.previewBox.innerHTML = `<p class="muted">CSV sem linhas.</p>`;
    return;
  }

  const head = cols.map(c => `<th style="text-align:left;padding:10px;border-bottom:1px solid rgba(255,255,255,.08);">${esc(c)}</th>`).join("");
  const body = sample.map(r => {
    const tds = cols.map(c => `<td style="padding:10px;border-bottom:1px solid rgba(255,255,255,.06);color:rgba(255,255,255,.86);">${esc(r[c] ?? "")}</td>`).join("");
    return `<tr>${tds}</tr>`;
  }).join("");

  el.previewBox.innerHTML = `
    <div style="overflow:auto;border:1px solid rgba(255,255,255,.08);border-radius:14px;">
      <table style="width:100%;border-collapse:collapse;min-width:760px;">
        <thead><tr>${head}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>
    <p class="muted" style="margin-top:10px;">
      Mostrando as primeiras ${sample.length} linhas.
    </p>
  `;
}

function renderErrors(errors){
  if (!errors || !errors.length){
    el.errorsBox.innerHTML = `<p class="muted">Nenhum erro.</p>`;
    return;
  }

  const missingCols = errors.filter(e => e.row === 0);
  const rowErrors = errors.filter(e => e.row !== 0);

  let html = "";

  if (missingCols.length){
    html += `
      <div style="padding:12px;border:1px solid rgba(255,80,80,.25);border-radius:14px;background:rgba(255,80,80,.08);margin-bottom:10px;">
        <strong>Colunas ausentes</strong>
        <div class="muted" style="margin-top:6px;">
          ${missingCols.map(e => `• ${esc(e.field)} — ${esc(e.message)}`).join("<br/>")}
        </div>
      </div>
    `;
  }

  if (!rowErrors.length){
    html += `<p class="muted">Sem erros por linha.</p>`;
    el.errorsBox.innerHTML = html;
    return;
  }

  html += `
    <div style="border:1px solid rgba(255,255,255,.08);border-radius:14px;overflow:hidden;">
      <div style="padding:10px;border-bottom:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.04);">
        <strong>Erros por linha</strong>
      </div>
      <div style="max-height:260px;overflow:auto;">
        ${rowErrors.map(e => `
          <div style="padding:10px;border-bottom:1px solid rgba(255,255,255,.06);">
            <span class="pill danger">Linha ${esc(e.row)}</span>
            <span class="muted" style="margin-left:8px;">${esc(e.field)} — ${esc(e.message)}</span>
          </div>
        `).join("")}
      </div>
    </div>
  `;

  el.errorsBox.innerHTML = html;
}

function renderReport(commit){
  const errs = commit.errors || [];
  const rowErrors = errs.filter(e => e.row !== 0);

  el.reportBox.innerHTML = `
    <div style="padding:12px;border:1px solid rgba(255,255,255,.08);border-radius:14px;background:rgba(255,255,255,.04);">
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <span class="pill">Total: <b>${esc(commit.total_rows)}</b></span>
        <span class="pill">Criados: <b>${esc(commit.created)}</b></span>
        <span class="pill">Atualizados: <b>${esc(commit.updated)}</b></span>
        <span class="pill danger">Falharam: <b>${esc(commit.failed)}</b></span>
      </div>
      <p class="muted" style="margin-top:10px;">
        ${rowErrors.length ? `Há ${rowErrors.length} erro(s) detalhado(s) na lista.` : "Importação finalizada sem erros por linha."}
      </p>
    </div>
  `;
}

async function doPreview(){
  const file = el.csvFile.files?.[0];
  if (!file) return alert("Selecione um CSV.");

  const fd = new FormData();
  fd.append("file", file);

  el.btnPreview.disabled = true;
  el.btnPreview.textContent = "Carregando...";
  setWarn("Gerando preview...");

  const res = await apiFetch(`/imports/processes/preview`, { method:"POST", body: fd });

  el.btnPreview.textContent = "Pré-visualizar";
  el.btnPreview.disabled = false;

  if (!res) return;
  if (!res.ok){ setErr(await readError(res)); return; }

  const data = await res.json();
  state.lastPreview = data;
  state.lastFile = file;

  renderPreview(data);
  renderErrors(data.errors || []);

  const missingCols = (data.errors || []).some(e => e.row === 0);
  el.btnCommit.disabled = missingCols || (data.valid_rows ?? 0) === 0;

  if (missingCols) setErr("CSV com colunas obrigatórias ausentes.");
  else setOk("Preview pronto. Pode importar.");
}

async function doCommit(){
  const file = el.csvFile.files?.[0];
  if (!file) return alert("Selecione um CSV.");

  const mode = getMode();

  const fd = new FormData();
  fd.append("file", file);

  el.btnCommit.disabled = true;
  el.btnCommit.textContent = "Importando...";
  setWarn("Importando...");

  const res = await apiFetch(`/imports/processes/commit?mode=${encodeURIComponent(mode)}`, {
    method:"POST",
    body: fd
  });

  el.btnCommit.textContent = "Importar";

  if (!res) return;
  if (!res.ok){ setErr(await readError(res)); el.btnCommit.disabled = false; return; }

  const data = await res.json();

  // Atualiza contadores/status
  el.stRows.textContent = String(data.total_rows ?? 0);
  // valid aqui é “resultado”; mantém o número do preview na UI, mas ok
  el.stErr.textContent = String(data.failed ?? 0);

  renderReport(data);
  renderErrors(data.errors || []);

  if ((data.failed ?? 0) > 0) setWarn("Importação concluída com falhas. Veja o relatório.");
  else setOk("Importação concluída ✅");

  el.btnCommit.disabled = false;
}

el.btnLogout.addEventListener("click", () => {
  doLogout();
  window.location.href = "index.html";
});

el.btnRefresh.addEventListener("click", () => {
  // aqui não tem muito o que recarregar, mas mantém padrão do projeto
  setOk("Pronto.");
});

el.btnReset.addEventListener("click", () => {
  el.csvFile.value = "";
  resetUI();
});

el.btnPreview.addEventListener("click", doPreview);
el.btnCommit.addEventListener("click", doCommit);

document.querySelectorAll('input[name="mode"]').forEach(r => {
  r.addEventListener("change", renderModeHint);
});

(function init(){
  if (!getToken()){ window.location.href="index.html"; return; }
  renderModeHint();
  resetUI();
})();

// Removidos imports para compatibilidade global

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

/* =====================
   STATE
===================== */
let allProcesses = [];
let selectedProcessId = null;

/* =====================
   UI ELEMENTS
===================== */
const selectEl = document.getElementById("processSelect");
const metaEl = document.getElementById("processMeta");
const timelineEl = document.getElementById("timelineList");
const deadlinesEl = document.getElementById("deadlinesList");
const docsEl = document.getElementById("docsList");

/* =====================
   CORE FUNCTIONS
===================== */
async function loadProcesses() {
  try {
    const res = await fetch(`${API}/processes`, { headers: authHeaders() });
    if (res.status === 401) { window.location.href = "index.html"; return; }
    
    allProcesses = await res.json();
    renderSelect();
    
    // Auto-seleciona se houver ID na URL ou no localStorage
    const pid = new URLSearchParams(window.location.search).get("id") || localStorage.getItem("selected_process_id");
    if (pid) {
        selectEl.value = pid;
        selectProcess(pid);
    }
  } catch (e) {
    console.error("Erro ao carregar processos:", e);
  }
}

function renderSelect() {
  if (!selectEl) return;
  selectEl.innerHTML = '<option value="">Selecione um processo...</option>';
  allProcesses.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = `${p.client_name} - ${p.action_type || 'Sem Ação'}`;
    selectEl.appendChild(opt);
  });
}

async function selectProcess(id) {
  if (!id) {
    selectedProcessId = null;
    return;
  }
  selectedProcessId = id;
  localStorage.setItem("selected_process_id", id);
  
  const p = allProcesses.find(x => String(x.id) === String(id));
  if (p) {
    metaEl.innerHTML = `
      <strong>Cliente:</strong> ${p.client_name}<br/>
      <strong>Ação:</strong> ${p.action_type || 'N/A'}<br/>
      <strong>Tribunal:</strong> ${p.court || 'N/A'}
    `;
    
    // Status de indexação
    const statusEl = document.getElementById("indexStatus");
    if (statusEl) {
        if (p.rag_indexed_at) {
            statusEl.innerHTML = `<i class="fas fa-check-circle" style="color:var(--success)"></i> Treinado em: ${new Date(p.rag_indexed_at).toLocaleString()}<br/>Chunks: ${p.rag_chunk_count}`;
        } else {
            statusEl.innerHTML = `<i class="fas fa-exclamation-triangle" style="color:var(--gold)"></i> Cérebro não treinado para este caso.`;
        }
    }
  }

  // Habilita botões
  document.getElementById("btnCreateDeadline").disabled = false;
  document.getElementById("btnUploadDoc").disabled = false;
  document.getElementById("btnStartEmailFlow").disabled = false;
  document.getElementById("btnPauseEmailFlow").disabled = false;
  document.getElementById("btnStopEmailFlow").disabled = false;
  const btnIndex = document.getElementById("btnIndexAI");
  if (btnIndex) btnIndex.disabled = false;

  loadTimeline(id);
  loadDeadlines(id);
  loadDocs(id);
  loadEmailFlow(id);
}

/* =====================
   EMAIL FLOW FUNCTIONS
===================== */
async function loadEmailFlow(processId) {
    const statusEl = document.getElementById("emailFlowStatus");
    try {
        const res = await fetch(`${API}/email-flows/process/${processId}`, { headers: authHeaders() });
        if (res.status === 404) {
            statusEl.textContent = "Status: Nenhum fluxo criado para este processo.";
            return;
        }
        const flow = await res.json();
        const activeText = flow.active ? `<span style="color:var(--accent)">ATIVO</span>` : `<span style="color:var(--danger)">INATIVO</span>`;
        statusEl.innerHTML = `Status: ${activeText} | Tentativas: ${flow.attempts}/${flow.max_attempts} | Intervalo: ${flow.interval_days} dias`;
        
        if (flow.stopped_reason) {
            statusEl.innerHTML += `<br/><small class="muted">Parado por: ${flow.stopped_reason}</small>`;
        }
    } catch (e) {
        statusEl.textContent = "Status: Erro ao carregar fluxo.";
    }
}

async function startEmailFlow() {
    if (!selectedProcessId) return;
    try {
        const res = await fetch(`${API}/email-flows/`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                process_id: parseInt(selectedProcessId),
                active: true,
                interval_days: 3,
                max_attempts: 10,
                template: "cobranca_docs",
                stop_on_any_upload: true
            })
        });
        if (!res.ok) throw new Error("Erro ao iniciar cobrança.");
        alert("Cobrança automática iniciada!");
        loadEmailFlow(selectedProcessId);
    } catch (e) { alert(e.message); }
}

async function pauseEmailFlow() {
    if (!selectedProcessId) return;
    try {
        const res = await fetch(`${API}/email-flows/process/${selectedProcessId}`, { headers: authHeaders() });
        const flow = await res.json();
        const resPause = await fetch(`${API}/email-flows/${flow.id}/pause`, { method: 'POST', headers: authHeaders() });
        if (!resPause.ok) throw new Error("Erro ao pausar.");
        alert("Cobrança pausada.");
        loadEmailFlow(selectedProcessId);
    } catch (e) { alert(e.message); }
}

async function stopEmailFlow() {
    if (!selectedProcessId) return;
    try {
        const res = await fetch(`${API}/email-flows/process/${selectedProcessId}`, { headers: authHeaders() });
        const flow = await res.json();
        const resStop = await fetch(`${API}/email-flows/${flow.id}/stop`, { method: 'POST', headers: authHeaders() });
        if (!resStop.ok) throw new Error("Erro ao encerrar.");
        alert("Cobrança encerrada permanentemente.");
        loadEmailFlow(selectedProcessId);
    } catch (e) { alert(e.message); }
}

async function indexProcessForAI() {
    if (!selectedProcessId) return;
    const btn = document.getElementById("btnIndexAI");
    const statusEl = document.getElementById("indexStatus");
    
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Treinando...`;
    statusEl.textContent = "Extraindo textos e gerando vetores (RAG)...";

    try {
        const res = await fetch(`${API}/rag/process/${selectedProcessId}/index`, {
            method: 'POST',
            headers: authHeaders()
        });
        const data = await res.json();
        
        if (res.status === 400) {
            throw new Error(data.detail || "Parece que este processo não possui documentos indexáveis. Faça upload de PDFs ou Word primeiro.");
        }
        
        if (!res.ok) throw new Error(data.detail || "Erro na indexação");

        alert(`Sucesso! IA treinada com ${data.chunks} fragmentos de documentos.`);
        loadProcesses(); // recarrega para atualizar data de indexação
    } catch(e) {
        console.error("Erro completo:", e);
        const msg = e.message || JSON.stringify(e);
        alert("Erro ao indexar: " + (msg.includes("object") ? "Falha na comunicação com o servidor." : msg));
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-sync"></i> Indexar para IA`;
    }
}

async function loadTimeline(id) {
    timelineEl.innerHTML = "<p class='muted'>Carregando histórico...</p>";
    try {
        const res = await fetch(`${API}/processes/${id}/events`, { headers: authHeaders() });
        const events = await res.json();
        timelineEl.innerHTML = events.map(e => `
            <div class="alert" style="margin-bottom:8px; background:rgba(255,255,255,0.03)">
                <small class="muted">${new Date(e.created_at).toLocaleString()}</small>
                <div>${e.description}</div>
            </div>
        `).join("") || "Nenhum evento registrado.";
    } catch(e) { timelineEl.innerHTML = "Erro ao carregar."; }
}

async function loadDeadlines(id) {
    deadlinesEl.innerHTML = "<p class='muted'>Carregando prazos...</p>";
    try {
        const res = await fetch(`${API}/deadlines?process_id=${id}`, { headers: authHeaders() });
        const data = await res.json();
        deadlinesEl.innerHTML = data.map(d => `
            <div class="panel" style="padding:12px; margin-bottom:8px; border-left:4px solid ${d.is_critical ? 'var(--danger)' : 'var(--primary)'}">
                <div style="display:flex; justify-content:space-between">
                    <strong>${d.description}</strong>
                    <span class="badge ${d.completed ? 'badge-active' : 'badge-pending'}">${d.completed ? 'Concluído' : 'Pendente'}</span>
                </div>
                <small class="muted">Vencimento: ${d.due_date}</small>
            </div>
        `).join("") || "Nenhum prazo criado.";
    } catch(e) { deadlinesEl.innerHTML = "Erro ao carregar."; }
}

async function loadDocs(id) {
    docsEl.innerHTML = "<p class='muted'>Carregando documentos...</p>";
    try {
        const res = await fetch(`${API}/processes/${id}/documents`, { headers: authHeaders() });
        const data = await res.json();
        
        // Atualiza a checklist de obrigatoriedade
        updateDocumentChecklist(data);

        docsEl.innerHTML = data.map(doc => `
            <div class="alert" style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03)">
                <div>
                    <i class="fas fa-file-pdf" style="color:var(--danger)"></i> ${doc.file_name}
                    <br/><small class="muted">${doc.category}</small>
                </div>
                <a href="${doc.drive_web_view_link}" target="_blank" class="secondary btn-small">Ver no Drive</a>
            </div>
        `).join("") || "Nenhum documento anexado.";
    } catch(e) { docsEl.innerHTML = "Erro ao carregar."; }
}

function updateDocumentChecklist(docs) {
    const categoriesFound = new Set(docs.map(d => d.category));
    const items = document.querySelectorAll('.checklist-item');
    let foundCount = 0;

    items.forEach(item => {
        const cat = item.dataset.category;
        const icon = item.querySelector('i');
        
        if (categoriesFound.has(cat)) {
            item.style.color = "var(--accent)";
            icon.className = "fas fa-check-circle";
            foundCount++;
        } else {
            item.style.color = "var(--text-secondary)";
            icon.className = "far fa-circle";
        }
    });

    const badge = document.getElementById("docProgressBadge");
    if (badge) {
        if (foundCount === items.length) {
            badge.className = "badge badge-active";
            badge.textContent = "Completo";
        } else if (foundCount > 0) {
            badge.className = "badge badge-pending";
            badge.style.background = "rgba(59, 130, 246, 0.1)";
            badge.style.color = "var(--primary)";
            badge.textContent = `Em progresso (${foundCount}/${items.length})`;
        } else {
            badge.className = "badge badge-pending";
            badge.textContent = "Pendente";
        }
    }
}

/* =====================
   CORE FUNCTIONS (UPLOAD & DEADLINES)
===================== */
async function uploadDocument() {
    const fileInput = document.getElementById("docFile");
    const category = document.getElementById("docCategory").value;
    
    if (!selectedProcessId) return alert("Selecione um processo.");
    if (!fileInput.files[0]) return alert("Selecione um arquivo.");

    const btn = document.getElementById("btnUploadDoc");
    btn.disabled = true;
    btn.textContent = "Enviando...";

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("category", category);

    try {
        const res = await fetch(`${API}/processes/${selectedProcessId}/documents/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${getToken()}` },
            body: formData
        });

        if (!res.ok) throw new Error("Falha no upload.");

        alert("Documento enviado e salvo no Google Drive!");
        fileInput.value = "";
        loadDocs(selectedProcessId);
        loadTimeline(selectedProcessId);
    } catch (e) {
        alert(e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = "Fazer Upload";
    }
}

async function createDeadline() {
    const desc = document.getElementById("deadline-desc").value;
    const date = document.getElementById("deadline-date").value;
    const resp = document.getElementById("deadline-resp").value;
    const isCritical = document.getElementById("deadline-critical").checked;

    if (!selectedProcessId || !desc || !date) return alert("Preencha descrição e data.");

    const btn = document.getElementById("btnCreateDeadline");
    btn.disabled = true;

    try {
        const res = await fetch(`${API}/deadlines?process_id=${selectedProcessId}`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                description: desc,
                due_date: date,
                responsible: resp,
                is_critical: isCritical
            })
        });

        if (!res.ok) throw new Error("Erro ao criar prazo.");

        alert("Prazo criado e agendado no Google Calendar!");
        document.getElementById("deadline-desc").value = "";
        loadDeadlines(selectedProcessId);
        loadTimeline(selectedProcessId);
    } catch (e) {
        alert(e.message);
    } finally {
        btn.disabled = false;
    }
}

/* =====================
   EVENT BINDINGS
===================== */
document.addEventListener("DOMContentLoaded", () => {
    loadProcesses();
    
    selectEl?.addEventListener("change", (e) => selectProcess(e.target.value));
    
    document.getElementById("btnRefresh")?.addEventListener("click", loadProcesses);
    document.getElementById("btnUploadDoc")?.addEventListener("click", uploadDocument);
    document.getElementById("btnCreateDeadline")?.addEventListener("click", createDeadline);
    
    document.getElementById("btnRefreshTimeline")?.addEventListener("click", () => {
        if(selectedProcessId) loadTimeline(selectedProcessId);
    });
    
    document.getElementById("btnIndexAI")?.addEventListener("click", indexProcessForAI);

    document.getElementById("btnStartEmailFlow")?.addEventListener("click", startEmailFlow);
    document.getElementById("btnPauseEmailFlow")?.addEventListener("click", pauseEmailFlow);
    document.getElementById("btnStopEmailFlow")?.addEventListener("click", stopEmailFlow);
});

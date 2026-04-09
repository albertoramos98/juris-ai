// Removidos imports para compatibilidade global

function getToken() { return localStorage.getItem("token"); }

function authHeaders(extra = {}) {
  const t = getToken();
  return { ...(t ? { Authorization: `Bearer ${t}` } : {}), ...extra };
}

/* =====================
   CORE STATE
===================== */
let currentComposition = null;

/* =====================
   CORE FUNCTIONS
===================== */
async function loadProcesses() {
  const select = document.getElementById("processSelect");
  try {
    const res = await fetch(`${API}/processes`, { headers: authHeaders() });
    const data = await res.json();
    select.innerHTML = '<option value="">Selecione o processo...</option>';
    data.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.client_name;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error("Erro ao carregar processos:", e);
  }
}

async function generateStrategy() {
  const processId = document.getElementById("processSelect").value;
  const mode = document.getElementById("modeSelect").value;
  const style = document.getElementById("styleSelect").value;
  const notes = document.getElementById("notesInput").value;
  const hasAudio = document.getElementById("hasAudio").checked;
  const audioNotes = document.getElementById("audioNotes").value;
  const calculationValue = document.getElementById("calculationValue").value;

  if (!processId) return alert("Selecione um processo.");

  document.getElementById("emptyBox").style.display = "none";
  document.getElementById("resultBox").style.display = "none";
  document.getElementById("loadingBox").style.display = "block";

  try {
    const res = await fetch(`${API}/rag/compose`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        process_id: processId,
        mode: mode,
        style: style,
        notes: notes,
        has_audio: hasAudio,
        audio_notes: audioNotes,
        calculation_value: calculationValue
      })
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Erro na geração.");

    currentComposition = data.composition;
    renderResult(data);
  } catch (e) {
    alert(e.message);
    document.getElementById("emptyBox").style.display = "block";
  } finally {
    document.getElementById("loadingBox").style.display = "none";
  }
}

function renderResult(data) {
  const resultBox = document.getElementById("resultBox");
  const summary = document.getElementById("resultSummary");
  const sections = document.getElementById("resultSections");
  const sources = document.getElementById("resultSources");

  resultBox.style.display = "block";
  
  // Garantir que summary seja string
  const comp = data.composition || {};
  summary.innerText = typeof comp.summary === 'string' ? comp.summary : (comp.summary?.text || "Análise Concluída.");
  
  sections.innerHTML = "";
  
  // Se houver texto completo, mostramos como destaque
  if (comp.full_text) {
      const div = document.createElement("div");
      div.className = "alert";
      div.style.background = "rgba(59, 130, 246, 0.05)";
      div.style.borderColor = "var(--primary)";
      div.innerHTML = `<h4 style="color:var(--primary); margin-bottom:8px;">MINUTA DA PEÇA</h4><p style="font-size:14px; line-height:1.6; white-space: pre-wrap;">${comp.full_text}</p>`;
      sections.appendChild(div);
  }

  const secData = comp.sections || {};
  Object.entries(secData).forEach(([title, content]) => {
    if (typeof content === 'object') content = JSON.stringify(content);
    const div = document.createElement("div");
    div.className = "alert";
    div.style.background = "rgba(255,255,255,0.03)";
    div.innerHTML = `<h4 style="color:var(--primary); margin-bottom:8px;">${title.replace(/_/g, ' ').toUpperCase()}</h4><p style="font-size:14px; line-height:1.6;">${content}</p>`;
    sections.appendChild(div);
  });

  sources.innerHTML = "";
  (data.sources || []).forEach(s => {
    const li = document.createElement("li");
    li.style.fontSize = "12px";
    li.style.padding = "8px";
    li.style.background = "rgba(0,0,0,0.1)";
    li.style.borderRadius = "4px";
    li.innerHTML = `<strong>[${s.type?.toUpperCase() || 'LOCAL'}]</strong> ${s.meta || ''}<br/><span class="muted">${(s.excerpt || '').substring(0, 150)}...</span>`;
    sources.appendChild(li);
  });
}

async function generateFullPetition() {
  const processId = document.getElementById("processSelect").value;
  const mode = document.getElementById("modeSelect").value;
  const style = document.getElementById("styleSelect").value;
  const notes = document.getElementById("notesInput").value;
  const hasAudio = document.getElementById("hasAudio").checked;
  const audioNotes = document.getElementById("audioNotes").value;
  const calculationValue = document.getElementById("calculationValue").value;

  if (!processId) return alert("Selecione um processo.");

  const btn = document.getElementById("btnGeneratePetition");
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Redigindo Peça...';

  try {
    const res = await fetch(`${API}/rag/generate-petition`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        process_id: parseInt(processId),
        mode: mode,
        style: style,
        notes: notes,
        has_audio: hasAudio,
        audio_notes: audioNotes,
        calculation_value: calculationValue
      })
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Erro na geração da peça.");

    // No novo formato, data.draft contém o objeto da petição
    showPetitionModal(data.draft, processId, mode);
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

async function downloadPetitionDocx(draft, processId, mode) {
  const btn = document.getElementById("btnDownloadDocx");
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Criando Réplica...';

  try {
    const res = await fetch(`${API}/rag/export-docx`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        process_id: parseInt(processId),
        mode: mode,
        composition: draft // Enviamos o objeto completo para o mapeamento inteligente
      })
    });
    
    if (!res.ok) throw new Error("Erro ao exportar Word.");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Replica_Peticao_${processId}.docx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

function showPetitionModal(draft, processId, mode) {
  let modal = document.getElementById("petitionModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "petitionModal";
    modal.className = "modal-overlay";
    modal.innerHTML = `
      <div class="modal-content" style="max-width: 900px; width: 90%; max-height: 90vh; overflow-y: auto; background: var(--card-bg); padding: 32px; border-radius: 16px; border: 1px solid var(--card-border); position: relative;">
        <button class="close-modal" style="position: absolute; top: 16px; right: 16px; background: none; border: none; color: var(--text-secondary); font-size: 20px; cursor: pointer;"><i class="fas fa-times"></i></button>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid var(--card-border); padding-bottom: 16px;">
          <h2 id="modalTitle" style="margin: 0; color: var(--primary);">Rascunho da Peça</h2>
          <div style="display: flex; gap: 8px;">
            <button id="btnDownloadDocx" class="secondary btn-small"><i class="fas fa-file-word"></i> Baixar Réplica .DOCX</button>
            <button id="btnCopyFullText" class="primary btn-small"><i class="fas fa-copy"></i> Copiar Tudo</button>
          </div>
        </div>
        <div id="modalBody" style="white-space: pre-wrap; font-family: 'Inter', sans-serif; line-height: 1.8; color: var(--text-main); font-size: 15px; padding: 20px; background: rgba(255,255,255,0.02); border-radius: 8px;"></div>
      </div>
    `;
    document.body.appendChild(modal);
    
    modal.querySelector(".close-modal").onclick = () => modal.style.display = "none";
    window.onclick = (event) => { if (event.target == modal) modal.style.display = "none"; };
  }

  const fullText = draft.full_text || "Texto não gerado.";
  document.getElementById("modalTitle").textContent = "Minuta de " + (mode === 'attack' ? 'Inicial' : 'Contestação');
  document.getElementById("modalBody").textContent = fullText;
  
  document.getElementById("btnDownloadDocx").onclick = () => downloadPetitionDocx(draft, processId, mode);
  document.getElementById("btnCopyFullText").onclick = () => {
    navigator.clipboard.writeText(fullText);
    alert("Copiado com sucesso!");
  };

  modal.style.display = "flex";
}

/* =====================
   EVENT BINDINGS
===================== */
document.addEventListener("DOMContentLoaded", () => {
  loadProcesses();
  
  const hasAudioCheckbox = document.getElementById("hasAudio");
  const audioDetailsDiv = document.getElementById("audioDetails");
  if (hasAudioCheckbox && audioDetailsDiv) {
      hasAudioCheckbox.addEventListener("change", () => {
        audioDetailsDiv.style.display = hasAudioCheckbox.checked ? "block" : "none";
      });
  }

  document.getElementById("btnCompose")?.addEventListener("click", generateStrategy);
  document.getElementById("btnGeneratePetition")?.addEventListener("click", generateFullPetition);
  
  document.getElementById("btnCopyResult")?.addEventListener("click", () => {
    if (currentComposition) {
      const text = typeof currentComposition === 'string' ? currentComposition : JSON.stringify(currentComposition, null, 2);
      navigator.clipboard.writeText(text);
      alert("Estrutura copiada!");
    }
  });
});

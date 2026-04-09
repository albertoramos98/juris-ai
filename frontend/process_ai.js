// Removidos imports para compatibilidade global

function getToken(){ return localStorage.getItem("token"); }

function authHeaders(extra = {}){
  const t = getToken();
  return { ...(t ? { Authorization:`Bearer ${t}` } : {}), ...extra };
}

/* =====================
   CORE STATE
===================== */
let processId = new URLSearchParams(window.location.search).get("process_id");
let chatMessages = [];

/* =====================
   CORE FUNCTIONS
===================== */
async function loadProcessData() {
    if(!processId) return;
    try {
        const res = await fetch(`${API}/processes`, { headers: authHeaders() });
        const data = await res.json();
        const p = data.find(x => String(x.id) === String(processId));
        if (p) {
            document.getElementById("processTitle").textContent = `${p.client_name || 'Processo'} - ${p.action_type || 'Análise IA'}`;
        }
    } catch(e) { console.error(e); }
}

async function sendMessage() {
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if(!text) return;

    appendMessage("user", text);
    input.value = "";

    try {
        const res = await fetch(`${API}/rag/query`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                process_id: parseInt(processId),
                question: text
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Erro na consulta");
        
        appendMessage("assistant", data.answer);
        renderSources(data.sources);
    } catch(e) {
        appendMessage("assistant", "Erro ao processar resposta: " + e.message);
    }
}

function appendMessage(role, text) {
    const box = document.getElementById("chatBox");
    const div = document.createElement("div");
    div.className = role === "user" ? "chat-msg user" : "chat-msg assistant";
    div.innerHTML = `<div class="msg-content">${text}</div>`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function renderSources(sources) {
    const container = document.getElementById("sourceList");
    if(!container) return;
    container.innerHTML = "<h4>Fontes Utilizadas:</h4>";
    (sources || []).forEach(s => {
        const div = document.createElement("div");
        div.className = "source-item";
        div.innerHTML = `<small><strong>${s.category || 'DOC'}</strong>: ${s.excerpt.substring(0, 100)}...</small>`;
        container.appendChild(div);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    loadProcessData();
    document.getElementById("btnSend")?.addEventListener("click", sendMessage);
    document.getElementById("chatInput")?.addEventListener("keydown", (e) => {
        if(e.key === "Enter") sendMessage();
    });
});

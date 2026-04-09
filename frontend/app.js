// Removidos imports para compatibilidade global

// initDomGuards e outros agora vem do dom.js carregado antes
if (typeof initDomGuards === 'function') initDomGuards();
if (typeof restoreBlockedOverlayFromStorage === 'function') restoreBlockedOverlayFromStorage();

/* =====================
   TOKEN / HEADERS
===================== */
function getToken() {
  return localStorage.getItem("token");
}

function getHeaders() {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

/* =====================
   OFFICE UNLOCK (OVERRIDE)
===================== */
async function unlockOffice() {
  const password = document.getElementById("unlock-password")?.value;
  if (!password) return alert("Digite a senha do Owner.");

  try {
    const res = await fetch(`${API}/system/unlock`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ password, minutes: 30 }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Erro ao desbloquear.");
    }

    alert("Escritório desbloqueado temporariamente!");
    if (typeof hideBlockedOverlay === 'function') hideBlockedOverlay();
    location.reload();
  } catch (err) {
    alert(err.message);
  }
}

// Expõe globalmente para o onclick do HTML
window.unlockOffice = unlockOffice;

/* =====================
   DATA FETCHING
===================== */
async function loadStatus() {
  try {
    const res = await fetch(`${API}/system/status`, { headers: getHeaders() });
    if (res.status === 401) return logout();
    if (!res.ok) throw new Error();

    const data = await res.json();
    
    // Atualiza UI (função no dom.js)
    if (typeof setStatusBar === 'function') setStatusBar(data);

    if (data.blocked) {
      if (typeof showBlockedOverlay === 'function') showBlockedOverlay(data.overdue_critical);
    } else {
      if (typeof hideBlockedOverlay === 'function') hideBlockedOverlay();
    }
  } catch (e) {
    console.error("Erro ao carregar status:", e);
  }
}

async function loadKPIs() {
  try {
    const [c, p, d] = await Promise.all([
      fetch(`${API}/clients`, { headers: getHeaders() }).then(r => r.json()),
      fetch(`${API}/processes`, { headers: getHeaders() }).then(r => r.json()),
      fetch(`${API}/deadlines`, { headers: getHeaders() }).then(r => r.json())
    ]);

    document.getElementById("clients-count").innerText = c.length || 0;
    document.getElementById("processes-count").innerText = p.length || 0;
    document.getElementById("deadlines-count").innerText = d.length || 0;

    renderRecentProcesses(p);
    renderRecentDeadlines(d);
  } catch (e) {
    console.error("Erro ao carregar KPIs:", e);
  }
}

function renderRecentProcesses(list) {
  const el = document.getElementById("processes-list");
  if (!el) return;
  el.innerHTML = "";
  list.slice(0, 5).forEach(p => {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${p.client_name}</strong> - ${p.action_type || 'Sem ação'}`;
    el.appendChild(li);
  });
}

function renderRecentDeadlines(list) {
  const el = document.getElementById("deadlines-list");
  if (!el) return;
  el.innerHTML = "";
  list.filter(d => !d.completed).slice(0, 5).forEach(d => {
    const li = document.createElement("li");
    li.style.borderLeft = d.is_critical ? "4px solid var(--danger)" : "4px solid var(--primary)";
    li.innerHTML = `<div>${d.description}</div><small>${d.due_date}</small>`;
    el.appendChild(li);
  });
}

// Inicia Dashboard
document.addEventListener("DOMContentLoaded", () => {
  if (window.location.pathname.includes("dashboard.html")) {
    loadStatus();
    loadKPIs();
  }
});

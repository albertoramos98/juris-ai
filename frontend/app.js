import { API } from "./config.js";
import { logout as doLogout } from "./auth.js";

/* =====================
   TOKEN / HEADERS
===================== */
function getToken() {
  return localStorage.getItem("token");
}

function authHeaders(extra = {}) {
  const token = getToken();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

/* =====================
   GUARD
===================== */
if (!getToken()) {
  window.location.href = "index.html";
}

/* =====================
   SAFE FETCH (401 / 423 / ERR)
===================== */
async function safeFetch(url, options = {}) {
  let res;
  try {
    res = await fetch(url, options);
  } catch (e) {
    console.error("Network error:", e);
    alert("Falha de rede ao comunicar com a API.");
    return null;
  }

  if (res.status === 401) {
    doLogout();
    window.location.href = "index.html";
    return null;
  }

  // teu backend usa 423 Locked quando escritório bloqueado
  if (res.status === 423) {
    let payload = {};
    try {
      const data = await res.json();
      payload = data?.detail || data || {};
    } catch {
      payload = { message: "Office blocked." };
    }

    localStorage.setItem("juris_block_info", JSON.stringify(payload));
    showBlockedOverlay(payload);
    return null;
  }

  return res;
}

async function readError(res) {
  try {
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const data = await res.json();
      return data?.detail || JSON.stringify(data);
    }
    return await res.text();
  } catch {
    return "Erro desconhecido";
  }
}

/* =====================
   LOCK OVERLAY UI
===================== */
function showBlockedOverlay(payload) {
  const overlay = document.getElementById("lock-overlay");
  if (overlay) overlay.style.display = "flex";

  const msg = document.getElementById("lock-message");
  if (msg) {
    msg.innerText =
      payload?.message ||
      payload?.detail ||
      "Office blocked: there is an overdue critical deadline.";
  }

  const list = document.getElementById("lock-deadlines");
  if (list) {
    list.innerHTML = "";
    const overdue = payload?.overdue_critical || [];
    if (Array.isArray(overdue) && overdue.length) {
      overdue.forEach((d) => {
        const li = document.createElement("li");
        li.innerText = `#${d.id} — ${d.description} (vence: ${d.due_date})`;
        list.appendChild(li);
      });
    }
  }
}

function hideBlockedOverlay() {
  const overlay = document.getElementById("lock-overlay");
  if (overlay) overlay.style.display = "none";
}

/* =====================
   SYSTEM STATUS
===================== */
async function checkSystemStatus() {
  const res = await safeFetch(`${API}/system/status`, {
    headers: authHeaders(),
  });
  if (!res) return null;
  return await res.json();
}

/* =====================
   DATE HELPERS
===================== */
function normalizeDate(dateStr) {
  // "YYYY-MM-DD" => Date local 00:00
  const d = new Date(dateStr);
  d.setHours(0, 0, 0, 0);
  return d;
}

function todayDate() {
  const t = new Date();
  t.setHours(0, 0, 0, 0);
  return t;
}

function isToday(dateStr) {
  return normalizeDate(dateStr).getTime() === todayDate().getTime();
}

function isTomorrow(dateStr) {
  const t = todayDate();
  t.setDate(t.getDate() + 1);
  return normalizeDate(dateStr).getTime() === t.getTime();
}

function isExpired(dateStr) {
  return normalizeDate(dateStr) < todayDate();
}

/* =====================
   LOAD DASHBOARD
===================== */
async function loadDashboard() {
  // Se já tinha bloqueio salvo, mostra logo (UX melhor)
  const saved = localStorage.getItem("juris_block_info");
  if (saved) {
    try {
      showBlockedOverlay(JSON.parse(saved));
    } catch {}
  }

  const status = await checkSystemStatus();
  if (!status) return;

  if (status.blocked) {
    showBlockedOverlay(status);
    // carrega prazos pra permitir concluir e destravar
    await loadDeadlines();
    return;
  }

  localStorage.removeItem("juris_block_info");
  hideBlockedOverlay();

  // carrega tudo em paralelo
  await Promise.all([
    loadClients(),
    loadProcesses(),
    loadDeadlines(),
    loadClientsSelect(),
    loadProcessesSelect(),
  ]);
}

/* =====================
   CLIENTES
===================== */
async function loadClients() {
  const res = await safeFetch(`${API}/clients/`, {
    headers: authHeaders(),
  });
  if (!res) return;

  const data = await res.json();

  const countEl = document.getElementById("clients-count");
  if (countEl) countEl.innerText = data.length;

  const list = document.getElementById("clients-list");
  if (!list) return;

  list.innerHTML = "";

  data.forEach((c) => {
    const li = document.createElement("li");
    li.innerText = `${c.name} — ${c.document}`;
    list.appendChild(li);
  });

  return data;
}

async function createClient() {
  const nameEl = document.getElementById("client-name");
  const docEl = document.getElementById("client-doc");

  const name = nameEl?.value?.trim() || "";
  const documentValue = docEl?.value?.trim() || "";

  if (!name || !documentValue) {
    alert("Preencha nome e CPF/CNPJ.");
    return;
  }

  const res = await safeFetch(`${API}/clients/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ name, document: documentValue }),
  });

  if (!res) return;

  if (!res.ok) {
    alert(await readError(res));
    return;
  }

  if (nameEl) nameEl.value = "";
  if (docEl) docEl.value = "";

  await Promise.all([loadClients(), loadClientsSelect()]);
}

/* =====================
   PROCESSOS
===================== */
async function loadProcesses() {
  const res = await safeFetch(`${API}/processes/`, {
    headers: authHeaders(),
  });
  if (!res) return;

  const data = await res.json();

  const countEl = document.getElementById("processes-count");
  if (countEl) countEl.innerText = data.length;

  const list = document.getElementById("processes-list");
  if (!list) return;

  list.innerHTML = "";

  data.forEach((p) => {
    const li = document.createElement("li");
    li.innerText = `Processo ${p.number}`;
    list.appendChild(li);
  });

  return data;
}

async function createProcess() {
  const numberEl = document.getElementById("process-number");
  const courtEl = document.getElementById("process-court");
  const typeEl = document.getElementById("process-type");
  const clientSelect = document.getElementById("process-client-select");

  const number = numberEl?.value?.trim() || "";
  const court = courtEl?.value?.trim() || "";
  const type = typeEl?.value?.trim() || "";
  const clientId = Number(clientSelect?.value || 0);

  if (!number || !court || !type) {
    alert("Preencha número, vara e tipo de ação.");
    return;
  }

  if (!clientId) {
    alert("Selecione um cliente.");
    return;
  }

  const res = await safeFetch(`${API}/processes/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ number, court, type, client_id: clientId }),
  });

  if (!res) return;

  if (!res.ok) {
    alert(await readError(res));
    return;
  }

  if (numberEl) numberEl.value = "";
  if (courtEl) courtEl.value = "";
  if (typeEl) typeEl.value = "";

  await Promise.all([loadProcesses(), loadProcessesSelect()]);
}

/* =====================
   PRAZOS
===================== */
async function loadDeadlines() {
  const res = await safeFetch(`${API}/deadlines/`, {
    headers: authHeaders(),
  });
  if (!res) return;

  const data = await res.json();

  const countEl = document.getElementById("deadlines-count");
  if (countEl) countEl.innerText = data.length;

  const list = document.getElementById("deadlines-list");
  if (!list) return;

  list.innerHTML = "";

  data.forEach((d) => {
    const li = document.createElement("li");
    li.classList.add("deadline-item");

    // classes visuais
    if (d.completed) {
      li.classList.add("deadline-done");
    } else if (isExpired(d.due_date)) {
      li.classList.add("deadline-expired");
    } else if (isToday(d.due_date)) {
      li.classList.add("deadline-today");
    } else if (isTomorrow(d.due_date)) {
      li.classList.add("deadline-soon");
    }

    const left = document.createElement("div");
    left.classList.add("deadline-left");
    left.innerText = `${d.description} — ${d.due_date}`;

    const right = document.createElement("div");
    right.classList.add("deadline-right");

    const isCritical = !!d.is_critical;
    const canComplete = !d.completed && isExpired(d.due_date);

    if (canComplete) {
      const btn = document.createElement("button");
      btn.classList.add("btn-small");
      btn.innerText = isCritical ? "✅ Concluir (crítico)" : "✅ Concluir";
      btn.onclick = async () => {
        await completeDeadline(d.id);
      };
      right.appendChild(btn);
    }

    li.appendChild(left);
    li.appendChild(right);

    list.appendChild(li);
  });

  return data;
}

async function createDeadline() {
  const descEl = document.getElementById("deadline-desc");
  const dateEl = document.getElementById("deadline-date");
  const respEl = document.getElementById("deadline-resp");
  const procEl = document.getElementById("deadline-process-select");
  const criticalEl = document.getElementById("deadline-critical");

  const description = descEl?.value?.trim() || "";
  const due_date = dateEl?.value || "";
  const responsible = respEl?.value?.trim() || "";
  const processId = Number(procEl?.value || 0);
  const isCritical = !!criticalEl?.checked;

  if (!description || !due_date || !responsible) {
    alert("Preencha descrição, data e responsável.");
    return;
  }

  if (!processId) {
    alert("Selecione um processo.");
    return;
  }

  const res = await safeFetch(`${API}/deadlines/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      description,
      due_date,
      responsible,
      process_id: processId,
      is_critical: isCritical,
    }),
  });

  if (!res) return;

  if (!res.ok) {
    alert(await readError(res));
    return;
  }

  if (descEl) descEl.value = "";
  if (dateEl) dateEl.value = "";
  if (respEl) respEl.value = "";
  if (criticalEl) criticalEl.checked = false;

  await loadDeadlines();
}

async function completeDeadline(deadlineId) {
  const res = await safeFetch(`${API}/deadlines/${deadlineId}/complete`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });

  if (!res) return;

  if (!res.ok) {
    alert(await readError(res));
    return;
  }

  // revalida status e recarrega
  localStorage.removeItem("juris_block_info");
  hideBlockedOverlay();
  await loadDashboard();
}

/* =====================
   SELECTS (evita refetch duplicado quando der)
===================== */
async function loadClientsSelect() {
  // tenta reaproveitar lista de clientes se já carregou
  const data = await loadClients();
  if (!Array.isArray(data)) return;

  const select = document.getElementById("process-client-select");
  if (!select) return;

  select.innerHTML = '<option value="">Selecione o cliente</option>';

  data.forEach((client) => {
    const option = document.createElement("option");
    option.value = client.id;
    option.innerText = client.name;
    select.appendChild(option);
  });
}

async function loadProcessesSelect() {
  const data = await loadProcesses();
  if (!Array.isArray(data)) return;

  const select = document.getElementById("deadline-process-select");
  if (!select) return;

  select.innerHTML = '<option value="">Selecione o processo</option>';

  data.forEach((process) => {
    const option = document.createElement("option");
    option.value = process.id;
    option.innerText = process.number;
    select.appendChild(option);
  });
}

/* =====================
   LOGOUT
===================== */
function logout() {
  doLogout();
  window.location.href = "index.html";
}

/* =====================
   EXPORTS PRA HTML (onclick)
===================== */
window.logout = logout;
window.createClient = createClient;
window.createProcess = createProcess;
window.createDeadline = createDeadline;
window.completeDeadline = completeDeadline;

/* =====================
   INIT
===================== */
loadDashboard();

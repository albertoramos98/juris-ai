import { API } from "./config.js";
import { logout as doLogout } from "./auth.js";
import {
  initDomGuards,
  restoreBlockedOverlayFromStorage,
  showBlockedOverlay,
  hideBlockedOverlay,
  clearBlockedOverlayStorage,
  setStatusBar
} from "./dom.js";

/* =====================
   INIT DOM GUARDS
===================== */
initDomGuards();
restoreBlockedOverlayFromStorage();

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
   SAFE FETCH (401 / 423 / NET ERR)
===================== */
let __netErrShownAt = 0;
const __NET_ERR_COOLDOWN_MS = 10000;

function showNetErrorOnce() {
  const now = Date.now();
  if (now - __netErrShownAt < __NET_ERR_COOLDOWN_MS) return;
  __netErrShownAt = now;

  alert(
    "Falha de rede ao comunicar com a API. Verifique se o backend está rodando (127.0.0.1:8000)."
  );
}

function normalizeBlockedPayload(payload) {
  // backend pode mandar {detail:{...}} ou objeto direto
  if (payload?.detail && typeof payload.detail === "object") return payload.detail;
  return payload || {};
}

async function safeFetch(url, options = {}) {
  let res;

  try {
    res = await fetch(url, options);
  } catch (e) {
    console.error("Network error:", e);
    console.error("URL:", url);
    console.error("OPTIONS:", options);
    showNetErrorOnce();
    return null;
  }

  if (res.status === 401) {
    doLogout();
    clearBlockedOverlayStorage();
    window.location.href = "index.html";
    return null;
  }

  // 423 Locked => escritório bloqueado
  if (res.status === 423) {
    let payload = {};
    try {
      const data = await res.json();
      payload = normalizeBlockedPayload(data);
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
   DEADLINES SUMMARY
===================== */
async function loadDeadlinesSummary(status = null) {
  const data = status || (await checkSystemStatus());
  if (!data) return;

  const blocked = !!data.blocked;

  document.querySelectorAll(".card").forEach((card) => {
    card.classList.toggle("card-blocked", blocked);
  });
}

/* =====================
   DATE HELPERS
===================== */
function normalizeDate(dateStr) {
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
   LOAD DASHBOARD (SYNC REAL STATUS)
===================== */
async function loadDashboard() {
  const status = await checkSystemStatus();
  if (!status) return;

  console.log("SYSTEM STATUS:", status);

  // statusbar via dom.js
  setStatusBar(status);
  await loadDeadlinesSummary(status);

  if (status.blocked) {
    localStorage.setItem("juris_block_info", JSON.stringify(status));
    showBlockedOverlay(status);

    // carrega prazos (pra concluir/destravar)
    await loadDeadlines();
    return;
  }

  // não bloqueado: limpa overlay e storage
  clearBlockedOverlayStorage();
  hideBlockedOverlay();

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
    const doc = c.document ? ` — ${c.document}` : "";
    const email = c.email ? ` • ${c.email}` : "";
    const li = document.createElement("li");
    li.innerText = `${c.name}${doc}${email}`;
    list.appendChild(li);
  });

  return data;
}

async function createClient() {
  const nameEl = document.getElementById("client-name");
  const docEl = document.getElementById("client-doc");
  const emailEl = document.getElementById("client-email");

  const name = nameEl?.value?.trim() || "";
  const documentValue = docEl?.value?.trim() || "";
  const email = emailEl?.value?.trim() || "";

  if (!name) {
    alert("Preencha o nome do cliente.");
    return;
  }

  // CPF/CNPJ é recomendado, mas deixa opcional pra não travar import/demo
  // Se você quiser manter obrigatório, volta a validação antiga.
  const payload = {
    name,
    document: documentValue || null,
    email: email || null,
  };

  const res = await safeFetch(`${API}/clients/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });

  if (!res) return;

  if (!res.ok) {
    alert(await readError(res));
    return;
  }

  if (nameEl) nameEl.value = "";
  if (docEl) docEl.value = "";
  if (emailEl) emailEl.value = "";

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

    if (d.completed) li.classList.add("deadline-done");
    else if (isExpired(d.due_date)) li.classList.add("deadline-expired");
    else if (isToday(d.due_date)) li.classList.add("deadline-today");
    else if (isTomorrow(d.due_date)) li.classList.add("deadline-soon");

    const left = document.createElement("div");
    left.classList.add("deadline-left");

    const title = document.createElement("div");
    title.classList.add("deadline-title");

    const badge = document.createElement("span");
    badge.classList.add("badge");
    badge.innerText = d.is_critical ? "CRÍTICO" : "NORMAL";
    if (d.is_critical) badge.classList.add("badge-danger");
    else badge.classList.add("badge-muted");

    const main = document.createElement("span");
    main.innerText = d.description;

    title.appendChild(badge);
    title.appendChild(main);

    const meta = document.createElement("div");
    meta.classList.add("deadline-meta");
    meta.innerText = `Vence: ${d.due_date} • Resp: ${d.responsible}`;

    left.appendChild(title);
    left.appendChild(meta);

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

    const btnCal = document.createElement("button");
    btnCal.classList.add("btn-small");
    btnCal.innerText = "📅 Calendar";
    btnCal.onclick = async () => {
      const res = await safeFetch(`${API}/deadlines/${d.id}/sync_calendar`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({}),
      });
      if (!res) return;

      if (!res.ok) {
        alert(await readError(res));
        return;
      }

      const data = await res.json();
      const link = data.openLink || data.htmlLink;
      if (link) window.open(link, "_blank");
      else alert("Evento criado, mas sem link retornado.");
    };
    right.appendChild(btnCal);

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

  clearBlockedOverlayStorage();
  hideBlockedOverlay();
  await loadDashboard();
}

/* =====================
   SELECTS
===================== */
async function loadClientsSelect() {
  const data = await loadClients();
  if (!Array.isArray(data)) return;

  const select = document.getElementById("process-client-select");
  if (!select) return;

  select.innerHTML = '<option value="">Selecione o cliente</option>';

  data.forEach((client) => {
    const option = document.createElement("option");
    option.value = client.id;
    const email = client.email ? ` • ${client.email}` : "";
    option.innerText = `${client.name}${email}`;

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
  clearBlockedOverlayStorage();
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

/* =====================
   UNLOCK (LETRA B)
===================== */
async function unlockOffice() {
  const errEl = document.getElementById("unlock-error");
  if (errEl) {
    errEl.style.display = "none";
    errEl.innerText = "";
  }

  const password = (document.getElementById("unlock-password")?.value || "").trim();
  const reason = (document.getElementById("unlock-reason")?.value || "").trim();
  const minutesRaw = document.getElementById("unlock-minutes")?.value;
  const minutes = Number(minutesRaw || 30);

  if (!password) {
    if (errEl) {
      errEl.style.display = "block";
      errEl.innerText = "Digite a senha de desbloqueio.";
    } else {
      alert("Digite a senha de desbloqueio.");
    }
    return;
  }

  const res = await safeFetch(`${API}/system/unlock`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      password,
      reason: reason || "Manual unlock",
      minutes: Number.isFinite(minutes) ? minutes : 30,
    }),
  });

  if (!res) return;

  if (!res.ok) {
    const msg = await readError(res);

    if (errEl) {
      errEl.style.display = "block";
      errEl.innerText = msg || "Falha ao desbloquear.";
    } else {
      alert(msg || "Falha ao desbloquear.");
    }
    return;
  }

  try {
    const payload = await res.json();
    alert(`✅ Desbloqueado! Expira em: ${payload.expires_at || "em breve"}`);
  } catch {
    alert("✅ Desbloqueado!");
  }

  clearBlockedOverlayStorage();

  const passEl = document.getElementById("unlock-password");
  const reasonEl = document.getElementById("unlock-reason");
  if (passEl) passEl.value = "";
  if (reasonEl) reasonEl.value = "";

  hideBlockedOverlay();
  await loadDashboard();
}

window.unlockOffice = unlockOffice;

/* =====================
   GOOGLE DRIVE (demo)
===================== */
window.connectGoogleDrive = async function () {
  const res = await safeFetch(`${API}/google/drive/files?page_size=10`, {
    headers: authHeaders(),
  });
  if (!res) return;

  if (!res.ok) {
    alert(await readError(res));
    return;
  }

  const data = await res.json();
  const files = data.files || [];

  if (!files.length) {
    alert("Drive conectado ✅\nNenhum arquivo encontrado.");
    return;
  }

  console.log("DRIVE FILES:", files);

  const first = files[0];
  if (first.webViewLink) window.open(first.webViewLink, "_blank");

  alert(`Drive conectado ✅\nArquivos recebidos: ${files.length}\nAbrindo: ${first.name}`);
};

// frontend/dom.js

function $(id) {
  return document.getElementById(id);
}

function showBlockedOverlay(payload = []) {
  const overlay = $("lock-overlay");
  if (overlay) overlay.style.display = "flex";

  const list = $("lock-deadlines");
  if (list) {
    list.innerHTML = "";
    // Payload pode ser a lista de prazos direto
    const overdue = Array.isArray(payload) ? payload : (payload?.overdue_critical || []);
    if (overdue.length) {
      overdue.forEach((d) => {
        const li = document.createElement("li");
        li.innerText = `#${d.id} — ${d.description} (vence: ${d.due_date})`;
        list.appendChild(li);
      });
    }
  }
  localStorage.setItem("office_blocked", "true");
}

function hideBlockedOverlay() {
  const overlay = $("lock-overlay");
  if (overlay) overlay.style.display = "none";
  localStorage.removeItem("office_blocked");
}

function restoreBlockedOverlayFromStorage() {
  if (localStorage.getItem("office_blocked") === "true") {
    showBlockedOverlay();
  }
}

function setStatusBar(data) {
  const dot = $("status-dot");
  const title = $("status-title");
  const sub = $("status-sub");

  if (data.blocked) {
    if (dot) { dot.className = "badge"; dot.style.background = "var(--danger)"; }
    if (title) title.innerText = "Escritório Bloqueado";
    if (sub) sub.innerText = "Regularize os prazos críticos.";
  } else {
    if (dot) { dot.className = "badge badge-active"; dot.style.background = "var(--accent)"; }
    if (title) title.innerText = "Escritório Saudável";
    if (sub) sub.innerText = "Todos os prazos críticos estão em dia.";
  }

  if ($("st-open-total")) $("st-open-total").innerText = data.counts.open_total;
  if ($("st-overdue-total")) $("st-overdue-total").innerText = data.counts.overdue_total;
}

function initDomGuards() {
  // Inicialização de eventos globais se necessário
}

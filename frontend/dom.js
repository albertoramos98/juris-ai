// frontend/dom.js

function $(id) {
  return document.getElementById(id);
}

export function showBlockedOverlay(payload = {}) {
  const overlay = $("lock-overlay");
  if (overlay) overlay.style.display = "flex";

  const msg = $("lock-message");
  if (msg) {
    msg.innerText =
      payload?.message ||
      payload?.detail ||
      "Escritório bloqueado: existe prazo crítico vencido não concluído.";
  }

  const list = $("lock-deadlines");
  if (list) {
    list.innerHTML = "";
    const overdue = payload?.overdue_critical || payload?.overdueCritical || [];
    if (Array.isArray(overdue) && overdue.length) {
      overdue.forEach((d) => {
        const li = document.createElement("li");
        li.innerText = `#${d.id} — ${d.description} (vence: ${d.due_date || d.dueDate})`;
        list.appendChild(li);
      });
    }
  }
}

export function hideBlockedOverlay() {
  const overlay = $("lock-overlay");
  if (overlay) overlay.style.display = "none";
}

export function restoreBlockedOverlayFromStorage() {
  const saved = localStorage.getItem("juris_block_info");
  if (!saved) return false;

  try {
    const payload = JSON.parse(saved);
    showBlockedOverlay(payload);
    return true;
  } catch {
    return false;
  }
}

export function clearBlockedOverlayStorage() {
  localStorage.removeItem("juris_block_info");
}

/**
 * Statusbar do dashboard
 * Espera o shape do /system/status que você já usa:
 * { blocked: bool, counts: {...}, next_deadline?, overdue_critical? }
 */
export function setStatusBar(status) {
  const dot = $("status-dot");
  const title = $("status-title");
  const sub = $("status-sub");

  const openTotal = $("st-open-total");
  const openCritical = $("st-open-critical");
  const overdueTotal = $("st-overdue-total");
  const overdueCritical = $("st-overdue-critical");

  const counts = status?.counts || {};

  if (openTotal) openTotal.innerText = counts.open_total ?? 0;
  if (openCritical) openCritical.innerText = counts.open_critical ?? 0;
  if (overdueTotal) overdueTotal.innerText = counts.overdue_total ?? 0;
  if (overdueCritical) overdueCritical.innerText = counts.overdue_critical ?? 0;

  if (status?.blocked) {
    if (dot) dot.className = "dot dot-red";
    if (title) title.innerText = "Escritório BLOQUEADO";

    const first = status?.overdue_critical?.[0];
    if (sub) {
      sub.innerText = first
        ? `Motivo: prazo crítico vencido (#${first.id}) — ${first.due_date}`
        : "Motivo: prazo crítico vencido.";
    }
  } else {
    if (dot) dot.className = "dot dot-green";
    if (title) title.innerText = "Escritório operacional";

    const next = status?.next_deadline;
    if (sub) {
      sub.innerText = next
        ? `Próximo prazo: #${next.id} — ${next.due_date}${next.is_critical ? " (crítico)" : ""}`
        : "Sem prazos pendentes.";
    }
  }
}

/**
 * Inicializa listeners globais
 * - ao receber 423 no http.js, ele dá dispatch "juris:blocked"
 */
export function initDomGuards() {
  window.addEventListener("juris:blocked", (ev) => {
    const payload = ev?.detail || {};
    showBlockedOverlay(payload);
  });
}

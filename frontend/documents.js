// Removidos imports para compatibilidade global

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

async function loadDocuments() {
  const tbody = document.getElementById("docsTbody");
  const filter = document.getElementById("filterCategory").value;
  
  try {
    const res = await fetch(`${API}/processes/all${filter ? '?category=' + filter : ''}`, {
      headers: authHeaders()
    });
    
    if (res.status === 401) { window.location.href = "index.html"; return; }
    
    const data = await res.json();
    tbody.innerHTML = "";
    
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 40px;">Nenhum documento encontrado.</td></tr>';
      return;
    }

    data.forEach(doc => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <div style="display:flex; align-items:center; gap:12px;">
            <i class="fas fa-file-pdf" style="color:var(--danger); font-size:18px;"></i>
            <div>
              <div style="font-weight:600;">${escapeHtml(doc.name)}</div>
              <div style="font-size:12px; color:var(--text-secondary);">ID: ${doc.id} | Processo: ${doc.process_id}</div>
            </div>
          </div>
        </td>
        <td><span class="badge badge-active">${escapeHtml(doc.category)}</span></td>
        <td style="color:var(--text-secondary); font-size:13px;">${new Date(doc.created_at).toLocaleDateString()}</td>
        <td>
          <a href="${doc.drive_web_view_link}" target="_blank" class="secondary btn-small">
            <i class="fas fa-external-link-alt"></i> Drive
          </a>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error(e);
    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color:var(--danger);">Erro ao carregar documentos.</td></tr>';
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadDocuments();
  document.getElementById("filterCategory")?.addEventListener("change", loadDocuments);
  document.getElementById("btnRefresh")?.addEventListener("click", loadDocuments);
});

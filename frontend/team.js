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

async function loadTeam() {
  const tbody = document.getElementById("teamTbody");
  try {
    const res = await fetch(`${API}/users/me/team`, { headers: authHeaders() });
    if (res.status === 401) { window.location.href = "index.html"; return; }
    
    const data = await res.json();
    tbody.innerHTML = "";
    
    data.forEach(user => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${escapeHtml(user.email.split('@')[0])}</strong></td>
        <td>${escapeHtml(user.email)}</td>
        <td><span class="badge">${user.is_owner ? 'Owner' : 'Membro'}</span></td>
        <td><span class="badge badge-active">${user.is_active ? 'Ativo' : 'Inativo'}</span></td>
        <td>
          <button class="danger btn-small" onclick="deleteUser(${user.id})">Remover</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="5">Erro ao carregar equipe.</td></tr>';
  }
}

async function createUser() {
    const name = document.getElementById("newUserName").value;
    const email = document.getElementById("newUserEmail").value;
    const pass = document.getElementById("newUserPass").value;
    const role = document.getElementById("newUserRole").value;

    if(!email || !pass) return alert("Preencha email e senha.");

    try {
        const res = await fetch(`${API}/users`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ email, password: pass, is_owner: role === 'owner' })
        });
        if(!res.ok) throw new Error("Erro ao criar usuário.");
        alert("Membro adicionado!");
        loadTeam();
    } catch(e) { alert(e.message); }
}

async function deleteUser(userId) {
    if (!confirm("Tem certeza que deseja remover este membro da equipe?")) return;

    try {
        const res = await fetch(`${API}/users/${userId}/deactivate`, {
            method: 'PATCH',
            headers: authHeaders()
        });
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Erro ao remover usuário.");
        }
        alert("Membro removido!");
        loadTeam();
    } catch(e) { alert(e.message); }
}

document.addEventListener("DOMContentLoaded", () => {
  loadTeam();
  document.getElementById("btnCreateUser")?.addEventListener("click", createUser);
  document.getElementById("btnRefresh")?.addEventListener("click", loadTeam);
});

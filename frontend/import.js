// Removidos imports para compatibilidade global

function getToken(){ return localStorage.getItem("token"); }
function authHeaders(extra = {}){
  const t = getToken();
  return { ...(t ? { Authorization:`Bearer ${t}` } : {}), ...extra };
}

async function uploadCsv() {
    const fileInput = document.getElementById("csvFile");
    const status = document.getElementById("status");
    if(!fileInput.files[0]) return alert("Selecione um arquivo CSV.");

    status.textContent = "Processando importação...";
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const res = await fetch(`${API}/imports/processes-csv`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${getToken()}` },
            body: formData
        });
        const data = await res.json();
        if(res.ok) {
            status.textContent = `Sucesso! ${data.imported_count} processos importados.`;
            status.style.color = "var(--accent)";
        } else {
            throw new Error(data.detail || "Erro na importação.");
        }
    } catch(e) {
        status.textContent = e.message;
        status.style.color = "var(--danger)";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btnUpload")?.addEventListener("click", uploadCsv);
    document.getElementById("btnDownloadTemplate")?.addEventListener("click", () => {
        window.open(`${API}/imports/template-csv`);
    });
});

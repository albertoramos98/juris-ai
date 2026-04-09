// Removidos imports

let __netErrShownAt = 0;
const __NET_ERR_COOLDOWN_MS = 10000;

function showNetErrorOnce() {
  const now = Date.now();
  if (now - __netErrShownAt < __NET_ERR_COOLDOWN_MS) return;
  __netErrShownAt = now;
  alert("Falha de rede ao comunicar com a API.");
}

function buildUrl(path) {
  if (/^https?:\/\//i.test(path)) return path;
  const base = typeof API !== 'undefined' ? API : "http://127.0.0.1:8000";
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalized}`;
}

async function apiGet(path) {
  const token = localStorage.getItem("token");
  const res = await fetch(buildUrl(path), {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (res.status === 401) { window.location.href = "index.html"; return; }
  return res.json();
}

async function apiPost(path, body) {
  const token = localStorage.getItem("token");
  const res = await fetch(buildUrl(path), {
    method: 'POST',
    headers: { 
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });
  return res.json();
}

// Expõe globalmente
window.apiGet = apiGet;
window.apiPost = apiPost;

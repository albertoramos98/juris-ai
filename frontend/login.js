// Removido import para usar global do config.js

const emailEl = document.getElementById("email");
const passEl = document.getElementById("password");
const errEl = document.getElementById("errorMsg"); // Ajustado para novo design
const btnLogin = document.getElementById("btnSubmit"); // Ajustado para novo design
const btnGoogle = document.getElementById("btnGoogle"); // Ajustado para novo design

function showError(msg){
  if (!errEl) return alert(msg);
  errEl.style.display = "block";
  errEl.innerText = msg || "Erro ao fazer login.";
}

function clearError(){
  if (!errEl) return;
  errEl.style.display = "none";
  errEl.innerText = "";
}

/* =========================
   LOGIN EMAIL/SENHA
========================= */
async function login(e){
  if (e) e.preventDefault();
  clearError();

  const email = (emailEl?.value || "").trim();
  const password = (passEl?.value || "").trim();

  if (!email || !password){
    return showError("Preencha email e senha.");
  }

  let res;
  try{
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type":"application/x-www-form-urlencoded" },
      body: form.toString()
    });
  }catch(err){
    return showError("Erro de rede com o servidor. Verifique se o backend está rodando.");
  }

  if (!res.ok){
    let msg = `Falha no login (${res.status}).`;
    try{
      const data = await res.json();
      msg = data.detail || msg;
    }catch{ }
    return showError(msg);
  }

  const data = await res.json();
  const token = data.access_token || data.token;
  
  if (!token) return showError("Login OK, mas token não veio na resposta.");

  localStorage.setItem("token", token);
  window.location.href = "dashboard.html";
}

/* =========================
   LOGIN GOOGLE
========================= */
function loginGoogle(){
  window.location.href = `${API}/auth/google/login`;
}

/* =========================
   CAPTURA TOKEN DO GOOGLE
========================= */
(function captureTokenFromUrl(){
  const url = new URL(window.location.href);
  const token = url.searchParams.get("token");
  if (!token) return;

  localStorage.setItem("token", token);

  url.searchParams.delete("token");
  window.history.replaceState({}, "", url.toString());

  window.location.href = "dashboard.html";
})();

/* =========================
   BINDINGS
========================= */
// No novo design usamos o form.submit
document.getElementById("authForm")?.addEventListener("submit", login);
btnGoogle?.addEventListener("click", loginGoogle);

passEl?.addEventListener("keydown", (e)=>{
  if (e.key === "Enter") login();
});

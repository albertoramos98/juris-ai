// Removido import para usar global do config.js

async function login(email, password) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body
  });

  if (!res.ok) throw new Error("Credenciais inválidas");

  const data = await res.json();
  localStorage.setItem("token", data.access_token);
  return data;
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "index.html";
}

// Expõe globalmente
window.logout = logout;

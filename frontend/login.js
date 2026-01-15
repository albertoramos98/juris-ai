import { login as doLogin } from "./auth.js";

window.login = async function () {
  const email = document.getElementById("email")?.value?.trim();
  const password = document.getElementById("password")?.value || "";

  if (!email || !password) {
    alert("Preencha email e senha.");
    return;
  }

  try {
    await doLogin(email, password);
    window.location.href = "dashboard.html";
  } catch (e) {
    alert("Erro no login: credenciais inválidas");
    console.error(e);
  }
};

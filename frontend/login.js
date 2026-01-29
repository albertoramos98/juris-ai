import { API } from "./config.js";

// expõe pro onclick do HTML
window.loginGoogle = function loginGoogle() {
  window.location.href = `${API}/auth/google/login`;
};

// se voltou do backend com ?token=...
(function captureTokenFromUrl() {
  const url = new URL(window.location.href);
  const token = url.searchParams.get("token");
  if (!token) return;

  localStorage.setItem("token", token);

  // limpa token da URL
  url.searchParams.delete("token");
  window.history.replaceState({}, "", url.toString());

  // segue fluxo normal
  window.location.href = "dashboard.html";
})();

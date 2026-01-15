import { API_BASE_URL } from "./config.js";
import { getToken, clearToken } from "./storage.js";

export async function apiFetch(path, options = {}) {
  const token = getToken();

  const headers = options.headers || {};
  if (token) headers.Authorization = `Bearer ${token}`;

  let body = options.body;
  if (body && typeof body === "object" && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method || "GET",
    headers,
    body,
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = "index.html";
    return;
  }

  if (res.status === 423) {
    const data = await res.json();
    localStorage.setItem("juris_block_info", JSON.stringify(data.detail || data));
    window.location.href = "dashboard.html";
    return;
  }

  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}
    
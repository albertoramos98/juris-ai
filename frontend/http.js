// frontend/http.js
import { API_BASE_URL } from "./config.js";
import { getToken, clearToken } from "./storage.js";

/**
 * Config
 */
let __netErrShownAt = 0;
const __NET_ERR_COOLDOWN_MS = 10000;

function showNetErrorOnce() {
  const now = Date.now();
  if (now - __netErrShownAt < __NET_ERR_COOLDOWN_MS) return;
  __netErrShownAt = now;

  alert(
    "Falha de rede ao comunicar com a API.\n" +
      "Verifique se o backend está rodando em http://127.0.0.1:8000"
  );
}

function normalizePath(path) {
  // aceita "/x" ou "x"
  if (!path) return "/";
  return path.startsWith("/") ? path : `/${path}`;
}

function buildUrl(path) {
  // se já vier URL completa, respeita
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE_URL}${normalizePath(path)}`;
}

function isPlainObject(x) {
  return Object.prototype.toString.call(x) === "[object Object]";
}

function dispatchBlocked(payload) {
  try {
    window.dispatchEvent(new CustomEvent("juris:blocked", { detail: payload }));
  } catch {
    // nada
  }
}

/**
 * Lê um erro de forma humana
 */
export async function readError(res) {
  try {
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const data = await res.json();
      return data?.detail || JSON.stringify(data);
    }
    return await res.text();
  } catch {
    return "Erro desconhecido";
  }
}

/**
 * Fetch base (retorna Response).
 * - injeta Authorization Bearer
 * - se body for objeto, envia JSON automaticamente (exceto FormData/Blob/etc)
 * - trata 401/423
 * - trata falha de rede (cooldown)
 */
export async function apiFetch(path, options = {}) {
  const url = buildUrl(path);
  const token = getToken();

  // Headers
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);

  // Body handling
  let body = options.body;

  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  const isBlob = typeof Blob !== "undefined" && body instanceof Blob;
  const isArrayBuffer = typeof ArrayBuffer !== "undefined" && body instanceof ArrayBuffer;

  // Se for "objeto puro", serializa JSON (mas não mexe em FormData/Blob/ArrayBuffer)
  if (body != null && isPlainObject(body) && !isFormData && !isBlob && !isArrayBuffer) {
    if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    body = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(url, {
      method: options.method || "GET",
      headers,
      body,
      credentials: options.credentials || "omit",
    });
  } catch (e) {
    console.error("Network error:", e);
    console.error("URL:", url);
    console.error("OPTIONS:", options);
    showNetErrorOnce();
    return null;
  }

  // 401 => desloga e redireciona
  if (res.status === 401) {
    clearToken();
    localStorage.removeItem("juris_block_info");
    window.location.href = "index.html";
    return null;
  }

  // 423 => salva payload e dispara evento pro dom.js cuidar do overlay
  if (res.status === 423) {
    let payload = {};
    try {
      const data = await res.json();
      payload = data?.detail && typeof data.detail === "object" ? data.detail : data;
    } catch {
      payload = { message: "Office blocked." };
    }

    localStorage.setItem("juris_block_info", JSON.stringify(payload));
    dispatchBlocked(payload);
    return null;
  }

  return res;
}

/**
 * Helpers (usam apiFetch)
 */
export async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options);
  if (!res) return null;
  if (!res.ok) {
    const msg = await readError(res);
    throw new Error(msg);
  }
  return await res.json();
}

export async function apiText(path, options = {}) {
  const res = await apiFetch(path, options);
  if (!res) return null;
  if (!res.ok) {
    const msg = await readError(res);
    throw new Error(msg);
  }
  return await res.text();
}

export async function apiBlob(path, options = {}) {
  const res = await apiFetch(path, options);
  if (!res) return null;
  if (!res.ok) {
    const msg = await readError(res);
    throw new Error(msg);
  }
  return await res.blob();
}

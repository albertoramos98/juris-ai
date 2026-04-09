// Configuração dinâmica da API
// Em desenvolvimento local, usa o localhost. Em produção, você pode definir a URL fixa ou deixar dinâmico.
const API = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
    ? "http://127.0.0.1:8000"
    : window.location.origin;

const API_BASE_URL = API;

// Configurações do Supabase (para uso futuro com Storage/Auth no frontend)
const SUPABASE_URL = "https://nyponijxdtijgktouvns.supabase.co";
const SUPABASE_KEY = "sb_publishable_9gTuIzzwQ-07x1ecfLjZQg_z20PeYd_";

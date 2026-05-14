// In production (Cloud Run): VITE_API_BASE_URL="" → same-origin calls (/predict, /chat, etc.)
// In dev mode: fall back to the local FastAPI backend directly.
const API_BASE = import.meta.env.VITE_API_BASE_URL !== undefined
  ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
  : (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '');

async function fetchWithRetry(url, options = {}, retries = 2, delayMs = 1500) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000);
    const response = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
      throw new Error(body.detail || `HTTP ${response.status}`);
    }

    return response;
  } catch (error) {
    if (error.name === 'AbortError') {
      if (retries > 0) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
        return fetchWithRetry(url, options, retries - 1, delayMs);
      }
      throw new Error('The server took too long to respond. Please try again.');
    }

    if (retries > 0 && (error.message === 'Failed to fetch' || error.message === 'Request failed')) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      return fetchWithRetry(url, options, retries - 1, delayMs);
    }

    if (error.message === 'Failed to fetch') {
      throw new Error('Could not reach the backend API. Check that the deployment is live and the API route is available.');
    }

    throw error;
  }
}

export async function predictDisease(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);

  const response = await fetchWithRetry(`${API_BASE}/predict`, {
    method: 'POST',
    body: formData,
  });

  return response.json();
}

export async function sendChatMessage(message, lang = 'en', weather = null, featureContext = null) {
  const response = await fetchWithRetry(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, lang, weather, feature_context: featureContext }),
  });

  return response.json();
}

export async function getFarmZones() {
  const response = await fetchWithRetry(`${API_BASE}/zones`);
  return response.json();
}

export async function getProfitOptions() {
  const response = await fetchWithRetry(`${API_BASE}/profit/crops`);
  return response.json();
}

export async function calculateProfit(payload) {
  const response = await fetchWithRetry(`${API_BASE}/profit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function getWeather(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value));
    }
  });

  const response = await fetchWithRetry(
    `${API_BASE}/weather${search.toString() ? `?${search.toString()}` : ''}`,
  );

  return response.json();
}

export async function analyzeSoilHealth(payload) {
  const response = await fetchWithRetry(`${API_BASE}/soil-health`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  return response.json();
}

export async function analyzeSoilChatGPT(payload) {
  const response = await fetchWithRetry(`${API_BASE}/analyze-soil`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  return response.json();
}

// ── Field Journal ──────────────────────────────────────────────────

export async function getJournalEntries() {
  const response = await fetchWithRetry(`${API_BASE}/journal`);
  return response.json();
}

export async function addJournalEntry(entry) {
  const response = await fetchWithRetry(`${API_BASE}/journal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  });
  return response.json();
}

export async function deleteJournalEntry(id) {
  await fetchWithRetry(`${API_BASE}/journal/${id}`, { method: 'DELETE' });
}

// ── Farm Task Manager ──────────────────────────────────────────────

export async function getTasks() {
  const response = await fetchWithRetry(`${API_BASE}/tasks`);
  return response.json();
}

export async function addTask(task) {
  const response = await fetchWithRetry(`${API_BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  });
  return response.json();
}

export async function updateTaskStatus(id, status) {
  const response = await fetchWithRetry(`${API_BASE}/tasks/${id}/status?status=${status}`, {
    method: 'PATCH',
  });
  return response.json();
}

export async function deleteTask(id) {
  await fetchWithRetry(`${API_BASE}/tasks/${id}`, { method: 'DELETE' });
}

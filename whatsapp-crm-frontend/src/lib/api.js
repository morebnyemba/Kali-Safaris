// Filename: c:\Users\Administrator\Desktop\HAVANO\whatsapp-crm-frontend\src\lib\api.js
import axios from 'axios';
import { toast } from 'sonner';
import { API_BASE_URL } from '@/config/appConfig';

export { API_BASE_URL };

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue = [];

const normalizeToken = (token) => {
  if (typeof token !== 'string') return '';

  let normalized = token.trim();
  for (let i = 0; i < 3; i += 1) {
    if (!normalized) break;

    if (
      (normalized.startsWith('"') && normalized.endsWith('"'))
      || (normalized.startsWith("'") && normalized.endsWith("'"))
    ) {
      normalized = normalized.slice(1, -1).trim();
      continue;
    }

    try {
      const parsed = JSON.parse(normalized);
      if (typeof parsed === 'string') {
        normalized = parsed.trim();
        continue;
      }
    } catch {
      // Keep as-is when not valid JSON.
    }

    normalized = normalized.replace(/\\"/g, '"').trim();
    break;
  }

  return normalized.replace(/^"+|"+$/g, '').replace(/^'+|'+$/g, '').trim();
};

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

const refreshToken = async () => {
  try {
    const refreshToken = normalizeToken(localStorage.getItem('refreshToken'));
    if (!refreshToken) throw new Error("Session expired. Please log in again.");

    const response = await axios.post(`${API_BASE_URL}/crm-api/auth/token/refresh/`, {
      refresh: refreshToken,
    });

    const { access, refresh: newRefreshToken } = response.data;
    localStorage.setItem('accessToken', normalizeToken(access));
    if (newRefreshToken) {
      localStorage.setItem('refreshToken', normalizeToken(newRefreshToken));
    }
    return normalizeToken(access);
  } catch {

    // Instead of forcing a redirect, dispatch an event that the AuthProvider can listen to.
    // This decouples the API layer from the UI/routing layer.
    window.dispatchEvent(new Event('auth-error'));
    return Promise.reject(new Error("Session expired. Please log in again."));
  }
};

apiClient.interceptors.request.use((config) => {
  const token = normalizeToken(localStorage.getItem('accessToken'));
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Do not attempt to refresh token for login or refresh endpoints
    if (originalRequest.url.endsWith('/token/') || originalRequest.url.endsWith('/token/refresh/')) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newAccessToken = await refreshToken();
        apiClient.defaults.headers.common['Authorization'] = 'Bearer ' + newAccessToken;
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        processQueue(null, newAccessToken);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    const message =
      error.response?.data?.detail ||
      (typeof error.response?.data === 'object' && error.response?.data !== null
        ? Object.entries(error.response.data)
            .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${Array.isArray(v) ? v.join(', ') : v}`)
            .join('; ')
        : error.message) ||
      'An unknown error occurred.';

    if (error.response?.status !== 401 && !originalRequest.suppressErrorToast) {
      toast.error(`API Error: ${message}`);
    }

    return Promise.reject(error);
  }
);

// --- API Service Definitions ---

// --- Dashboard / Analytics Stats API ---
export const dashboardApi = {
  getSummary: (params) => apiClient.get('/crm-api/stats/summary/', { params }),
  getBookingStats: (params) => apiClient.get('/crm-api/stats/bookings/', { params }),
  getMessageVolume: (params) => apiClient.get('/crm-api/stats/messages/', { params }),
  getEngagement: (params) => apiClient.get('/crm-api/stats/engagement/', { params }),
};

// --- Contacts API ---
export const contactsApi = {
  list: (params) => apiClient.get('/crm-api/conversations/contacts/', { params }),
  retrieve: (id) => apiClient.get(`/crm-api/conversations/contacts/${id}/`),
  patch: (id, data) => apiClient.patch(`/crm-api/conversations/contacts/${id}/`, data),
  listMessages: (contactId, params) => apiClient.get(`/crm-api/conversations/contacts/${contactId}/messages/`, { params }),
  markRead: (contactId) => apiClient.post(`/crm-api/conversations/contacts/${contactId}/mark-read/`),
};

// --- Customer Profile API ---
export const profilesApi = {
  // GET creates the profile on first access (CustomerProfile pk == contact id).
  retrieve: (id) => apiClient.get(`/crm-api/customer-data/profiles/${id}/`),
  patch: (id, data) => apiClient.patch(`/crm-api/customer-data/profiles/${id}/`, data),
};

// --- Tours (catalogue) ---
export const toursApi = {
  list: () => apiClient.get('/crm-api/tours/'),
};

// --- Tour Inquiries API ---
export const inquiriesApi = {
  list: (params) => apiClient.get('/crm-api/customer-data/inquiries/', { params }),
  create: (data) => apiClient.post('/crm-api/customer-data/inquiries/', data),
  update: (id, data) => apiClient.patch(`/crm-api/customer-data/inquiries/${id}/`, data),
  delete: (id) => apiClient.delete(`/crm-api/customer-data/inquiries/${id}/`),
};

// --- Flows API ---
// Flow pages show their own (field-level) errors, so the global toast is muted.
const FLOW_BASE = '/crm-api/flows/flows/';
const quiet = { suppressErrorToast: true };
export const flowsApi = {
  list: (params) => apiClient.get(FLOW_BASE, { params, ...quiet }),
  retrieve: (id) => apiClient.get(`${FLOW_BASE}${id}/`, quiet),
  create: (data) => apiClient.post(FLOW_BASE, data, quiet),
  patch: (id, data) => apiClient.patch(`${FLOW_BASE}${id}/`, data, quiet),
  delete: (id) => apiClient.delete(`${FLOW_BASE}${id}/`, quiet),

  listSteps: (flowId) => apiClient.get(`${FLOW_BASE}${flowId}/steps/`, quiet),
  createStep: (flowId, data) => apiClient.post(`${FLOW_BASE}${flowId}/steps/`, data, quiet),
  patchStep: (flowId, stepId, data) => apiClient.patch(`${FLOW_BASE}${flowId}/steps/${stepId}/`, data, quiet),
  deleteStep: (flowId, stepId) => apiClient.delete(`${FLOW_BASE}${flowId}/steps/${stepId}/`, quiet),

  listTransitions: (flowId, stepId) => apiClient.get(`${FLOW_BASE}${flowId}/steps/${stepId}/transitions/`, quiet),
  createTransition: (flowId, stepId, data) => apiClient.post(`${FLOW_BASE}${flowId}/steps/${stepId}/transitions/`, data, quiet),
  updateTransition: (flowId, stepId, transitionId, data) => apiClient.patch(`${FLOW_BASE}${flowId}/steps/${stepId}/transitions/${transitionId}/`, data, quiet),
  deleteTransition: (flowId, stepId, transitionId) => apiClient.delete(`${FLOW_BASE}${flowId}/steps/${stepId}/transitions/${transitionId}/`, quiet),
};

// --- Meta API Configs ---
const META_BASE = '/crm-api/meta/api/';
export const metaApi = {
  getConfigs: () => apiClient.get(`${META_BASE}configs/`, { params: { page_size: 100 }, suppressErrorToast: true }),
  createConfig: (data) => apiClient.post(`${META_BASE}configs/`, data, { suppressErrorToast: true }),
  patchConfig: (id, data) => apiClient.patch(`${META_BASE}configs/${id}/`, data, { suppressErrorToast: true }),
  deleteConfig: (id) => apiClient.delete(`${META_BASE}configs/${id}/`, { suppressErrorToast: true }),
  setActive: (id) => apiClient.post(`${META_BASE}configs/${id}/set_active/`, null, { suppressErrorToast: true }),
  latestWebhookEvents: (count = 15) => apiClient.get(`${META_BASE}webhook-logs/latest/`, { params: { count }, suppressErrorToast: true }),
};

// --- Media Assets API ---
const MEDIA_BASE = '/crm-api/media/assets/';
export const mediaAssetsApi = {
  list: (params) => apiClient.get(MEDIA_BASE, { params }),
  // FormData upload: override the client's JSON default or axios would JSON-encode it.
  create: (formData) => apiClient.post(MEDIA_BASE, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, data) => apiClient.patch(`${MEDIA_BASE}${id}/`, data),
  delete: (id) => apiClient.delete(`${MEDIA_BASE}${id}/`),
  sync: (id) => apiClient.post(`${MEDIA_BASE}${id}/sync-with-whatsapp/`),
};

// Backward-compatible apiCall function.
// It's recommended to migrate away from this and use the specific service APIs above.
/**
 * Makes an API call using the configured axios client. This function is provided
 * for backward compatibility with older parts of the application that used a
 * fetch-based `apiCall`.
 * @param {string} endpoint The API endpoint to call.
 * @param {object|string} [arg2] Either an options object `{ method, body, params }` or the HTTP method string.
 * @param {object} [arg3] The request body if `arg2` is the method string.
 * @returns {Promise<any>} The response data.
 */
export async function apiCall(endpoint, arg2, arg3) {
  let method = 'GET';
  let body = null;
  let params = null;

  if (typeof arg2 === 'object' && arg2 !== null) {
    // Signature: apiCall(endpoint, { method, body, params })
    method = arg2.method || 'GET';
    body = arg2.body || null;
    params = arg2.params || null;
  } else if (typeof arg2 === 'string') {
    // Signature: apiCall(endpoint, method, body)
    method = arg2;
    body = arg3 || null;
  }

  const response = await apiClient({
    url: endpoint,
    method,
    data: body,
    params,
  });
  // Axios wraps the response in a `data` property.
  // Old apiCall returned the data directly.
  return response.data;
}

export default apiClient;

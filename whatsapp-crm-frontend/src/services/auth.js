import { jwtDecode } from 'jwt-decode';
import apiClient from '@/lib/api'; // Use the central axios client

const ACCESS_TOKEN_KEY = 'accessToken';
const REFRESH_TOKEN_KEY = 'refreshToken';

export const normalizeToken = (token) => {
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

export const authService = {
  // Token Management
  storeTokens(accessToken, refreshToken) {
    const cleanedAccessToken = normalizeToken(accessToken);
    localStorage.setItem(ACCESS_TOKEN_KEY, cleanedAccessToken);
    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, normalizeToken(refreshToken));
    }
  },
  clearTokens() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem('user'); // Also clear user from jotai/storage
  },
  getAccessToken: () => normalizeToken(localStorage.getItem(ACCESS_TOKEN_KEY)),
  getRefreshToken: () => normalizeToken(localStorage.getItem(REFRESH_TOKEN_KEY)),

  // API Calls
  async login(username, password) {
    try {
      // Use the central apiClient. The interceptor is now safe for this call.
      const response = await apiClient.post('/crm-api/auth/token/', { username, password });
      const { access, refresh } = response.data;
      this.storeTokens(access, refresh);
      const user = jwtDecode(normalizeToken(access));
      return { success: true, user };
    } catch (error) {
      // The interceptor in apiClient will toast errors, but we still need to return failure.
      const errorMessage = error.response?.data?.detail || 'Login failed. Please check credentials.';
      return { success: false, error: errorMessage };
    }
  },

  async logout(notifyBackend = true) {
    const refreshToken = this.getRefreshToken();
    if (notifyBackend && refreshToken) {
      try {
        // Use apiClient for consistency.
        // Suppress the generic error toast since we handle this failure case gracefully.
        await apiClient.post('/crm-api/auth/token/blacklist/', { refresh: refreshToken }, { suppressErrorToast: true });
      } catch (error) {
        if (error.response?.status === 404) {
          // This is a common case if the backend URL isn't configured. Log as info, not a warning.
          console.info("Token blacklist endpoint not found on server. Skipping server-side logout. This is safe, but the endpoint should be configured for enhanced security.");
        } else {
          // For other errors (e.g., 401 if refresh token is already invalid), log a warning. This is expected.
          console.warn("Could not blacklist token on server. This is expected if the session has already expired.", error);
        }
      }
    }
    this.clearTokens();
  },

  // refreshTokenInternal is no longer needed here.
  // The interceptor in `lib/api.js` handles all token refreshing automatically.
};
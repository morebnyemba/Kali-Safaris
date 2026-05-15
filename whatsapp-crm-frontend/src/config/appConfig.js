const ENV_API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").trim();
const DEFAULT_API_BASE_URL = "https://backend.kalaisafaris.com";

function normalizeBaseUrl(url) {
  return url.replace(/\/+$/, "");
}

export const API_BASE_URL = normalizeBaseUrl(ENV_API_BASE_URL || DEFAULT_API_BASE_URL);
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

export const BRAND_ATTRIBUTION = {
  text: "Powered by Slyker Tech Web Services",
  url: "https://slykertech.net"
};

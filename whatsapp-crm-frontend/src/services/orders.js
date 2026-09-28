import apiClient from '@/lib/api';

// Server-side exporters, keyed by manifest kind.
const MANIFEST_ENDPOINTS = {
  park: { path: '/crm-api/customer-data/export/manifest/', filePrefix: 'booking_manifest' },
  summary: { path: '/crm-api/customer-data/export/passenger-summary/', filePrefix: 'passenger_summary' },
};

// Blob error bodies can't be read by the global error interceptor, so manifest
// requests opt out of its toast and surface the backend's JSON message here.
const readBlobError = async (error) => {
  const data = error?.response?.data;
  if (data instanceof Blob) {
    try {
      const parsed = JSON.parse(await data.text());
      return parsed.error || parsed.detail || 'Export failed.';
    } catch {
      return `Export failed (HTTP ${error.response.status}).`;
    }
  }
  return error?.message || 'Export failed.';
};

export const ordersApi = {
  list: (params) => apiClient.get('/crm-api/customer-data/bookings/', { params }),
  create: (data) => apiClient.post('/crm-api/customer-data/bookings/', data),
  update: (id, data) => apiClient.put(`/crm-api/customer-data/bookings/${id}/`, data),
  delete: (id) => apiClient.delete(`/crm-api/customer-data/bookings/${id}/`),

  /**
   * Downloads a passenger manifest for a tour date.
   * @param {'park'|'summary'} kind  park = ZimParks entry manifest, summary = crew headcount
   * @param {string} date            YYYY-MM-DD
   * @param {'pdf'|'excel'} format
   */
  downloadManifest: async (kind, date, format = 'pdf') => {
    const endpoint = MANIFEST_ENDPOINTS[kind];
    if (!endpoint) throw new Error(`Unknown manifest type: ${kind}`);

    let response;
    try {
      response = await apiClient.get(endpoint.path, {
        params: { date, format },
        responseType: 'blob',
        suppressErrorToast: true,
      });
    } catch (error) {
      throw new Error(await readBlobError(error));
    }

    const extension = format === 'excel' ? 'xlsx' : 'pdf';
    const url = URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${endpoint.filePrefix}_${date}.${extension}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    // Give the browser a tick to start the download before revoking.
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};

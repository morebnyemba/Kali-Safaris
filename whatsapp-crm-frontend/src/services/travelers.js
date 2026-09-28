import apiClient from '@/lib/api';

const BASE = '/crm-api/customer-data/travelers/';

// Multipart only when a file is attached; JSON otherwise.
const toBody = (data) => {
  if (!(data.id_document instanceof File)) {
    const { id_document: _omit, ...rest } = data;
    return rest;
  }
  const form = new FormData();
  Object.entries(data).forEach(([key, value]) => {
    if (value !== undefined && value !== null) form.append(key, value);
  });
  return form;
};

// DRF returns {field: [msgs]} or {non_field_errors: [msgs]}; flatten for display.
export const travelerErrorMessage = (err) => {
  const data = err?.response?.data;
  if (data && typeof data === 'object') {
    return Object.values(data).flat().join(' ');
  }
  return err?.message || 'Could not save passenger.';
};

// Validation errors are shown inline in the editor, so skip the global toast.
// The shared client defaults to JSON, which would make axios JSON-encode a
// FormData body (dropping the file); declare multipart so it's sent as-is.
const requestConfig = (body) => ({
  suppressErrorToast: true,
  ...(body instanceof FormData && { headers: { 'Content-Type': 'multipart/form-data' } }),
});

export const travelersApi = {
  list: (bookingId) => apiClient.get(BASE, { params: { booking: bookingId } }),
  create: (data) => {
    const body = toBody(data);
    return apiClient.post(BASE, body, requestConfig(body));
  },
  update: (id, data) => {
    const body = toBody(data);
    return apiClient.patch(`${BASE}${id}/`, body, requestConfig(body));
  },
  delete: (id) => apiClient.delete(`${BASE}${id}/`),

  /** Opens the ID/passport copy in a new tab via an authenticated request. */
  openIdDocument: async (id) => {
    // Open the tab synchronously (popup blockers), then point it at the blob.
    const tab = window.open('', '_blank');
    try {
      const response = await apiClient.get(`${BASE}${id}/id-document/`, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      if (tab) {
        tab.location.href = url;
      } else {
        window.location.assign(url);
      }
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (error) {
      tab?.close();
      throw error;
    }
  },
};

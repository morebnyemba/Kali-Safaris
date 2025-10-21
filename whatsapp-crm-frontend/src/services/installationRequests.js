import apiClient from '@/lib/api';

export const installationRequestsApi = {
  list: (params) => apiClient.get('/crm-api/customer-data/installation-requests/', { params }),
  create: (data) => apiClient.post('/crm-api/customer-data/installation-requests/', data),
  update: (id, data) => apiClient.put(`/crm-api/customer-data/installation-requests/${id}/`, data),
  delete: (id) => apiClient.delete(`/crm-api/customer-data/installation-requests/${id}/`),
};

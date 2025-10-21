import apiClient from '@/lib/api';

export const ordersApi = {
  list: (params) => apiClient.get('/crm-api/customer-data/orders/', { params }),
  create: (data) => apiClient.post('/crm-api/customer-data/orders/', data),
  update: (id, data) => apiClient.put(`/crm-api/customer-data/orders/${id}/`, data),
  delete: (id) => apiClient.delete(`/crm-api/customer-data/orders/${id}/`),
};

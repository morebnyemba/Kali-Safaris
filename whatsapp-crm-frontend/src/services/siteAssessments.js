import apiClient from '@/lib/api';

export const siteAssessmentsApi = {
  list: (params) => apiClient.get('/crm-api/customer-data/tour-inquiries/', { params }),
  create: (data) => apiClient.post('/crm-api/customer-data/tour-inquiries/', data),
  update: (id, data) => apiClient.put(`/crm-api/customer-data/tour-inquiries/${id}/`, data),
  delete: (id) => apiClient.delete(`/crm-api/customer-data/tour-inquiries/${id}/`),
};

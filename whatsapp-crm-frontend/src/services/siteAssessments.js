import apiClient from '@/lib/api';

export const siteAssessmentsApi = {
  list: (params) => apiClient.get('/crm-api/customer-data/site-assessments/', { params }),
  create: (data) => apiClient.post('/crm-api/customer-data/site-assessments/', data),
  update: (id, data) => apiClient.put(`/crm-api/customer-data/site-assessments/${id}/`, data),
  delete: (id) => apiClient.delete(`/crm-api/customer-data/site-assessments/${id}/`),
};

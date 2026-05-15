import apiClient from '@/lib/api';

function normalizePaginatedResponse(data) {
  if (Array.isArray(data)) {
    return { results: data, count: data.length, next: null, previous: null };
  }

  return {
    results: data?.results || [],
    count: data?.count || 0,
    next: data?.next || null,
    previous: data?.previous || null,
  };
}

export const adminApi = {
  async listUsers(params = {}) {
    const response = await apiClient.get('/crm-api/admin/users/', { params });
    return normalizePaginatedResponse(response.data);
  },

  async createUser(payload) {
    const response = await apiClient.post('/crm-api/admin/users/', payload);
    return response.data;
  },

  async updateUser(userId, payload) {
    const response = await apiClient.patch(`/crm-api/admin/users/${userId}/`, payload);
    return response.data;
  },

  async deactivateUser(userId) {
    const response = await apiClient.post(`/crm-api/admin/users/${userId}/deactivate/`);
    return response.data;
  },

  async activateUser(userId) {
    const response = await apiClient.post(`/crm-api/admin/users/${userId}/activate/`);
    return response.data;
  },

  async listRoles(params = {}) {
    const response = await apiClient.get('/crm-api/admin/roles/', { params });
    return normalizePaginatedResponse(response.data);
  },

  async createRole(payload) {
    const response = await apiClient.post('/crm-api/admin/roles/', payload);
    return response.data;
  },

  async updateRole(roleId, payload) {
    const response = await apiClient.patch(`/crm-api/admin/roles/${roleId}/`, payload);
    return response.data;
  },

  async listPermissions() {
    const response = await apiClient.get('/crm-api/admin/roles/permissions/');
    return response.data || [];
  },

  async listAudit(params = {}) {
    const response = await apiClient.get('/crm-api/admin/audit/', { params });
    return normalizePaginatedResponse(response.data);
  },
};

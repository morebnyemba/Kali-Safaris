import apiClient from '@/lib/api';

// Admin pages render their own (field-level) errors.
const quiet = { suppressErrorToast: true };

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
    const response = await apiClient.get('/crm-api/admin/users/', { params, ...quiet });
    return normalizePaginatedResponse(response.data);
  },

  async createUser(payload) {
    const response = await apiClient.post('/crm-api/admin/users/', payload, quiet);
    return response.data;
  },

  async updateUser(userId, payload) {
    const response = await apiClient.patch(`/crm-api/admin/users/${userId}/`, payload, quiet);
    return response.data;
  },

  async deactivateUser(userId) {
    const response = await apiClient.post(`/crm-api/admin/users/${userId}/deactivate/`, null, quiet);
    return response.data;
  },

  async activateUser(userId) {
    const response = await apiClient.post(`/crm-api/admin/users/${userId}/activate/`, null, quiet);
    return response.data;
  },

  async listRoles(params = {}) {
    const response = await apiClient.get('/crm-api/admin/roles/', { params, ...quiet });
    return normalizePaginatedResponse(response.data);
  },

  async createRole(payload) {
    const response = await apiClient.post('/crm-api/admin/roles/', payload, quiet);
    return response.data;
  },

  async updateRole(roleId, payload) {
    const response = await apiClient.patch(`/crm-api/admin/roles/${roleId}/`, payload, quiet);
    return response.data;
  },

  async listPermissions() {
    const response = await apiClient.get('/crm-api/admin/roles/permissions/', quiet);
    return response.data || [];
  },

  async deleteRole(roleId) {
    await apiClient.delete(`/crm-api/admin/roles/${roleId}/`, quiet);
  },

  async listAudit(params = {}) {
    const response = await apiClient.get('/crm-api/admin/audit/', { params, ...quiet });
    return normalizePaginatedResponse(response.data);
  },
};

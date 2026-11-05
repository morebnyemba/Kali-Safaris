import apiClient from '@/lib/api';

const BASE = '/crm-api/customer-data/payments/';

export const paymentsApi = {
  list: (params) => apiClient.get(BASE, { params }),
  summary: (params) => apiClient.get(`${BASE}summary/`, { params }),
  approve: (id) => apiClient.post(`${BASE}${id}/approve/`),
  reject: (id, reason) => apiClient.post(`${BASE}${id}/reject/`, { reason }),
};

export const PAYMENT_METHODS = [
  ['cbz_card', 'Card (Visa/Mastercard)'], ['cbz_ecocash', 'EcoCash (CBZ)'], ['omari', 'Omari'],
  ['paynow_ecocash', 'Paynow – EcoCash'], ['paynow_onemoney', 'Paynow – OneMoney'], ['paynow_innbucks', 'Paynow – InnBucks'],
  ['bank_transfer', 'Bank transfer'], ['credit_card', 'Credit card'], ['other', 'Other'],
];

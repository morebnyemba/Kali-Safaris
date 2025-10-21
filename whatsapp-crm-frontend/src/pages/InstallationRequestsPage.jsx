
import React, { useEffect, useState } from 'react';
import { installationRequestsApi } from '@/services/installationRequests';
import { Button } from '@/components/ui/button';

export default function InstallationRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    installationRequestsApi.list()
      .then(res => setRequests(res.data.results || res.data))
      .catch(err => setError('Failed to load installation requests.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Installation Requests</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && (
        <table className="min-w-full border text-sm">
          <thead>
            <tr>
              <th className="border px-2 py-1">ID</th>
              <th className="border px-2 py-1">Full Name</th>
              <th className="border px-2 py-1">Status</th>
              <th className="border px-2 py-1">Type</th>
              <th className="border px-2 py-1">Order #</th>
              <th className="border px-2 py-1">Created</th>
              <th className="border px-2 py-1">WhatsApp</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(requests) && requests.map(req => (
              <tr key={req.id}>
                <td className="border px-2 py-1">{req.id}</td>
                <td className="border px-2 py-1">{req.customer?.full_name || req.full_name || '-'}</td>
                <td className="border px-2 py-1">{req.status}</td>
                <td className="border px-2 py-1">{req.installation_type}</td>
                <td className="border px-2 py-1">{req.order_number}</td>
                <td className="border px-2 py-1">{req.created_at?.slice(0,10)}</td>
                <td className="border px-2 py-1">
                  {req.contact_phone ? (
                    <a
                      href={`https://wa.me/${req.contact_phone.replace(/[^\d]/g, '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-green-500 text-white hover:bg-green-600 transition"
                    >
                      WhatsApp
                    </a>
                  ) : (
                    <span className="text-gray-400">N/A</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}


import React, { useEffect, useState } from 'react';
import { siteAssessmentsApi } from '@/services/siteAssessments';
import { Button } from '@/components/ui/button';

export default function SiteAssessmentsPage() {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    siteAssessmentsApi.list()
      .then(res => setAssessments(res.data.results || res.data))
      .catch(() => setError('Failed to load site assessments.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Site Assessments</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && (
        <table className="min-w-full border text-sm">
          <thead>
            <tr>
              <th className="border px-2 py-1">ID</th>
              <th className="border px-2 py-1">Customer</th>
              <th className="border px-2 py-1">Status</th>
              <th className="border px-2 py-1">Scheduled</th>
              <th className="border px-2 py-1">Created</th>
              <th className="border px-2 py-1">WhatsApp</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(assessments) && assessments.map(a => (
              <tr key={a.id}>
                <td className="border px-2 py-1">{a.id}</td>
                <td className="border px-2 py-1">{a.customer?.full_name || a.customer_name || '-'}</td>
                <td className="border px-2 py-1">{a.status_display || a.status}</td>
                <td className="border px-2 py-1">{a.scheduled_date || '-'}</td>
                <td className="border px-2 py-1">{a.created_at?.slice(0,10)}</td>
                <td className="border px-2 py-1">
                  {a.contact_info && /^\+?\d{7,15}$/.test(a.contact_info.replace(/[^\d+]/g, '')) ? (
                    <a
                      href={`https://wa.me/${a.contact_info.replace(/[^\d]/g, '')}`}
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

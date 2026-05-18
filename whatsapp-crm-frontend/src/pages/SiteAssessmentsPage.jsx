
import React, { useEffect, useState } from 'react';
import { siteAssessmentsApi } from '@/services/siteAssessments';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogClose } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function SiteAssessmentsPage() {
  const [inquiries, setInquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add');
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({
    customer: '',
    status: 'new',
    lead_traveler_name: '',
    destinations: '',
    preferred_dates: '',
    number_of_travelers: '',
    notes: '',
    assigned_agent: '',
  });

  const fetchInquiries = () => {
    setLoading(true);
    setError(null);
    siteAssessmentsApi.list()
      .then((res) => setInquiries(res.data.results || res.data))
      .catch(() => setError('Failed to load inquiries.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchInquiries();
  }, []);

  const openAddModal = () => {
    setModalMode('add');
    setEditingId(null);
    setForm({
      customer: '',
      status: 'new',
      lead_traveler_name: '',
      destinations: '',
      preferred_dates: '',
      number_of_travelers: '',
      notes: '',
      assigned_agent: '',
    });
    setShowModal(true);
  };

  const openEditModal = (inquiry) => {
    setModalMode('edit');
    setEditingId(inquiry.id);
    setForm({
      customer: inquiry.customer || '',
      status: inquiry.status || 'new',
      lead_traveler_name: inquiry.lead_traveler_name || '',
      destinations: inquiry.destinations || '',
      preferred_dates: inquiry.preferred_dates || '',
      number_of_travelers: inquiry.number_of_travelers ?? '',
      notes: inquiry.notes || '',
      assigned_agent: inquiry.assigned_agent || '',
    });
    setShowModal(true);
  };

  const handleFormChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      ...form,
      customer: form.customer ? Number(form.customer) : null,
      assigned_agent: form.assigned_agent ? Number(form.assigned_agent) : null,
      number_of_travelers: form.number_of_travelers === '' ? null : Number(form.number_of_travelers),
    };

    try {
      if (modalMode === 'add') {
        await siteAssessmentsApi.create(payload);
      } else {
        await siteAssessmentsApi.update(editingId, payload);
      }
      setShowModal(false);
      fetchInquiries();
    } catch {
      alert('Failed to save inquiry.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this inquiry?')) return;
    try {
      await siteAssessmentsApi.delete(id);
      fetchInquiries();
    } catch {
      alert('Failed to delete inquiry.');
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Tour Inquiries</h1>
        <Button onClick={openAddModal}>+ Add Inquiry</Button>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && (
        <div className="overflow-x-auto rounded-lg shadow border">
          <table className="min-w-full border text-sm">
            <thead>
              <tr>
                <th className="border px-2 py-1">Reference</th>
                <th className="border px-2 py-1">Lead Traveler</th>
                <th className="border px-2 py-1">Destinations</th>
                <th className="border px-2 py-1">Preferred Dates</th>
                <th className="border px-2 py-1">Travelers</th>
                <th className="border px-2 py-1">Status</th>
                <th className="border px-2 py-1">Created</th>
                <th className="border px-2 py-1">Actions</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(inquiries) && inquiries.length === 0 && (
                <tr><td colSpan={8} className="text-center py-8 text-gray-400">No inquiries found.</td></tr>
              )}
              {Array.isArray(inquiries) && inquiries.map((inquiry) => (
                <tr key={inquiry.id}>
                  <td className="border px-2 py-1">{inquiry.inquiry_reference || '-'}</td>
                  <td className="border px-2 py-1">{inquiry.lead_traveler_name || '-'}</td>
                  <td className="border px-2 py-1">{inquiry.destinations || '-'}</td>
                  <td className="border px-2 py-1">{inquiry.preferred_dates || '-'}</td>
                  <td className="border px-2 py-1">{inquiry.number_of_travelers ?? '-'}</td>
                  <td className="border px-2 py-1">{inquiry.status_display || inquiry.status}</td>
                  <td className="border px-2 py-1">{inquiry.created_at?.slice(0, 10)}</td>
                  <td className="border px-2 py-1 flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => openEditModal(inquiry)}>Edit</Button>
                    <Button size="sm" variant="destructive" onClick={() => handleDelete(inquiry.id)}>Delete</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <h2 className="text-lg font-semibold mb-2">{modalMode === 'add' ? 'Add Inquiry' : 'Edit Inquiry'}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="lead_traveler_name">Lead Traveler</Label>
                <Input id="lead_traveler_name" name="lead_traveler_name" value={form.lead_traveler_name} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="status">Status</Label>
                <Input id="status" name="status" value={form.status} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="destinations">Destinations</Label>
                <Input id="destinations" name="destinations" value={form.destinations} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="preferred_dates">Preferred Dates</Label>
                <Input id="preferred_dates" name="preferred_dates" value={form.preferred_dates} onChange={handleFormChange} />
              </div>
              <div>
                <Label htmlFor="number_of_travelers">Number of Travelers</Label>
                <Input id="number_of_travelers" name="number_of_travelers" type="number" min="1" value={form.number_of_travelers} onChange={handleFormChange} />
              </div>
              <div>
                <Label htmlFor="customer">Customer Profile ID (optional)</Label>
                <Input id="customer" name="customer" type="number" value={form.customer} onChange={handleFormChange} />
              </div>
              <div>
                <Label htmlFor="assigned_agent">Assigned Agent ID (optional)</Label>
                <Input id="assigned_agent" name="assigned_agent" type="number" value={form.assigned_agent} onChange={handleFormChange} />
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="notes">Notes</Label>
                <Input id="notes" name="notes" value={form.notes} onChange={handleFormChange} />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <DialogClose asChild>
                <Button type="button" variant="outline">Cancel</Button>
              </DialogClose>
              <Button type="submit">{modalMode === 'add' ? 'Create' : 'Save'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

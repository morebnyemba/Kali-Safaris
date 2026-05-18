import React, { useEffect, useState } from 'react';
import { ordersApi } from '@/services/orders';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogClose } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';


export default function OrdersPage() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add');
  const [form, setForm] = useState({
    customer: '',
    tour_name: '',
    start_date: '',
    end_date: '',
    number_of_adults: 1,
    number_of_children: 0,
    total_amount: '',
    payment_status: '',
    source: 'manual_entry',
    notes: '',
  });
  const [editingId, setEditingId] = useState(null);

  const fetchBookings = () => {
    setLoading(true);
    setError(null);
    ordersApi.list()
      .then((res) => setBookings(res.data.results || res.data))
      .catch(() => setError('Failed to load bookings.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchBookings();
  }, []);

  const openAddModal = () => {
    setForm({
      customer: '',
      tour_name: '',
      start_date: '',
      end_date: '',
      number_of_adults: 1,
      number_of_children: 0,
      total_amount: '',
      payment_status: 'pending',
      source: 'manual_entry',
      notes: '',
    });
    setModalMode('add');
    setEditingId(null);
    setShowModal(true);
  };

  const openEditModal = (booking) => {
    setForm({
      customer: booking.customer || '',
      tour_name: booking.tour_name || '',
      start_date: booking.start_date || '',
      end_date: booking.end_date || '',
      number_of_adults: booking.number_of_adults ?? 1,
      number_of_children: booking.number_of_children ?? 0,
      total_amount: booking.total_amount || '',
      payment_status: booking.payment_status || 'pending',
      source: booking.source || 'manual_entry',
      notes: booking.notes || '',
    });
    setModalMode('edit');
    setEditingId(booking.id);
    setShowModal(true);
  };

  const handleFormChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        customer: form.customer ? Number(form.customer) : null,
        number_of_adults: Number(form.number_of_adults || 0),
        number_of_children: Number(form.number_of_children || 0),
        total_amount: form.total_amount === '' ? '0.00' : form.total_amount,
      };

      if (modalMode === 'add') {
        await ordersApi.create(payload);
      } else if (modalMode === 'edit' && editingId) {
        await ordersApi.update(editingId, payload);
      }
      setShowModal(false);
      fetchBookings();
    } catch (err) {
      alert('Failed to save booking.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this booking?')) return;
    try {
      await ordersApi.delete(id);
      fetchBookings();
    } catch {
      alert('Failed to delete booking.');
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Bookings</h1>
        <Button onClick={openAddModal} variant="primary">+ Add Booking</Button>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && (
        <div className="overflow-x-auto rounded-lg shadow border">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 dark:bg-slate-800">
              <tr>
                <th className="border px-2 py-2">Reference</th>
                <th className="border px-2 py-2">Tour</th>
                <th className="border px-2 py-2">Dates</th>
                <th className="border px-2 py-2">PAX</th>
                <th className="border px-2 py-2">Payment</th>
                <th className="border px-2 py-2">Amount</th>
                <th className="border px-2 py-2">Created</th>
                <th className="border px-2 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(bookings) && bookings.length === 0 && (
                <tr><td colSpan={8} className="text-center py-8 text-gray-400">No bookings found.</td></tr>
              )}
              {Array.isArray(bookings) && bookings.map((booking) => (
                <tr key={booking.id} className="hover:bg-gray-50 dark:hover:bg-slate-700 transition">
                  <td className="border px-2 py-1">{booking.booking_reference || '-'}</td>
                  <td className="border px-2 py-1">{booking.tour_name || '-'}</td>
                  <td className="border px-2 py-1">{booking.start_date || '-'} - {booking.end_date || '-'}</td>
                  <td className="border px-2 py-1">{booking.number_of_adults || 0}A / {booking.number_of_children || 0}C</td>
                  <td className="border px-2 py-1">{booking.payment_status_display || booking.payment_status || '-'}</td>
                  <td className="border px-2 py-1">{booking.total_amount || '0.00'}</td>
                  <td className="border px-2 py-1">{booking.created_at?.slice(0, 10)}</td>
                  <td className="border px-2 py-1 flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => openEditModal(booking)}>Edit</Button>
                    <Button size="sm" variant="destructive" onClick={() => handleDelete(booking.id)}>Delete</Button>
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
            <h2 className="text-lg font-semibold mb-2">{modalMode === 'add' ? 'Add Booking' : 'Edit Booking'}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="tour_name">Tour Name</Label>
                <Input id="tour_name" name="tour_name" value={form.tour_name} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="customer">Customer Profile ID (optional)</Label>
                <Input id="customer" name="customer" type="number" value={form.customer} onChange={handleFormChange} />
              </div>
              <div>
                <Label htmlFor="start_date">Start Date</Label>
                <Input id="start_date" name="start_date" type="date" value={form.start_date} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="end_date">End Date</Label>
                <Input id="end_date" name="end_date" type="date" value={form.end_date} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="number_of_adults">Adults</Label>
                <Input id="number_of_adults" name="number_of_adults" type="number" min="0" value={form.number_of_adults} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="number_of_children">Children</Label>
                <Input id="number_of_children" name="number_of_children" type="number" min="0" value={form.number_of_children} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="total_amount">Total Amount</Label>
                <Input id="total_amount" name="total_amount" type="number" min="0" step="0.01" value={form.total_amount} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="payment_status">Payment Status</Label>
                <Input id="payment_status" name="payment_status" value={form.payment_status} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="source">Source</Label>
                <Input id="source" name="source" value={form.source} onChange={handleFormChange} required />
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
              <Button type="submit" variant="primary">{modalMode === 'add' ? 'Create' : 'Save'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}



import React, { useEffect, useState } from 'react';
import { ordersApi } from '@/services/orders';
import { Button } from '@/components/ui/button';
import { Dialog, DialogTrigger, DialogContent, DialogClose } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';


export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [form, setForm] = useState({
    name: '',
    amount: '',
    currency: 'USD',
    stage: '',
    payment_status: '',
  });
  const [editingId, setEditingId] = useState(null);

  const fetchOrders = () => {
    setLoading(true);
    setError(null);
    ordersApi.list()
      .then(res => setOrders(res.data.results || res.data))
      .catch(() => setError('Failed to load orders.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const openAddModal = () => {
    setForm({ name: '', amount: '', currency: 'USD', stage: '', payment_status: '' });
    setModalMode('add');
    setEditingId(null);
    setShowModal(true);
  };

  const openEditModal = (order) => {
    setForm({
      name: order.name || '',
      amount: order.amount || '',
      currency: order.currency || 'USD',
      stage: order.stage || '',
      payment_status: order.payment_status || '',
    });
    setModalMode('edit');
    setEditingId(order.id);
    setShowModal(true);
  };

  const handleFormChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (modalMode === 'add') {
        await ordersApi.create(form);
      } else if (modalMode === 'edit' && editingId) {
        await ordersApi.update(editingId, form);
      }
      setShowModal(false);
      fetchOrders();
    } catch (err) {
      alert('Failed to save order.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this order?')) return;
    try {
      await ordersApi.delete(id);
      fetchOrders();
    } catch {
      alert('Failed to delete order.');
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Orders</h1>
        <Button onClick={openAddModal} variant="primary">+ Add Order</Button>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && (
        <div className="overflow-x-auto rounded-lg shadow border">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 dark:bg-slate-800">
              <tr>
                <th className="border px-2 py-2">Order #</th>
                <th className="border px-2 py-2">Name</th>
                <th className="border px-2 py-2">Stage</th>
                <th className="border px-2 py-2">Payment</th>
                <th className="border px-2 py-2">Amount</th>
                <th className="border px-2 py-2">Created</th>
                <th className="border px-2 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(orders) && orders.length === 0 && (
                <tr><td colSpan={7} className="text-center py-8 text-gray-400">No orders found.</td></tr>
              )}
              {Array.isArray(orders) && orders.map(order => (
                <tr key={order.id} className="hover:bg-gray-50 dark:hover:bg-slate-700 transition">
                  <td className="border px-2 py-1">{order.order_number}</td>
                  <td className="border px-2 py-1">{order.customer?.full_name || order.customer?.company || '-'}</td>
                  <td className="border px-2 py-1">{order.stage_display || order.stage}</td>
                  <td className="border px-2 py-1">{order.payment_status_display || order.payment_status}</td>
                  <td className="border px-2 py-1">{order.amount} {order.currency}</td>
                  <td className="border px-2 py-1">{order.created_at?.slice(0,10)}</td>
                  <td className="border px-2 py-1 flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => openEditModal(order)}>Edit</Button>
                    <Button size="sm" variant="destructive" onClick={() => handleDelete(order.id)}>Delete</Button>
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
            <h2 className="text-lg font-semibold mb-2">{modalMode === 'add' ? 'Add Order' : 'Edit Order'}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Name</Label>
                <Input id="name" name="name" value={form.name} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="amount">Amount</Label>
                <Input id="amount" name="amount" type="number" value={form.amount} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="currency">Currency</Label>
                <Input id="currency" name="currency" value={form.currency} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="stage">Stage</Label>
                <Input id="stage" name="stage" value={form.stage} onChange={handleFormChange} required />
              </div>
              <div>
                <Label htmlFor="payment_status">Payment Status</Label>
                <Input id="payment_status" name="payment_status" value={form.payment_status} onChange={handleFormChange} required />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <DialogClose asChild>
                <Button type="button" variant="outline">Cancel</Button>
              </DialogClose>
              <Button type="submit" variant="primary">{modalMode === 'add' ? 'Add' : 'Save'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

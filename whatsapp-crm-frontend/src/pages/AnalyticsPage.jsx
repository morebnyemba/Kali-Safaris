// src/pages/AnalyticsPage.jsx
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { subDays, startOfYear } from 'date-fns';
import {
  Bar, BarChart, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { FiCalendar, FiCheckCircle, FiDollarSign, FiMessageSquare, FiRefreshCw, FiUsers } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import PageHeader from '@/components/app/PageHeader';
import StatCard from '@/components/app/StatCard';
import StatusBadge from '@/components/app/StatusBadge';
import { EmptyState, ErrorState, LoadingState } from '@/components/app/States';
import { dashboardApi } from '@/lib/api';
import { apiErrorMessage, formatDate, formatMoney, formatNumber, toIsoDate } from '@/lib/format';

const PRESETS = [
  { key: '7d', label: '7 days', from: () => subDays(new Date(), 6) },
  { key: '30d', label: '30 days', from: () => subDays(new Date(), 29) },
  { key: '90d', label: '90 days', from: () => subDays(new Date(), 89) },
  { key: 'ytd', label: 'This year', from: () => startOfYear(new Date()) },
];

const tooltipStyle = { background: 'var(--popover)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 };
const axisTick = { fontSize: 11, fill: 'var(--muted-foreground)' };

function ChartCard({ title, description, children, className = '' }) {
  return (
    <Card className={`gap-0 py-0 ${className}`}>
      <CardHeader className="border-b py-4">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="py-4">{children}</CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const [range, setRange] = useState(() => ({ preset: '30d', start: toIsoDate(subDays(new Date(), 29)), end: toIsoDate(new Date()) }));
  const [data, setData] = useState({ bookings: null, messages: null, engagement: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    const params = { start_date: range.start, end_date: range.end };
    try {
      const [bookings, messages, engagement] = await Promise.all([
        dashboardApi.getBookingStats(params),
        dashboardApi.getMessageVolume(params),
        dashboardApi.getEngagement(params),
      ]);
      setData({ bookings: bookings.data, messages: messages.data, engagement: engagement.data });
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [range.start, range.end]);

  useEffect(() => { load(); }, [load]);

  const choosePreset = (preset) => {
    setRange({ preset: preset.key, start: toIsoDate(preset.from()), end: toIsoDate(new Date()) });
  };

  const kpis = data.bookings?.kpis;
  const series = useMemo(
    () => (data.bookings?.series || []).map((d) => ({ ...d, label: formatDate(d.date, 'd MMM') })),
    [data.bookings],
  );
  const messageSeries = useMemo(
    () => (data.messages?.volume_per_period || []).map((d) => ({
      label: formatDate(d.period, 'd MMM'), received: d.incoming_messages, sent: d.outgoing_messages,
    })),
    [data.messages],
  );
  const totalMessages = messageSeries.reduce((sum, d) => sum + d.received + d.sent, 0);

  return (
    <>
      <PageHeader
        title="Analytics"
        description={`${formatDate(range.start)} – ${formatDate(range.end)}`}
        actions={(
          <Button variant="outline" size="sm" onClick={load} disabled={loading}>
            <FiRefreshCw className={loading ? 'animate-spin' : ''} /> Refresh
          </Button>
        )}
      />

      <div className="mb-6 flex flex-col gap-3 rounded-xl border bg-card p-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-wrap gap-1" role="group" aria-label="Date range presets">
          {PRESETS.map((p) => (
            <Button key={p.key} size="sm" variant={range.preset === p.key ? 'default' : 'ghost'} onClick={() => choosePreset(p)}>
              {p.label}
            </Button>
          ))}
        </div>
        <div className="flex items-end gap-2">
          <div>
            <Label htmlFor="range-start" className="mb-1 text-xs text-muted-foreground">From</Label>
            <Input id="range-start" type="date" value={range.start} max={range.end}
              onChange={(e) => e.target.value && setRange((r) => ({ ...r, preset: 'custom', start: e.target.value }))} className="h-8 w-40" />
          </div>
          <div>
            <Label htmlFor="range-end" className="mb-1 text-xs text-muted-foreground">To</Label>
            <Input id="range-end" type="date" value={range.end} min={range.start}
              onChange={(e) => e.target.value && setRange((r) => ({ ...r, preset: 'custom', end: e.target.value }))} className="h-8 w-40" />
          </div>
        </div>
      </div>

      {error ? <ErrorState message={error} onRetry={load} /> : loading && !data.bookings ? <LoadingState label="Loading analytics…" /> : (
        <>
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Revenue received" value={formatMoney(kpis?.revenue)} hint={`${kpis?.payments_count ?? 0} successful payments`} icon={FiDollarSign} tone="accent" loading={loading} />
            <StatCard label="Bookings created" value={formatNumber(kpis?.bookings_created)} hint={`${kpis?.bookings_confirmed ?? 0} confirmed`} icon={FiCalendar} loading={loading} />
            <StatCard label="Inquiries received" value={formatNumber(kpis?.inquiries_created)} hint={`${kpis?.open_inquiries ?? 0} still open overall`} icon={FiCheckCircle} tone="info" loading={loading} />
            <StatCard label="Customers who messaged" value={formatNumber(data.engagement?.active_contacts_in_period)} hint={`${formatNumber(totalMessages)} messages · ${data.engagement?.handovers_requested_in_period ?? 0} handovers`} icon={FiUsers} tone="warning" loading={loading} />
          </div>

          <div className="mb-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
            <ChartCard title="Bookings & revenue" description="New bookings per day and payments received" className="xl:col-span-2">
              <div className="h-72">
                {series.length === 0 ? <EmptyState icon={FiCalendar} title="No bookings in this period" /> : (
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={series} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="label" tick={axisTick} tickLine={false} axisLine={false} />
                      <YAxis yAxisId="left" allowDecimals={false} tick={axisTick} tickLine={false} axisLine={false} />
                      <YAxis yAxisId="right" orientation="right" tick={axisTick} tickLine={false} axisLine={false} tickFormatter={(v) => `$${v}`} />
                      <Tooltip contentStyle={tooltipStyle} formatter={(v, n) => (n === 'Revenue' ? formatMoney(v) : v)} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Bar yAxisId="left" dataKey="bookings" name="Bookings" fill="var(--chart-1)" radius={[4, 4, 0, 0]} maxBarSize={28} />
                      <Line yAxisId="right" type="monotone" dataKey="revenue" name="Revenue" stroke="var(--chart-2)" strokeWidth={2} dot={false} />
                    </ComposedChart>
                  </ResponsiveContainer>
                )}
              </div>
            </ChartCard>

            <ChartCard title="Booking status" description="Bookings created in this period">
              {(data.bookings?.status_breakdown?.length ?? 0) === 0 ? <EmptyState title="No bookings" /> : (
                <ul className="space-y-3">
                  {data.bookings.status_breakdown.map((s) => {
                    const pct = kpis?.bookings_created ? Math.round((s.count / kpis.bookings_created) * 100) : 0;
                    return (
                      <li key={s.status}>
                        <div className="mb-1 flex items-center justify-between text-sm">
                          <StatusBadge status={s.status} />
                          <span className="tabular-nums text-muted-foreground">{s.count} · {pct}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-muted">
                          <div className="h-1.5 rounded-full bg-primary" style={{ width: `${pct}%` }} />
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <ChartCard title="WhatsApp messages" description="Received vs sent per day" className="xl:col-span-2">
              <div className="h-64">
                {messageSeries.length === 0 ? <EmptyState icon={FiMessageSquare} title="No messages in this period" /> : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={messageSeries} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="label" tick={axisTick} tickLine={false} axisLine={false} />
                      <YAxis allowDecimals={false} tick={axisTick} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Bar dataKey="received" name="Received" stackId="m" fill="var(--chart-1)" maxBarSize={28} />
                      <Bar dataKey="sent" name="Sent" stackId="m" fill="var(--chart-3)" radius={[4, 4, 0, 0]} maxBarSize={28} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </ChartCard>

            <ChartCard title="Top tours" description="By bookings created">
              {(data.bookings?.by_tour?.length ?? 0) === 0 ? <EmptyState title="No bookings" /> : (
                <table className="w-full text-sm">
                  <thead className="text-left text-xs text-muted-foreground">
                    <tr><th className="pb-2 font-medium">Tour</th><th className="pb-2 pl-4 text-right font-medium">Bookings</th><th className="pb-2 pl-4 text-right font-medium">Value</th></tr>
                  </thead>
                  <tbody className="divide-y">
                    {data.bookings.by_tour.map((t) => (
                      <tr key={t.tour_name}>
                        <td className="py-2 pr-2">{t.tour_name}</td>
                        <td className="py-2 pl-4 text-right tabular-nums">{t.bookings}</td>
                        <td className="whitespace-nowrap py-2 pl-4 text-right tabular-nums">{formatMoney(t.value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </ChartCard>
          </div>
        </>
      )}
    </>
  );
}

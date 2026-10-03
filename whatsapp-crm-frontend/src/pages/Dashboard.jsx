// src/pages/Dashboard.jsx
import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import {
  FiAlertTriangle, FiArrowRight, FiCalendar, FiClipboard, FiDollarSign, FiDownload, FiMessageSquare,
  FiRefreshCw, FiUserCheck, FiUsers, FiZap,
} from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import PageHeader from '@/components/app/PageHeader';
import StatCard from '@/components/app/StatCard';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/app/States';
import { useAuth } from '@/context/AuthContext';
import { dashboardApi } from '@/lib/api';
import { apiErrorMessage, formatDate, formatMoney, formatNumber, formatRelative } from '@/lib/format';
import { ordersApi } from '@/services/orders';

const greeting = () => {
  const h = new Date().getHours();
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
};

function AttentionStrip({ kpis, stats }) {
  const items = [];
  if (kpis?.awaiting_details > 0) {
    items.push({
      to: '/bookings?status=awaiting_details',
      text: `${kpis.awaiting_details} paid booking${kpis.awaiting_details === 1 ? '' : 's'} waiting on passenger details`,
      hint: 'They stay off the manifest until every passenger is complete.',
    });
  }
  if (stats?.pending_human_handovers > 0) {
    items.push({
      to: '/conversation?filter=attention',
      text: `${stats.pending_human_handovers} conversation${stats.pending_human_handovers === 1 ? '' : 's'} need a human`,
      hint: 'The bot is paused for these customers.',
    });
  }
  if (items.length === 0) return null;
  return (
    <div className="mb-6 space-y-2">
      {items.map((item) => (
        <Link
          key={item.to}
          to={item.to}
          className="flex items-center gap-3 rounded-xl border border-warning/40 bg-warning/10 px-4 py-3 text-sm transition-colors hover:bg-warning/15"
        >
          <FiAlertTriangle className="size-5 shrink-0 text-warning" aria-hidden />
          <span className="min-w-0 flex-1">
            <span className="font-medium text-foreground">{item.text}</span>
            <span className="block text-xs text-muted-foreground sm:inline sm:pl-2">{item.hint}</span>
          </span>
          <FiArrowRight className="size-4 shrink-0 text-muted-foreground" aria-hidden />
        </Link>
      ))}
    </div>
  );
}

function DeparturesCard({ data, loading }) {
  const [busy, setBusy] = useState(null);
  const download = async (date) => {
    setBusy(date);
    try {
      await ordersApi.downloadManifest('park', date, 'pdf');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card className="gap-0 py-0 lg:col-span-3">
      <CardHeader className="flex flex-row items-center justify-between gap-2 border-b py-4">
        <div>
          <CardTitle className="text-base">Upcoming departures</CardTitle>
          <CardDescription>Confirmed passengers for the next {data?.departure_days ?? 14} days</CardDescription>
        </div>
        <Button asChild variant="ghost" size="sm"><Link to="/bookings">All bookings <FiArrowRight /></Link></Button>
      </CardHeader>
      <CardContent className="px-0">
        {loading ? <TableSkeleton rows={4} cols={4} /> : (data?.upcoming_departures?.length ?? 0) === 0 ? (
          <EmptyState icon={FiCalendar} title="No departures coming up" description="Confirmed bookings in the next two weeks will appear here." />
        ) : (
          <div className="relative overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Date</th>
                  <th className="px-4 py-2.5 font-medium">Tour</th>
                  <th className="px-4 py-2.5 text-right font-medium">Passengers</th>
                  <th className="px-4 py-2.5 font-medium"><span className="sr-only">Manifest</span></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.upcoming_departures.map((d) => (
                  <tr key={`${d.date}-${d.tour_name}`} className="hover:bg-muted/30">
                    <td className="whitespace-nowrap px-4 py-3 font-medium">{formatDate(d.date, 'EEE d MMM')}</td>
                    <td className="px-4 py-3">
                      <span className="block">{d.tour_name}</span>
                      <span className="text-xs text-muted-foreground">
                        {d.bookings} booking{d.bookings === 1 ? '' : 's'}
                        {d.held_bookings > 0 && (
                          <span className="text-warning"> · {d.held_bookings} held for details</span>
                        )}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-semibold tabular-nums">{d.passengers}</td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="outline" size="sm" onClick={() => download(d.date)} disabled={busy === d.date || d.passengers === 0}>
                        <FiDownload /> {busy === d.date ? 'Preparing…' : 'Manifest'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MessagingCard({ summary, loading }) {
  const stats = summary?.stats_cards || {};
  const trend = (summary?.charts_data?.conversation_trends || []).map((d) => ({
    date: formatDate(d.date, 'd MMM'), incoming: d.incoming_messages, outgoing: d.outgoing_messages,
  }));
  return (
    <Card className="gap-0 py-0 lg:col-span-2">
      <CardHeader className="flex flex-row items-center justify-between gap-2 border-b py-4">
        <div>
          <CardTitle className="text-base">WhatsApp activity</CardTitle>
          <CardDescription>Last 24 hours</CardDescription>
        </div>
        <Button asChild variant="ghost" size="sm"><Link to="/conversation">Inbox <FiArrowRight /></Link></Button>
      </CardHeader>
      <CardContent className="space-y-4 py-4">
        <dl className="grid grid-cols-3 gap-3 text-center">
          {[
            ['Received', stats.messages_received_24h],
            ['Sent', stats.messages_sent_24h],
            ['Active chats', stats.active_conversations_count],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg bg-muted/50 px-2 py-3">
              <dt className="text-xs text-muted-foreground">{label}</dt>
              <dd className="mt-1 text-xl font-semibold tabular-nums">{loading ? '…' : formatNumber(value ?? 0)}</dd>
            </div>
          ))}
        </dl>
        <div className="h-36" aria-label="Messages per day">
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: 'var(--popover)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="incoming" name="Received" stroke="var(--chart-1)" fill="var(--chart-1)" fillOpacity={0.15} strokeWidth={2} />
                <Area type="monotone" dataKey="outgoing" name="Sent" stroke="var(--chart-2)" fill="var(--chart-2)" fillOpacity={0.12} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-muted-foreground">No messages in this period</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [bookingStats, setBookingStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    const [s, b] = await Promise.allSettled([dashboardApi.getSummary(), dashboardApi.getBookingStats()]);
    if (s.status === 'fulfilled') setSummary(s.value.data);
    if (b.status === 'fulfilled') setBookingStats(b.value.data);
    if (s.status === 'rejected' && b.status === 'rejected') setError(apiErrorMessage(b.reason));
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const kpis = bookingStats?.kpis;
  const stats = summary?.stats_cards;
  const name = user?.first_name || user?.username || '';

  if (error) {
    return <ErrorState message={error} onRetry={load} />;
  }

  return (
    <>
      <PageHeader
        title={`${greeting()}${name ? `, ${name}` : ''}`}
        description={`${formatDate(new Date(), 'EEEE d MMMM yyyy')} · here's what needs your attention today.`}
        actions={(
          <Button variant="outline" size="sm" onClick={load} disabled={loading}>
            <FiRefreshCw className={loading ? 'animate-spin' : ''} /> Refresh
          </Button>
        )}
      />

      <AttentionStrip kpis={kpis} stats={stats} />

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Passengers departing"
          value={formatNumber(kpis?.upcoming_passengers ?? 0)}
          hint={`Next ${bookingStats?.departure_days ?? 14} days`}
          icon={FiUserCheck}
          to="/bookings"
          loading={loading}
        />
        <StatCard
          label="Revenue received"
          value={formatMoney(kpis?.revenue ?? 0)}
          hint={`${kpis?.payments_count ?? 0} payments · last 30 days`}
          icon={FiDollarSign}
          tone="accent"
          to="/analytics"
          loading={loading}
        />
        <StatCard
          label="New bookings"
          value={formatNumber(kpis?.bookings_created ?? 0)}
          hint={`${kpis?.bookings_confirmed ?? 0} confirmed · last 30 days`}
          icon={FiCalendar}
          tone="info"
          to="/bookings"
          loading={loading}
        />
        <StatCard
          label="Open inquiries"
          value={formatNumber(kpis?.open_inquiries ?? 0)}
          hint={kpis?.pending_payment ? `${kpis.pending_payment} booking${kpis.pending_payment === 1 ? '' : 's'} awaiting payment` : 'Custom tour requests'}
          icon={FiClipboard}
          tone={kpis?.open_inquiries ? 'warning' : 'default'}
          to="/inquiries"
          loading={loading}
        />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-5">
        <DeparturesCard data={bookingStats} loading={loading} />
        <MessagingCard summary={summary} loading={loading} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <Card className="gap-0 py-0 lg:col-span-3">
          <CardHeader className="border-b py-4">
            <CardTitle className="text-base">Recent activity</CardTitle>
          </CardHeader>
          <CardContent className="px-0">
            {loading ? <TableSkeleton rows={4} cols={2} /> : (summary?.recent_activity_log?.length ?? 0) === 0 ? (
              <EmptyState title="Nothing yet" description="New contacts, bookings and flow changes show up here." />
            ) : (
              <ul className="divide-y">
                {summary.recent_activity_log.map((a) => (
                  <li key={a.id} className="flex items-start gap-3 px-4 py-3 text-sm">
                    <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                      {a.iconName === 'FiZap' ? <FiZap className="size-3.5" /> : a.iconName === 'FiUsers' ? <FiUsers className="size-3.5" /> : <FiMessageSquare className="size-3.5" />}
                    </span>
                    <span className="min-w-0 flex-1">{a.text}</span>
                    <span className="shrink-0 text-xs text-muted-foreground">{formatRelative(a.timestamp)}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="gap-0 py-0 lg:col-span-2">
          <CardHeader className="border-b py-4">
            <CardTitle className="text-base">Automation</CardTitle>
            <CardDescription>WhatsApp bot flows</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 py-4 text-sm">
            {[
              ['Active flows', summary?.flow_insights?.active_flows_count],
              ['Flows completed today', summary?.flow_insights?.flow_completions_today],
              ['Conversations needing a human', stats?.pending_human_handovers],
              ['WhatsApp number', stats?.meta_config_active_name || 'Not configured'],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">{label}</span>
                <span className="font-medium tabular-nums">{loading ? '…' : value ?? 0}</span>
              </div>
            ))}
            <div className="flex gap-2 pt-2">
              <Button asChild variant="outline" size="sm"><Link to="/flows">Manage flows</Link></Button>
              <Button asChild variant="ghost" size="sm"><Link to="/api-settings">WhatsApp API</Link></Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

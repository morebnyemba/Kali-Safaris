// src/pages/FlowsPage.jsx
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { FiEdit2, FiGitBranch, FiMoreHorizontal, FiPlus, FiSearch, FiTrash2 } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import PageHeader from '@/components/app/PageHeader';
import { EmptyState, ErrorState, TableSkeleton } from '@/components/app/States';
import { flowsApi } from '@/lib/api';
import { apiErrorMessage, formatRelative } from '@/lib/format';

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'inactive', label: 'Inactive' },
];

export default function FlowsPage() {
  const navigate = useNavigate();
  const [flows, setFlows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [togglingId, setTogglingId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await flowsApi.list({ page_size: 100 });
      setFlows(res.data.results || res.data || []);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return flows
      .filter((f) => filter === 'all' || (filter === 'active') === f.is_active)
      .filter((f) => !q || [f.name, f.description, ...(f.trigger_keywords || [])].some((v) => v?.toLowerCase().includes(q)));
  }, [flows, query, filter]);

  const counts = useMemo(() => ({
    all: flows.length,
    active: flows.filter((f) => f.is_active).length,
    inactive: flows.filter((f) => !f.is_active).length,
  }), [flows]);

  const toggle = async (flow) => {
    setTogglingId(flow.id);
    try {
      const res = await flowsApi.patch(flow.id, { is_active: !flow.is_active });
      setFlows((prev) => prev.map((f) => (f.id === flow.id ? res.data : f)));
      toast.success(`${res.data.name} ${res.data.is_active ? 'is live' : 'switched off'}`);
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not change the flow status'));
    } finally {
      setTogglingId(null);
    }
  };

  const remove = async (flow) => {
    if (!window.confirm(`Delete “${flow.name}” and all ${flow.steps_count ?? 0} of its steps? This cannot be undone.`)) return;
    try {
      await flowsApi.delete(flow.id);
      setFlows((prev) => prev.filter((f) => f.id !== flow.id));
      toast.success('Flow deleted');
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <>
      <PageHeader
        title="Flows"
        description="Automated WhatsApp conversations. A customer message matching a trigger keyword starts the flow."
        actions={<Button onClick={() => navigate('/flows/new')}><FiPlus /> New flow</Button>}
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-1" role="tablist" aria-label="Filter flows">
          {FILTERS.map((f) => (
            <Button key={f.key} role="tab" aria-selected={filter === f.key} size="sm" variant={filter === f.key ? 'secondary' : 'ghost'} onClick={() => setFilter(f.key)}>
              {f.label} <span className="tabular-nums text-muted-foreground">{counts[f.key]}</span>
            </Button>
          ))}
        </div>
        <div className="relative sm:w-72">
          <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search name or keyword" className="pl-9" aria-label="Search flows" />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border bg-card">
        {error ? <ErrorState message={error} onRetry={load} /> : loading ? <TableSkeleton rows={6} cols={4} /> : visible.length === 0 ? (
          <EmptyState
            icon={FiGitBranch}
            title={flows.length ? 'No flows match' : 'No flows yet'}
            description={flows.length ? 'Try another search or filter.' : 'Create a flow to start automating replies.'}
            action={!flows.length && <Button onClick={() => navigate('/flows/new')}><FiPlus /> New flow</Button>}
          />
        ) : (
          <ul className="divide-y">
            {visible.map((flow) => (
              <li key={flow.id} className="flex items-start gap-4 px-4 py-3 hover:bg-muted/40">
                <div className="min-w-0 flex-1">
                  <Link to={`/flows/edit/${flow.id}`} className="font-medium hover:underline">{flow.name}</Link>
                  <p className="truncate text-sm text-muted-foreground">{flow.description || 'No description'}</p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                    {(flow.trigger_keywords || []).slice(0, 5).map((k) => (
                      <span key={k} className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-foreground">{k}</span>
                    ))}
                    {(flow.trigger_keywords?.length || 0) > 5 && <span>+{flow.trigger_keywords.length - 5} more</span>}
                    {!flow.trigger_keywords?.length && <span className="italic">Started from another flow</span>}
                    <span aria-hidden>·</span>
                    <span>{flow.steps_count ?? 0} steps</span>
                    <span aria-hidden>·</span>
                    <span>Updated {formatRelative(flow.updated_at)}</span>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <label className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="hidden sm:inline">{flow.is_active ? 'Live' : 'Off'}</span>
                    <Switch checked={flow.is_active} disabled={togglingId === flow.id} onCheckedChange={() => toggle(flow)} aria-label={`${flow.name} active`} />
                  </label>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" aria-label={`Actions for ${flow.name}`}><FiMoreHorizontal /></Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => navigate(`/flows/edit/${flow.id}`)}><FiEdit2 className="size-4" /> Edit flow</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => remove(flow)} className="text-destructive focus:text-destructive"><FiTrash2 className="size-4" /> Delete</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

// src/pages/FlowEditorPage.jsx
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import {
  FiArrowLeft, FiArrowRight, FiGitBranch, FiInfo, FiMoreHorizontal, FiPlus, FiSearch, FiSettings, FiTrash2,
} from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { EmptyState, ErrorState, LoadingState } from '@/components/app/States';
import StepConfigEditor from '@/components/bot_builder/StepConfigEditor';
import TransitionEditorModal from '@/components/bot_builder/TransitionEditorModal';
import { flowsApi } from '@/lib/api';
import { apiErrorMessage } from '@/lib/format';

const selectClass = 'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';
const STEP_TYPES = {
  send_message: { label: 'Message', tone: 'bg-info/10 text-info' },
  question: { label: 'Question', tone: 'bg-brand-accent/10 text-brand-accent' },
  action: { label: 'Action', tone: 'bg-primary/10 text-primary' },
  condition: { label: 'Condition', tone: 'bg-warning/15 text-warning' },
  wait_for_reply: { label: 'Wait for reply', tone: 'bg-muted text-muted-foreground' },
  human_handover: { label: 'Handover', tone: 'bg-destructive/10 text-destructive' },
  switch_flow: { label: 'Switch flow', tone: 'bg-muted text-foreground' },
  start_flow_node: { label: 'Start', tone: 'bg-success/10 text-success' },
  end_flow: { label: 'End', tone: 'bg-muted text-muted-foreground' },
};
const NEW_STEP_CONFIG = {
  send_message: () => ({ message_type: 'text', text: { body: '', preview_url: false } }),
  question: () => ({ message_config: { message_type: 'text', text: { body: '' } }, reply_config: { save_to_variable: '', expected_type: 'text' } }),
  action: () => ({ actions_to_run: [] }),
  switch_flow: () => ({ target_flow_name: '' }),
};
const EMPTY_FLOW = { id: null, name: '', description: '', keywords: '', is_active: false };

function messageText(conf = {}) {
  return conf.text?.body || conf.interactive?.body?.text || conf[conf.message_type]?.caption || (conf.message_type ? `${conf.message_type} message` : '');
}

function stepSummary(step) {
  const c = step.config || {};
  switch (step.step_type) {
    case 'send_message': return messageText(c);
    case 'question': return messageText(c.message_config);
    case 'action': return (c.actions_to_run || []).map((a) => a.action_type).join(', ') || 'No actions';
    case 'switch_flow': return `Continues in ${c.target_flow_name || '—'}`;
    case 'end_flow': return messageText(c.message_config) || 'Ends the conversation';
    case 'human_handover': return c.pre_handover_message_text || 'Hands over to the team';
    default: return '';
  }
}

export default function FlowEditorPage() {
  const { flowId } = useParams();
  const navigate = useNavigate();
  const isNew = !flowId || flowId === 'new';

  const [flow, setFlow] = useState(EMPTY_FLOW);
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(!isNew);
  const [loadError, setLoadError] = useState('');
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const [addOpen, setAddOpen] = useState(false);
  const [newStep, setNewStep] = useState({ name: '', step_type: 'send_message' });
  const [addError, setAddError] = useState('');
  const [adding, setAdding] = useState(false);

  const [editingStep, setEditingStep] = useState(null);
  const [rulesStep, setRulesStep] = useState(null);
  const [transitions, setTransitions] = useState([]);
  const [loadingTransitions, setLoadingTransitions] = useState(false);
  const [editingTransition, setEditingTransition] = useState(null);

  const loadSteps = useCallback(async (id) => {
    const res = await flowsApi.listSteps(id);
    setSteps(res.data.results || res.data || []);
  }, []);

  const load = useCallback(async () => {
    if (isNew) { setFlow(EMPTY_FLOW); setSteps([]); setLoading(false); return; }
    setLoading(true);
    setLoadError('');
    try {
      const res = await flowsApi.retrieve(flowId);
      const f = res.data;
      setFlow({ id: f.id, name: f.name, description: f.description || '', keywords: (f.trigger_keywords || []).join(', '), is_active: f.is_active });
      await loadSteps(f.id);
      setDirty(false);
    } catch (err) {
      setLoadError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [flowId, isNew, loadSteps]);

  useEffect(() => { load(); }, [load]);

  const setField = (key) => (e) => { setFlow((f) => ({ ...f, [key]: e?.target ? e.target.value : e })); setDirty(true); };

  const saveFlow = async (e) => {
    e?.preventDefault();
    if (!flow.name.trim()) { toast.error('Give the flow a name'); return; }
    setSaving(true);
    const payload = {
      name: flow.name.trim(),
      description: flow.description,
      is_active: flow.is_active,
      trigger_keywords: flow.keywords.split(',').map((k) => k.trim()).filter(Boolean),
    };
    try {
      if (isNew) {
        const res = await flowsApi.create(payload);
        toast.success('Flow created — now add its steps');
        navigate(`/flows/edit/${res.data.id}`, { replace: true });
      } else {
        await flowsApi.patch(flow.id, payload);
        setDirty(false);
        toast.success('Flow saved');
      }
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not save the flow'));
    } finally {
      setSaving(false);
    }
  };

  const addStep = async (e) => {
    e.preventDefault();
    setAddError('');
    setAdding(true);
    try {
      const res = await flowsApi.createStep(flow.id, {
        flow: flow.id,
        name: newStep.name.trim(),
        step_type: newStep.step_type,
        config: NEW_STEP_CONFIG[newStep.step_type]?.() || {},
        is_entry_point: !steps.some((s) => s.is_entry_point),
      });
      setSteps((prev) => [...prev, res.data]);
      setAddOpen(false);
      setNewStep({ name: '', step_type: 'send_message' });
      setEditingStep(res.data);
    } catch (err) {
      setAddError(apiErrorMessage(err));
    } finally {
      setAdding(false);
    }
  };

  const saveStep = async (stepId, payload) => {
    try {
      const res = await flowsApi.patchStep(flow.id, stepId, payload);
      setSteps((prev) => prev.map((s) => (s.id === stepId ? res.data : s)));
      toast.success('Step saved');
      return true;
    } catch (err) {
      return apiErrorMessage(err, 'Could not save this step');
    }
  };

  const deleteStep = async (step) => {
    const incoming = steps.filter((s) => (s.outgoing_transitions || []).some((t) => t.next_step === step.id)).length;
    const warn = incoming ? ` ${incoming} other step(s) lead here and will lose that path.` : '';
    if (!window.confirm(`Delete step “${step.name}”?${warn}`)) return;
    try {
      await flowsApi.deleteStep(flow.id, step.id);
      await loadSteps(flow.id);
      toast.success('Step deleted');
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const openRules = async (step) => {
    setRulesStep(step);
    setEditingTransition(null);
    setLoadingTransitions(true);
    try {
      const res = await flowsApi.listTransitions(flow.id, step.id);
      setTransitions(res.data.results || res.data || []);
    } catch (err) {
      setTransitions([]);
      toast.error(apiErrorMessage(err));
    } finally {
      setLoadingTransitions(false);
    }
  };

  const saveTransition = async (isEditing, transitionId, payload) => {
    try {
      const res = isEditing
        ? await flowsApi.updateTransition(flow.id, rulesStep.id, transitionId, payload)
        : await flowsApi.createTransition(flow.id, rulesStep.id, { ...payload, current_step: rulesStep.id });
      setTransitions((prev) => (isEditing ? prev.map((t) => (t.id === res.data.id ? res.data : t)) : [...prev, res.data]));
      toast.success(isEditing ? 'Rule updated' : 'Rule added');
      return true;
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not save the rule'));
      return false;
    }
  };

  const deleteTransition = async (transitionId) => {
    if (!window.confirm('Delete this rule?')) return;
    try {
      await flowsApi.deleteTransition(flow.id, rulesStep.id, transitionId);
      setTransitions((prev) => prev.filter((t) => t.id !== transitionId));
      if (editingTransition?.id === transitionId) setEditingTransition(null);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const closeRules = () => {
    setRulesStep(null);
    setTransitions([]);
    setEditingTransition(null);
    loadSteps(flow.id).catch(() => {});
  };

  const typeCounts = useMemo(() => steps.reduce((acc, s) => ({ ...acc, [s.step_type]: (acc[s.step_type] || 0) + 1 }), {}), [steps]);
  const visibleSteps = useMemo(() => {
    const q = query.trim().toLowerCase();
    return steps
      .filter((s) => !typeFilter || s.step_type === typeFilter)
      .filter((s) => !q || s.name.toLowerCase().includes(q) || stepSummary(s).toLowerCase().includes(q))
      .sort((a, b) => Number(b.is_entry_point) - Number(a.is_entry_point));
  }, [steps, query, typeFilter]);
  const deadEnds = steps.filter((s) => !['end_flow', 'switch_flow', 'human_handover'].includes(s.step_type) && !(s.outgoing_transitions || []).length).length;

  if (loading) return <LoadingState label="Loading flow…" />;
  if (loadError) {
    return <ErrorState title="Couldn't open this flow" message={loadError} onRetry={load} />;
  }

  return (
    <>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <Button asChild variant="outline" size="icon" aria-label="Back to flows">
            <Link to="/flows"><FiArrowLeft /></Link>
          </Button>
          <div className="min-w-0">
            <h1 className="truncate text-2xl font-semibold tracking-tight">{isNew ? 'New flow' : flow.name || 'Untitled flow'}</h1>
            {!isNew && <p className="text-sm text-muted-foreground">{steps.length} steps{deadEnds ? ` · ${deadEnds} with no next step` : ''}</p>}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <Switch checked={flow.is_active} onCheckedChange={setField('is_active')} aria-label="Flow is live" />
            {flow.is_active ? 'Live' : 'Off'}
          </label>
          <Button onClick={saveFlow} disabled={saving || (!dirty && !isNew)}>{saving ? 'Saving…' : isNew ? 'Create flow' : dirty ? 'Save changes' : 'Saved'}</Button>
        </div>
      </div>

      <form onSubmit={saveFlow} className="mb-6 grid grid-cols-1 gap-4 rounded-xl border bg-card p-4 md:grid-cols-2">
        <div>
          <Label htmlFor="flow-name" className="mb-1.5">Name <span className="text-destructive">*</span></Label>
          <Input id="flow-name" className="font-mono text-sm" value={flow.name} onChange={setField('name')} placeholder="e.g. late_checkout_offer" required />
        </div>
        <div>
          <Label htmlFor="flow-keywords" className="mb-1.5">Trigger keywords</Label>
          <Input id="flow-keywords" value={flow.keywords} onChange={setField('keywords')} placeholder="e.g. book, tours" />
          <p className="mt-1 text-xs text-muted-foreground">Comma separated. Leave empty if another flow switches into this one.</p>
        </div>
        <div className="md:col-span-2">
          <Label htmlFor="flow-desc" className="mb-1.5">Description</Label>
          <Textarea id="flow-desc" rows={2} value={flow.description} onChange={setField('description')} placeholder="What this flow does for the customer" />
        </div>
        <button type="submit" hidden aria-hidden tabIndex={-1} />
      </form>

      {isNew ? (
        <p className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">Create the flow first, then add its steps.</p>
      ) : (
        <section aria-label="Steps" className="overflow-hidden rounded-xl border bg-card">
          <div className="flex flex-col gap-3 border-b p-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="-mx-1 flex gap-1 overflow-x-auto px-1">
              <Button size="sm" variant={typeFilter ? 'ghost' : 'secondary'} onClick={() => setTypeFilter('')}>All <span className="text-muted-foreground">{steps.length}</span></Button>
              {Object.entries(typeCounts).map(([t, n]) => (
                <Button key={t} size="sm" variant={typeFilter === t ? 'secondary' : 'ghost'} onClick={() => setTypeFilter(t)} className="shrink-0">
                  {STEP_TYPES[t]?.label || t} <span className="text-muted-foreground">{n}</span>
                </Button>
              ))}
            </div>
            <div className="flex gap-2">
              <div className="relative flex-1 lg:w-64">
                <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
                <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search steps" className="pl-9" aria-label="Search steps" />
              </div>
              <Button onClick={() => { setAddError(''); setAddOpen(true); }}><FiPlus /> Add step</Button>
            </div>
          </div>

          {steps.length === 0 ? (
            <EmptyState icon={FiGitBranch} title="No steps yet" description="Start with a message or a question; the first step becomes the entry point." />
          ) : visibleSteps.length === 0 ? (
            <EmptyState icon={FiSearch} title="No steps match" />
          ) : (
            <ul className="divide-y">
              {visibleSteps.map((step) => {
                const type = STEP_TYPES[step.step_type] || { label: step.step_type, tone: 'bg-muted' };
                const outs = [...(step.outgoing_transitions || [])].sort((a, b) => a.priority - b.priority);
                return (
                  <li key={step.id} className="flex items-start gap-3 px-4 py-3 hover:bg-muted/40">
                    <button type="button" onClick={() => setEditingStep(step)} className="min-w-0 flex-1 text-left">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-sm font-medium">{step.name}</span>
                        <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${type.tone}`}>{type.label}</span>
                        {step.is_entry_point && <span className="rounded bg-success/10 px-1.5 py-0.5 text-[11px] font-medium text-success">Entry point</span>}
                      </div>
                      {stepSummary(step) && <p className="mt-0.5 line-clamp-2 text-sm text-muted-foreground">{stepSummary(step)}</p>}
                      {outs.length > 0 ? (
                        <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
                          <FiArrowRight className="size-3" aria-hidden />
                          {outs.slice(0, 4).map((t) => <span key={t.id} className="font-mono">{t.next_step_name}</span>)}
                          {outs.length > 4 && <span>+{outs.length - 4}</span>}
                        </p>
                      ) : !['end_flow', 'switch_flow', 'human_handover'].includes(step.step_type) && (
                        <p className="mt-1 text-xs text-warning">No next step — the conversation stops here.</p>
                      )}
                    </button>
                    <div className="flex shrink-0 items-center">
                      <Button variant="ghost" size="sm" onClick={() => openRules(step)} className="hidden sm:inline-flex"><FiGitBranch /> Rules</Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" aria-label={`Actions for ${step.name}`}><FiMoreHorizontal /></Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => setEditingStep(step)}><FiSettings className="size-4" /> Edit step</DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openRules(step)}><FiGitBranch className="size-4" /> Next-step rules</DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => deleteStep(step)} className="text-destructive focus:text-destructive"><FiTrash2 className="size-4" /> Delete</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
          <p className="flex items-start gap-2 border-t bg-muted/30 px-4 py-3 text-xs text-muted-foreground">
            <FiInfo className="mt-0.5 size-3.5 shrink-0" aria-hidden />
            Built-in flows are installed from code by <code className="font-mono">load_flow_definitions</code>; re-running it replaces their steps, so permanent changes to those flows belong in the code.
          </p>
        </section>
      )}

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="sm:max-w-md">
          <form onSubmit={addStep} className="space-y-4">
            <DialogHeader>
              <DialogTitle>Add step</DialogTitle>
              <DialogDescription>You'll configure it next.</DialogDescription>
            </DialogHeader>
            <div>
              <Label htmlFor="ns-name" className="mb-1.5">Name <span className="text-destructive">*</span></Label>
              <Input id="ns-name" className="font-mono text-sm" value={newStep.name} onChange={(e) => setNewStep((s) => ({ ...s, name: e.target.value }))} placeholder="ask_travel_date" required autoFocus />
            </div>
            <div>
              <Label htmlFor="ns-type" className="mb-1.5">Type</Label>
              <select id="ns-type" className={selectClass} value={newStep.step_type} onChange={(e) => setNewStep((s) => ({ ...s, step_type: e.target.value }))}>
                {Object.entries(STEP_TYPES).filter(([k]) => k !== 'wait_for_reply').map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
            </div>
            {addError && <p role="alert" className="text-sm text-destructive">{addError}</p>}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAddOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={adding || !newStep.name.trim()}>{adding ? 'Adding…' : 'Add step'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {editingStep && (
        <StepConfigEditor key={editingStep.id} isOpen step={editingStep} onClose={() => setEditingStep(null)} onSaveStep={saveStep} />
      )}

      {rulesStep && (
        <TransitionEditorModal
          key={rulesStep.id}
          isOpen
          currentStep={rulesStep}
          allStepsInFlow={steps}
          existingTransitions={transitions}
          editingTransitionState={[editingTransition, setEditingTransition]}
          onClose={closeRules}
          onSave={saveTransition}
          onDelete={deleteTransition}
          isLoadingExternally={loadingTransitions}
        />
      )}
    </>
  );
}

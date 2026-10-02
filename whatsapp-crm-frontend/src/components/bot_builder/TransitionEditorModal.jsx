// src/components/bot_builder/TransitionEditorModal.jsx
import React, { useEffect, useMemo, useState } from 'react';
import { FiArrowRight, FiCode, FiEdit2, FiPlus, FiTrash2 } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { LoadingState } from '@/components/app/States';

const selectClass = 'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';
const VAR = { key: 'variable_name', label: 'Variable', placeholder: 'e.g. flow_context.num_adults', mono: true, required: true };
const NUMERIC = { fields: [VAR, { key: 'value_template', label: 'Compare with', placeholder: 'number or {{ variable }}', required: true }] };

// Mirrors the condition types evaluated in flows/services.py — keys must match exactly
// or the transition silently never fires.
const CONDITIONS = {
  always_true: { label: 'Always', fields: [] },
  user_reply_matches_keyword: { label: 'Reply is exactly', fields: [{ key: 'keyword', label: 'Text', required: true }, { key: 'case_sensitive', label: 'Case sensitive', type: 'bool' }] },
  user_reply_contains_keyword: { label: 'Reply contains', fields: [{ key: 'keyword', label: 'Text', required: true }, { key: 'case_sensitive', label: 'Case sensitive', type: 'bool' }] },
  interactive_reply_id_equals: { label: 'Button / list choice is', fields: [{ key: 'value', label: 'Reply ID', placeholder: 'id of the button or list row', mono: true, required: true }] },
  message_type_is: { label: 'Message type is', fields: [{ key: 'value', label: 'Type', type: 'select', options: ['text', 'image', 'document', 'audio', 'video', 'location', 'interactive', 'button', 'sticker'] }] },
  user_reply_matches_regex: { label: 'Reply matches pattern', fields: [{ key: 'regex', label: 'Regular expression', mono: true, required: true }] },
  variable_equals: { label: 'Variable equals', fields: [VAR, { key: 'value', label: 'Value', placeholder: 'leave empty to match “not set”' }] },
  variable_exists: { label: 'Variable is set', fields: [VAR] },
  variable_contains: { label: 'Variable contains', fields: [VAR, { key: 'value', label: 'Value', required: true }] },
  variable_greater_than: { label: 'Variable >', ...NUMERIC },
  variable_greater_than_or_equal: { label: 'Variable ≥', ...NUMERIC },
  variable_less_than: { label: 'Variable <', ...NUMERIC },
  variable_less_than_or_equal: { label: 'Variable ≤', ...NUMERIC },
  question_reply_is_valid: { label: 'Question answer validity', fields: [{ key: 'value', label: 'Answer was valid', type: 'bool', default: true }] },
  whatsapp_flow_response_received: { label: 'WhatsApp form submitted', fields: [{ ...VAR, required: false, placeholder: 'whatsapp_flow_response_received' }] },
  nfm_response_field_equals: { label: 'Form field equals', fields: [{ key: 'field_path', label: 'Field path', mono: true, required: true }, { key: 'value', label: 'Value' }] },
  user_requests_human: { label: 'Customer asks for a human', fields: [{ key: 'keywords', label: 'Keywords (comma separated)', type: 'list', placeholder: 'help, agent, human' }] },
  contact_is_admin: { label: 'Contact is staff', fields: [] },
};

function newConfig(type) {
  const config = { type };
  (CONDITIONS[type]?.fields || []).forEach((f) => {
    if (f.default !== undefined) config[f.key] = f.default;
    else if (f.type === 'bool') config[f.key] = false;
  });
  return config;
}

/** One-line human summary of a transition condition, e.g. `Reply is exactly "yes"`. */
function describeCondition(config) {
  const def = CONDITIONS[config?.type];
  if (!def) return config?.type || 'Unknown condition';
  const parts = def.fields
    .filter((f) => f.type !== 'bool' && config[f.key] !== undefined && config[f.key] !== '')
    .map((f) => (Array.isArray(config[f.key]) ? config[f.key].join(', ') : String(config[f.key])));
  if (config.type === 'question_reply_is_valid') return config.value === false ? 'Answer was invalid' : 'Answer was valid';
  return parts.length ? `${def.label} “${parts.join(' · ')}”` : def.label;
}

function ConditionFields({ config, onChange, disabled }) {
  const def = CONDITIONS[config.type];
  if (!def) return null;
  if (def.fields.length === 0) return <p className="text-sm text-muted-foreground">No settings — this condition needs nothing else.</p>;
  return def.fields.map((f) => {
    const id = `cond-${f.key}`;
    const value = config[f.key];
    if (f.type === 'bool') {
      return (
        <div key={f.key} className="flex items-center gap-2">
          <Switch id={id} checked={!!value} onCheckedChange={(v) => onChange(f.key, v)} disabled={disabled} />
          <Label htmlFor={id}>{f.label}</Label>
        </div>
      );
    }
    if (f.type === 'select') {
      return (
        <div key={f.key}>
          <Label htmlFor={id} className="mb-1.5">{f.label}</Label>
          <select id={id} className={selectClass} value={value || ''} onChange={(e) => onChange(f.key, e.target.value)} disabled={disabled}>
            <option value="" disabled>Choose…</option>
            {f.options.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        </div>
      );
    }
    return (
      <div key={f.key}>
        <Label htmlFor={id} className="mb-1.5">{f.label}{f.required && <span className="text-destructive"> *</span>}</Label>
        <Input
          id={id}
          value={f.type === 'list' ? (value || []).join(', ') : (value ?? '')}
          onChange={(e) => onChange(f.key, f.type === 'list' ? e.target.value.split(',').map((s) => s.trim()).filter(Boolean) : e.target.value)}
          placeholder={f.placeholder}
          required={f.required}
          className={f.mono ? 'font-mono text-xs' : ''}
          disabled={disabled}
        />
      </div>
    );
  });
}

export default function TransitionEditorModal({
  isOpen,
  currentStep,
  allStepsInFlow,
  existingTransitions,
  editingTransitionState,
  onClose,
  onSave,
  onDelete,
  isLoadingExternally,
}) {
  const [editingTransition, setEditingTransition] = editingTransitionState;
  const [nextStepId, setNextStepId] = useState('');
  const [priority, setPriority] = useState(0);
  const [config, setConfig] = useState(newConfig('always_true'));
  const [jsonMode, setJsonMode] = useState(false);
  const [jsonText, setJsonText] = useState('');
  const [jsonError, setJsonError] = useState('');
  const [saving, setSaving] = useState(false);

  const sorted = useMemo(() => [...(existingTransitions || [])].sort((a, b) => a.priority - b.priority), [existingTransitions]);
  const stepName = (id) => allStepsInFlow.find((s) => s.id === id)?.name;

  useEffect(() => {
    if (editingTransition) {
      const conf = editingTransition.condition_config && typeof editingTransition.condition_config === 'object'
        ? structuredClone(editingTransition.condition_config) : newConfig('always_true');
      setNextStepId(String(editingTransition.next_step ?? ''));
      setPriority(editingTransition.priority ?? 0);
      setConfig(conf);
      setJsonMode(!CONDITIONS[conf.type]);
      setJsonText(JSON.stringify(conf, null, 2));
    } else {
      const highest = (existingTransitions || []).reduce((max, t) => Math.max(max, t.priority), -1);
      setNextStepId('');
      setPriority(highest + 1);
      setConfig(newConfig('always_true'));
      setJsonMode(false);
      setJsonText('');
    }
    setJsonError('');
  }, [editingTransition, existingTransitions]);

  if (!isOpen || !currentStep) return null;

  const toggleJson = () => {
    if (!jsonMode) { setJsonText(JSON.stringify(config, null, 2)); setJsonError(''); setJsonMode(true); return; }
    try {
      const parsed = JSON.parse(jsonText);
      if (!parsed || typeof parsed !== 'object' || !parsed.type) throw new Error('Needs an object with a "type"');
      setConfig(parsed);
      setJsonMode(false);
    } catch (e) {
      setJsonError(e.message);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    let condition = config;
    if (jsonMode) {
      try {
        condition = JSON.parse(jsonText);
        if (!condition?.type) throw new Error('Condition needs a "type"');
      } catch (err) {
        setJsonError(err.message);
        return;
      }
    }
    if (!nextStepId) return;
    setSaving(true);
    const isEditing = !!editingTransition?.id;
    const ok = await onSave(isEditing, isEditing ? editingTransition.id : null, {
      next_step: Number(nextStepId), priority: Number(priority) || 0, condition_config: condition,
    });
    setSaving(false);
    if (ok) setEditingTransition(null);
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !saving && onClose()}>
      <DialogContent className="flex max-h-[90vh] flex-col gap-0 p-0 sm:max-w-4xl">
        <DialogHeader className="border-b p-5">
          <DialogTitle>Next steps after “{currentStep.name}”</DialogTitle>
          <DialogDescription>Rules are checked from the top; the first one that matches decides where the conversation goes.</DialogDescription>
        </DialogHeader>

        <div className="grid min-h-0 flex-1 grid-cols-1 overflow-y-auto md:grid-cols-2 md:overflow-hidden">
          <section aria-label="Existing rules" className="flex min-h-0 flex-col border-b md:border-b-0 md:border-r">
            <div className="flex items-center justify-between px-5 py-3">
              <h3 className="text-sm font-medium">Rules ({sorted.length})</h3>
              <Button size="sm" variant="ghost" onClick={() => setEditingTransition(null)} disabled={!editingTransition}><FiPlus /> New rule</Button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-3">
              {isLoadingExternally ? <LoadingState /> : sorted.length === 0 ? (
                <p className="px-2 py-8 text-center text-sm text-muted-foreground">No rules yet.</p>
              ) : (
                <ol className="space-y-1.5">
                  {sorted.map((t) => (
                    <li key={t.id} className={`rounded-lg border p-3 text-sm ${editingTransition?.id === t.id ? 'border-primary bg-primary/5' : ''}`}>
                      <div className="flex items-start gap-2">
                        <span className="mt-0.5 rounded bg-muted px-1.5 font-mono text-[11px] tabular-nums text-muted-foreground" title="Priority">{t.priority}</span>
                        <div className="min-w-0 flex-1">
                          <p className="break-words">{describeCondition(t.condition_config)}</p>
                          <p className="mt-0.5 flex items-center gap-1 text-muted-foreground">
                            <FiArrowRight className="size-3.5 shrink-0" aria-hidden />
                            <span className="truncate font-medium text-foreground">{t.next_step_name || stepName(t.next_step) || `Step #${t.next_step}`}</span>
                          </p>
                        </div>
                        <Button size="icon" variant="ghost" className="size-7" onClick={() => setEditingTransition(t)} aria-label="Edit rule"><FiEdit2 className="size-3.5" /></Button>
                        <Button size="icon" variant="ghost" className="size-7 text-destructive" onClick={() => onDelete(t.id)} aria-label="Delete rule"><FiTrash2 className="size-3.5" /></Button>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </section>

          <form onSubmit={submit} className="min-h-0 space-y-4 overflow-y-auto p-5">
            <h3 className="text-sm font-medium">{editingTransition ? 'Edit rule' : 'New rule'}</h3>
            <div>
              <Label htmlFor="t-next" className="mb-1.5">Go to step <span className="text-destructive">*</span></Label>
              <select id="t-next" className={selectClass} value={nextStepId} onChange={(e) => setNextStepId(e.target.value)} required disabled={saving}>
                <option value="" disabled>Choose a step…</option>
                {allStepsInFlow.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-[1fr_7rem] gap-3">
              <div>
                <Label htmlFor="t-type" className="mb-1.5">When</Label>
                <select id="t-type" className={selectClass} value={CONDITIONS[config.type] ? config.type : ''} disabled={saving || jsonMode}
                  onChange={(e) => setConfig(newConfig(e.target.value))}>
                  {!CONDITIONS[config.type] && <option value="">{config.type} (custom)</option>}
                  {Object.entries(CONDITIONS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                </select>
              </div>
              <div>
                <Label htmlFor="t-priority" className="mb-1.5">Order</Label>
                <Input id="t-priority" type="number" value={priority} onChange={(e) => setPriority(e.target.value)} disabled={saving} />
              </div>
            </div>

            <div className="space-y-3 rounded-lg border bg-muted/30 p-3">
              {jsonMode ? (
                <>
                  <Label htmlFor="t-json">Condition JSON</Label>
                  <Textarea id="t-json" rows={8} value={jsonText} onChange={(e) => { setJsonText(e.target.value); setJsonError(''); }} className="font-mono text-xs" disabled={saving} />
                  {jsonError && <p role="alert" className="text-xs text-destructive">{jsonError}</p>}
                </>
              ) : (
                <ConditionFields config={config} disabled={saving} onChange={(key, value) => setConfig((c) => ({ ...c, [key]: value }))} />
              )}
              <button type="button" onClick={toggleJson} className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
                <FiCode className="size-3.5" aria-hidden /> {jsonMode ? 'Back to form' : 'Edit as JSON'}
              </button>
            </div>

            <div className="flex justify-end gap-2">
              {editingTransition && <Button type="button" variant="outline" onClick={() => setEditingTransition(null)} disabled={saving}>Cancel</Button>}
              <Button type="submit" disabled={saving}>{saving ? 'Saving…' : editingTransition ? 'Save rule' : 'Add rule'}</Button>
            </div>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}

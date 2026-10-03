// src/components/bot_builder/StepConfigEditor.jsx
// Form editor for FlowStep.config. Shapes mirror whatsappcrm_backend/flows/schemas.py —
// in particular send_message config is FLAT ({message_type, text: {...}}), while question
// and end_flow nest the same shape under `message_config`.
import React, { useEffect, useState } from 'react';
import { FiCode, FiList, FiPlus, FiTrash2 } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { flowsApi } from '@/lib/api';
import MediaAssetSelector from './MediaAssetSelector';

const selectClass = 'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';
const FORM_TYPES = ['send_message', 'question', 'action', 'end_flow', 'human_handover', 'switch_flow'];
const MESSAGE_TYPES = [
  ['text', 'Text'], ['image', 'Image'], ['document', 'Document'], ['video', 'Video'], ['audio', 'Audio'],
  ['sticker', 'Sticker'], ['interactive', 'Buttons / list'], ['template', 'Template'], ['location', 'Location'], ['contacts', 'Contact card'],
];
const MEDIA_TYPES = ['image', 'document', 'video', 'audio', 'sticker'];
const REPLY_TYPES = [
  ['text', 'Any text'], ['number', 'Number'], ['email', 'Email address'], ['interactive_id', 'Button / list choice'],
  ['image', 'Image'], ['location', 'Location'], ['nfm_reply', 'WhatsApp form reply'],
];
const ACTION_FIELDS = {
  set_context_variable: [{ key: 'variable_name', label: 'Variable', mono: true }, { key: 'value_template', label: 'Value', placeholder: 'text or {{ template }}' }],
  update_contact_field: [{ key: 'field_path', label: 'Contact field', mono: true, placeholder: 'e.g. name' }, { key: 'value_template', label: 'Value' }],
  update_customer_profile: [{ key: 'fields_to_update', label: 'Fields to update', json: true }],
  send_admin_notification: [{ key: 'message_template', label: 'Message', multiline: true }],
};

function Field({ id, label, hint, children, required }) {
  return (
    <div>
      <Label htmlFor={id} className="mb-1.5">{label}{required && <span className="text-destructive"> *</span>}</Label>
      {children}
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function CharCount({ value, max }) {
  const n = (value || '').length;
  return <span className={`text-xs tabular-nums ${n > max ? 'text-destructive' : 'text-muted-foreground'}`}>{n}/{max}</span>;
}

/** Textarea bound to a JSON value; only valid JSON propagates, and validity is reported up. */
function JsonField({ id, value, onChange, onValidity, rows = 4, placeholder }) {
  const [text, setText] = useState(() => (value === undefined ? '' : JSON.stringify(value, null, 2)));
  const [error, setError] = useState('');
  return (
    <>
      <Textarea
        id={id}
        rows={rows}
        value={text}
        placeholder={placeholder}
        className="font-mono text-xs"
        onChange={(e) => {
          const next = e.target.value;
          setText(next);
          if (!next.trim()) { setError(''); onValidity?.(id, true); onChange(undefined); return; }
          try {
            onChange(JSON.parse(next));
            setError('');
            onValidity?.(id, true);
          } catch (err) {
            setError(err.message);
            onValidity?.(id, false);
          }
        }}
      />
      {error && <p role="alert" className="mt-1 text-xs text-destructive">Invalid JSON: {error}</p>}
    </>
  );
}

function defaultMessage(type, prev = {}) {
  const bodyText = prev.text?.body || prev.interactive?.body?.text || '';
  if (type === 'text') return { message_type: 'text', text: { body: bodyText, preview_url: false } };
  if (MEDIA_TYPES.includes(type)) return { message_type: type, [type]: { asset_pk: null, ...(type !== 'audio' && type !== 'sticker' ? { caption: '' } : {}) } };
  if (type === 'interactive') {
    return { message_type: 'interactive', interactive: { type: 'button', body: { text: bodyText }, action: { buttons: [{ type: 'reply', reply: { id: '', title: '' } }] } } };
  }
  return { message_type: type };
}

function ButtonsEditor({ buttons, onChange, idPrefix }) {
  const set = (i, key, v) => onChange(buttons.map((b, j) => (j === i ? { type: 'reply', reply: { ...b.reply, [key]: v } } : b)));
  return (
    <div className="space-y-2">
      <Label>Buttons <span className="font-normal text-muted-foreground">(up to 3)</span></Label>
      {buttons.map((b, i) => (
        <div key={i} className="grid grid-cols-[1fr_1fr_auto] items-start gap-2">
          <Input aria-label={`Button ${i + 1} title`} placeholder="Title (max 20)" maxLength={20} value={b.reply?.title || ''} onChange={(e) => set(i, 'title', e.target.value)} />
          <Input aria-label={`Button ${i + 1} reply ID`} id={i === 0 ? `${idPrefix}-btn-id` : undefined} placeholder="Reply ID" className="font-mono text-xs" value={b.reply?.id || ''} onChange={(e) => set(i, 'id', e.target.value)} />
          <Button type="button" size="icon" variant="ghost" aria-label={`Remove button ${i + 1}`} onClick={() => onChange(buttons.filter((_, j) => j !== i))}><FiTrash2 /></Button>
        </div>
      ))}
      {buttons.length < 3 && (
        <Button type="button" size="sm" variant="outline" onClick={() => onChange([...buttons, { type: 'reply', reply: { id: '', title: '' } }])}><FiPlus /> Add button</Button>
      )}
      <p className="text-xs text-muted-foreground">Transitions match on the reply ID, so keep IDs stable once the flow is live.</p>
    </div>
  );
}

function ListEditor({ action, onChange }) {
  const sections = action.sections || [];
  if (sections.some((s) => typeof s.rows === 'string')) {
    return <p className="text-sm text-muted-foreground">This list is built from a template at runtime — use “Edit as JSON” to change it.</p>;
  }
  const setSection = (i, next) => onChange({ ...action, sections: sections.map((s, j) => (j === i ? next : s)) });
  return (
    <div className="space-y-3">
      <Field id="l-button" label="Menu button label" hint="The button customers tap to open the list (max 20).">
        <Input id="l-button" maxLength={20} value={action.button || ''} onChange={(e) => onChange({ ...action, button: e.target.value })} />
      </Field>
      {sections.map((s, i) => (
        <fieldset key={i} className="space-y-2 rounded-lg border p-3">
          <div className="flex items-center gap-2">
            <Input aria-label={`Section ${i + 1} title`} placeholder="Section title (optional)" value={s.title || ''} onChange={(e) => setSection(i, { ...s, title: e.target.value })} />
            <Button type="button" size="icon" variant="ghost" aria-label={`Remove section ${i + 1}`} onClick={() => onChange({ ...action, sections: sections.filter((_, j) => j !== i) })}><FiTrash2 /></Button>
          </div>
          {(s.rows || []).map((r, k) => (
            <div key={k} className="grid grid-cols-1 gap-2 rounded-md bg-muted/40 p-2 sm:grid-cols-[1fr_1fr_auto]">
              <Input aria-label="Row title" placeholder="Title (max 24)" maxLength={24} value={r.title || ''} onChange={(e) => setSection(i, { ...s, rows: s.rows.map((x, m) => (m === k ? { ...x, title: e.target.value } : x)) })} />
              <Input aria-label="Row ID" placeholder="Reply ID" className="font-mono text-xs" value={r.id || ''} onChange={(e) => setSection(i, { ...s, rows: s.rows.map((x, m) => (m === k ? { ...x, id: e.target.value } : x)) })} />
              <Button type="button" size="icon" variant="ghost" aria-label="Remove row" onClick={() => setSection(i, { ...s, rows: s.rows.filter((_, m) => m !== k) })}><FiTrash2 /></Button>
              <Input aria-label="Row description" placeholder="Description (optional, max 72)" maxLength={72} className="sm:col-span-3" value={r.description || ''} onChange={(e) => setSection(i, { ...s, rows: s.rows.map((x, m) => (m === k ? { ...x, description: e.target.value } : x)) })} />
            </div>
          ))}
          <Button type="button" size="sm" variant="ghost" onClick={() => setSection(i, { ...s, rows: [...(s.rows || []), { id: '', title: '' }] })}><FiPlus /> Add row</Button>
        </fieldset>
      ))}
      <Button type="button" size="sm" variant="outline" onClick={() => onChange({ ...action, sections: [...sections, { title: '', rows: [{ id: '', title: '' }] }] })}><FiList /> Add section</Button>
    </div>
  );
}

function MessageFields({ value = {}, onChange, idPrefix }) {
  const type = value.message_type || 'text';
  const inter = value.interactive || {};
  const setInter = (patch) => onChange({ ...value, interactive: { ...inter, ...patch } });
  const media = value[type] || {};
  const setMedia = (patch) => onChange({ ...value, [type]: { ...media, ...patch } });

  return (
    <div className="space-y-4">
      <Field id={`${idPrefix}-type`} label="Message type">
        <select id={`${idPrefix}-type`} className={selectClass} value={type} onChange={(e) => onChange(defaultMessage(e.target.value, value))}>
          {MESSAGE_TYPES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
      </Field>

      {type === 'text' && (
        <>
          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <Label htmlFor={`${idPrefix}-body`}>Message <span className="text-destructive">*</span></Label>
              <CharCount value={value.text?.body} max={4096} />
            </div>
            <Textarea id={`${idPrefix}-body`} rows={6} value={value.text?.body || ''} onChange={(e) => onChange({ ...value, text: { ...value.text, body: e.target.value } })} placeholder="Hi {{ contact.name }} 👋" />
            <p className="mt-1 text-xs text-muted-foreground">Use {'{{ contact.name }}'} or {'{{ flow_context.some_value }}'} to insert data. *bold* and _italic_ work in WhatsApp.</p>
          </div>
          <div className="flex items-center gap-2">
            <Switch id={`${idPrefix}-preview`} checked={!!value.text?.preview_url} onCheckedChange={(v) => onChange({ ...value, text: { ...value.text, preview_url: v } })} />
            <Label htmlFor={`${idPrefix}-preview`}>Show link previews</Label>
          </div>
        </>
      )}

      {MEDIA_TYPES.includes(type) && (
        <>
          <Field id={`${idPrefix}-asset`} label="File" required hint={!media.asset_pk && (media.link || media.id) ? `Currently sent from ${media.link ? 'link' : 'media ID'} “${media.link || media.id}”. Picking a file replaces it.` : undefined}>
            <MediaAssetSelector id={`${idPrefix}-asset`} mediaTypeFilter={type} currentAssetPk={media.asset_pk ?? null} onAssetSelect={(pk) => setMedia({ asset_pk: pk })} />
          </Field>
          {type !== 'audio' && type !== 'sticker' && (
            <Field id={`${idPrefix}-caption`} label="Caption">
              <Textarea id={`${idPrefix}-caption`} rows={2} value={media.caption || ''} onChange={(e) => setMedia({ caption: e.target.value })} />
            </Field>
          )}
          {type === 'document' && (
            <Field id={`${idPrefix}-filename`} label="File name shown to customer">
              <Input id={`${idPrefix}-filename`} value={media.filename || ''} onChange={(e) => setMedia({ filename: e.target.value })} placeholder="itinerary.pdf" />
            </Field>
          )}
        </>
      )}

      {type === 'interactive' && (
        <>
          <Field id={`${idPrefix}-itype`} label="Style">
            <select id={`${idPrefix}-itype`} className={selectClass} value={inter.type || 'button'} onChange={(e) => {
              const t = e.target.value;
              const action = t === 'button' ? { buttons: [{ type: 'reply', reply: { id: '', title: '' } }] }
                : t === 'list' ? { button: 'Choose', sections: [{ title: '', rows: [{ id: '', title: '' }] }] } : inter.action || {};
              setInter({ type: t, action });
            }}>
              <option value="button">Reply buttons (up to 3)</option>
              <option value="list">List menu (up to 10 rows)</option>
              <option value="flow">WhatsApp form</option>
            </select>
          </Field>
          <Field id={`${idPrefix}-ibody`} label="Message" required>
            <Textarea id={`${idPrefix}-ibody`} rows={4} maxLength={1024} value={inter.body?.text || ''} onChange={(e) => setInter({ body: { text: e.target.value } })} />
          </Field>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Field id={`${idPrefix}-ihead`} label="Header (optional)">
              <Input id={`${idPrefix}-ihead`} maxLength={60} value={inter.header?.type === 'text' || !inter.header ? inter.header?.text || '' : ''} disabled={inter.header && inter.header.type !== 'text'}
                onChange={(e) => setInter({ header: e.target.value ? { type: 'text', text: e.target.value } : undefined })} />
            </Field>
            <Field id={`${idPrefix}-ifoot`} label="Footer (optional)">
              <Input id={`${idPrefix}-ifoot`} maxLength={60} value={inter.footer?.text || ''} onChange={(e) => setInter({ footer: e.target.value ? { text: e.target.value } : undefined })} />
            </Field>
          </div>
          {inter.type === 'list' ? <ListEditor action={inter.action || {}} onChange={(action) => setInter({ action })} />
            : inter.type === 'flow' ? <p className="text-sm text-muted-foreground">WhatsApp form settings (flow ID, screen, data) are edited with “Edit as JSON”.</p>
              : <ButtonsEditor idPrefix={idPrefix} buttons={inter.action?.buttons || []} onChange={(buttons) => setInter({ action: { ...inter.action, buttons } })} />}
        </>
      )}

      {['template', 'location', 'contacts'].includes(type) && (
        <p className="text-sm text-muted-foreground">This message type is edited with “Edit as JSON”.</p>
      )}
    </div>
  );
}

function ActionFields({ actions, onChange, onValidity }) {
  const update = (i, next) => onChange(actions.map((a, j) => (j === i ? next : a)));
  return (
    <div className="space-y-3">
      <datalist id="action-types">{Object.keys(ACTION_FIELDS).map((k) => <option key={k} value={k} />)}</datalist>
      {actions.length === 0 && <p className="text-sm text-muted-foreground">No actions yet.</p>}
      {actions.map((a, i) => {
        const fields = ACTION_FIELDS[a.action_type];
        const extra = Object.fromEntries(Object.entries(a).filter(([k]) => k !== 'action_type'));
        return (
          <fieldset key={i} className="space-y-3 rounded-lg border p-3">
            <div className="flex items-end gap-2">
              <div className="flex-1">
                <Label htmlFor={`act-${i}`} className="mb-1.5">Action {i + 1}</Label>
                <Input id={`act-${i}`} list="action-types" className="font-mono text-xs" value={a.action_type || ''} onChange={(e) => update(i, { ...a, action_type: e.target.value })} />
              </div>
              <Button type="button" size="icon" variant="ghost" aria-label={`Remove action ${i + 1}`} onClick={() => onChange(actions.filter((_, j) => j !== i))}><FiTrash2 /></Button>
            </div>
            {fields ? fields.map((f) => (
              <Field key={f.key} id={`act-${i}-${f.key}`} label={f.label}>
                {f.json ? <JsonField id={`act-${i}-${f.key}`} value={a[f.key]} onValidity={onValidity} onChange={(v) => update(i, { ...a, [f.key]: v })} />
                  : f.multiline ? <Textarea id={`act-${i}-${f.key}`} rows={3} value={a[f.key] ?? ''} onChange={(e) => update(i, { ...a, [f.key]: e.target.value })} />
                    : <Input id={`act-${i}-${f.key}`} className={f.mono ? 'font-mono text-xs' : ''} placeholder={f.placeholder} value={typeof a[f.key] === 'string' ? a[f.key] : JSON.stringify(a[f.key] ?? '')} onChange={(e) => update(i, { ...a, [f.key]: e.target.value })} />}
              </Field>
            )) : (
              <Field id={`act-${i}-params`} label="Settings" hint="Custom action — its settings are passed as-is.">
                <JsonField id={`act-${i}-params`} rows={5} value={extra} onValidity={onValidity} onChange={(v) => update(i, { action_type: a.action_type, ...(v || {}) })} />
              </Field>
            )}
          </fieldset>
        );
      })}
      <Button type="button" size="sm" variant="outline" onClick={() => onChange([...actions, { action_type: 'set_context_variable', variable_name: '', value_template: '' }])}><FiPlus /> Add action</Button>
    </div>
  );
}

function SwitchFlowFields({ config, patch, onValidity }) {
  const [flows, setFlows] = useState([]);
  useEffect(() => {
    flowsApi.list({ page_size: 100 }).then((res) => setFlows(res.data.results || res.data || [])).catch(() => setFlows([]));
  }, []);
  const known = flows.some((f) => f.name === config.target_flow_name);
  return (
    <div className="space-y-4">
      <Field id="sf-target" label="Switch to flow" required>
        <select id="sf-target" className={selectClass} value={config.target_flow_name || ''} onChange={(e) => patch('target_flow_name', e.target.value)}>
          <option value="" disabled>Choose a flow…</option>
          {config.target_flow_name && !known && <option value={config.target_flow_name}>{config.target_flow_name}</option>}
          {flows.map((f) => <option key={f.id} value={f.name}>{f.name}{f.is_active ? '' : ' (inactive)'}</option>)}
        </select>
      </Field>
      <Field id="sf-keyword" label="Keyword to pass (optional)">
        <Input id="sf-keyword" value={config.trigger_keyword_to_pass || ''} onChange={(e) => patch('trigger_keyword_to_pass', e.target.value || undefined)} />
      </Field>
      <Field id="sf-context" label="Data to carry over (JSON, optional)">
        <JsonField id="sf-context" value={config.initial_context_template} onValidity={onValidity} onChange={(v) => patch('initial_context_template', v)} placeholder={'{ "booking_reference": "{{ flow_context.booking_reference }}" }'} />
      </Field>
    </div>
  );
}

function StepForm({ stepType, config, setConfig, onValidity }) {
  const patch = (key, v) => setConfig((c) => {
    const next = { ...c, [key]: v };
    if (v === undefined) delete next[key];
    return next;
  });

  switch (stepType) {
    case 'send_message':
      return <MessageFields idPrefix="sm" value={config} onChange={setConfig} />;
    case 'question': {
      const reply = config.reply_config || {};
      const fallback = config.fallback_config || {};
      const setFallback = (k, v) => patch('fallback_config', { action: 're_prompt', ...fallback, [k]: v });
      return (
        <div className="space-y-5">
          <MessageFields idPrefix="q" value={config.message_config} onChange={(v) => patch('message_config', v)} />
          <fieldset className="space-y-3 rounded-lg border p-3">
            <legend className="px-1 text-sm font-medium">Answer</legend>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Field id="q-var" label="Save answer as" required>
                <Input id="q-var" className="font-mono text-xs" value={reply.save_to_variable || ''} onChange={(e) => patch('reply_config', { ...reply, save_to_variable: e.target.value })} />
              </Field>
              <Field id="q-expected" label="Expected answer">
                <select id="q-expected" className={selectClass} value={reply.expected_type || 'text'} onChange={(e) => patch('reply_config', { ...reply, expected_type: e.target.value })}>
                  {REPLY_TYPES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                </select>
              </Field>
            </div>
            <Field id="q-regex" label="Must match pattern (optional)">
              <Input id="q-regex" className="font-mono text-xs" value={reply.validation_regex || ''} onChange={(e) => patch('reply_config', { ...reply, validation_regex: e.target.value || undefined })} placeholder="^\d{1,2}$" />
            </Field>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_7rem]">
              <Field id="q-retry" label="If the answer is invalid, say">
                <Input id="q-retry" value={fallback.re_prompt_message_text || ''} onChange={(e) => setFallback('re_prompt_message_text', e.target.value)} placeholder="Sorry, please reply with a number." />
              </Field>
              <Field id="q-retries" label="Retries">
                <Input id="q-retries" type="number" min={0} value={fallback.max_retries ?? 2} onChange={(e) => setFallback('max_retries', Number(e.target.value))} />
              </Field>
            </div>
          </fieldset>
        </div>
      );
    }
    case 'action':
      return <ActionFields actions={Array.isArray(config.actions_to_run) ? config.actions_to_run : []} onValidity={onValidity} onChange={(v) => patch('actions_to_run', v)} />;
    case 'end_flow':
      return config.message_config ? (
        <div className="space-y-3">
          <MessageFields idPrefix="end" value={config.message_config} onChange={(v) => patch('message_config', v)} />
          <Button type="button" size="sm" variant="ghost" onClick={() => patch('message_config', undefined)}><FiTrash2 /> Remove closing message</Button>
        </div>
      ) : (
        <div className="text-sm text-muted-foreground">
          The conversation ends silently.{' '}
          <Button type="button" size="sm" variant="link" className="px-0" onClick={() => patch('message_config', defaultMessage('text'))}>Add a closing message</Button>
        </div>
      );
    case 'human_handover':
      return (
        <div className="space-y-4">
          <Field id="hh-msg" label="Tell the customer">
            <Textarea id="hh-msg" rows={3} value={config.pre_handover_message_text || ''} onChange={(e) => patch('pre_handover_message_text', e.target.value || undefined)} placeholder="Connecting you to a member of our team…" />
          </Field>
          <Field id="hh-note" label="Note for the team">
            <Input id="hh-note" value={config.notification_details || ''} onChange={(e) => patch('notification_details', e.target.value || undefined)} />
          </Field>
        </div>
      );
    case 'switch_flow':
      return <SwitchFlowFields config={config} patch={patch} onValidity={onValidity} />;
    default:
      return null;
  }
}

function validate(stepType, config) {
  if (stepType === 'send_message' && !config.message_type) return 'Choose a message type.';
  if (stepType === 'send_message' && config.message_type === 'text' && !config.text?.body?.trim()) return 'The message text is empty.';
  if (stepType === 'question' && !config.reply_config?.save_to_variable) return 'Set where to save the answer.';
  if (stepType === 'question' && !config.message_config?.message_type) return 'The question needs a message.';
  if (stepType === 'action' && !Array.isArray(config.actions_to_run)) return 'Actions must be a list.';
  if (stepType === 'switch_flow' && !config.target_flow_name) return 'Choose a flow to switch to.';
  const buttons = (stepType === 'question' ? config.message_config : config)?.interactive?.action?.buttons;
  if (buttons?.some((b) => !b.reply?.id || !b.reply?.title)) return 'Every button needs a title and a reply ID.';
  return '';
}

export default function StepConfigEditor({ isOpen, step, onClose, onSaveStep }) {
  const [name, setName] = useState('');
  const [isEntry, setIsEntry] = useState(false);
  const [config, setConfig] = useState({});
  const [jsonMode, setJsonMode] = useState(false);
  const [jsonText, setJsonText] = useState('');
  const [error, setError] = useState('');
  const [invalid, setInvalid] = useState({});
  const [saving, setSaving] = useState(false);
  const hasForm = FORM_TYPES.includes(step?.step_type);

  useEffect(() => {
    if (!step) return;
    const conf = step.config && typeof step.config === 'object' ? structuredClone(step.config) : {};
    setName(step.name || '');
    setIsEntry(!!step.is_entry_point);
    setConfig(conf);
    setJsonText(JSON.stringify(conf, null, 2));
    setJsonMode(!FORM_TYPES.includes(step.step_type));
    setError('');
    setInvalid({});
  }, [step]);

  if (!isOpen || !step) return null;

  const onValidity = (key, ok) => setInvalid((prev) => {
    if (ok === !prev[key]) return prev;
    const next = { ...prev };
    if (ok) delete next[key]; else next[key] = true;
    return next;
  });

  const parseJson = () => {
    try {
      const parsed = JSON.parse(jsonText || '{}');
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Config must be a JSON object');
      return parsed;
    } catch (e) {
      setError(`Invalid JSON: ${e.message}`);
      return null;
    }
  };

  const toggleMode = () => {
    setError('');
    if (!jsonMode) { setJsonText(JSON.stringify(config, null, 2)); setJsonMode(true); return; }
    const parsed = parseJson();
    if (parsed) { setConfig(parsed); setInvalid({}); setJsonMode(false); }
  };

  const save = async (e) => {
    e.preventDefault();
    setError('');
    const finalConfig = jsonMode ? parseJson() : config;
    if (!finalConfig) return;
    if (!name.trim()) { setError('Give the step a name.'); return; }
    const problem = validate(step.step_type, finalConfig);
    if (problem) { setError(problem); return; }
    setSaving(true);
    const result = await onSaveStep(step.id, { name: name.trim(), is_entry_point: isEntry, config: finalConfig });
    setSaving(false);
    if (result === true) onClose();
    else setError(typeof result === 'string' ? result : 'Could not save this step.');
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !saving && onClose()}>
      <DialogContent className="flex max-h-[90vh] flex-col gap-0 p-0 sm:max-w-2xl">
        <form onSubmit={save} className="flex min-h-0 flex-1 flex-col">
          <DialogHeader className="border-b p-5">
            <DialogTitle>Edit step</DialogTitle>
            <DialogDescription>{step.step_type_display || step.step_type}</DialogDescription>
          </DialogHeader>
          <div className="min-h-0 flex-1 space-y-5 overflow-y-auto p-5">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
              <Field id="step-name" label="Step name" required>
                <Input id="step-name" className="font-mono text-sm" value={name} onChange={(e) => setName(e.target.value)} />
              </Field>
              <div className="flex h-9 items-center gap-2">
                <Switch id="step-entry" checked={isEntry} onCheckedChange={setIsEntry} />
                <Label htmlFor="step-entry">Entry point</Label>
              </div>
            </div>

            {jsonMode ? (
              <Field id="step-json" label="Configuration (JSON)" hint={hasForm ? undefined : 'This step type has no form editor.'}>
                <Textarea id="step-json" rows={16} className="font-mono text-xs" value={jsonText} onChange={(e) => { setJsonText(e.target.value); setError(''); }} />
              </Field>
            ) : (
              <StepForm stepType={step.step_type} config={config} setConfig={setConfig} onValidity={onValidity} />
            )}
            {hasForm && (
              <button type="button" onClick={toggleMode} className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
                <FiCode className="size-3.5" aria-hidden /> {jsonMode ? 'Back to form' : 'Edit as JSON'}
              </button>
            )}
          </div>
          <DialogFooter className="items-center border-t p-4">
            {error && <p role="alert" className="mr-auto text-sm text-destructive">{error}</p>}
            <Button type="button" variant="outline" onClick={onClose} disabled={saving}>Cancel</Button>
            <Button type="submit" disabled={saving || Object.keys(invalid).length > 0}>{saving ? 'Saving…' : 'Save step'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

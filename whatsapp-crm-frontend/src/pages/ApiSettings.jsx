// src/pages/ApiSettings.jsx
import React, { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { FiCheckCircle, FiCopy, FiEye, FiEyeOff, FiPlus, FiRefreshCw, FiTrash2 } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import PageHeader from '@/components/app/PageHeader';
import { EmptyState, ErrorState, LoadingState } from '@/components/app/States';
import { API_BASE_URL, metaApi } from '@/lib/api';
import { apiErrorMessage, formatRelative } from '@/lib/format';

const WEBHOOK_URL = `${API_BASE_URL}/crm-api/meta/webhook/`;
const EMPTY = {
  id: null, name: '', phone_number_id: '', waba_id: '', api_version: 'v19.0',
  verify_token: '', access_token: '', app_secret: '', is_active: false,
};
const EVENT_TONE = { processed: 'text-success', error: 'text-destructive', failed: 'text-destructive', pending: 'text-warning' };

function SecretInput({ id, value, onChange, placeholder, required }) {
  const [shown, setShown] = useState(false);
  return (
    <div className="relative">
      <Input id={id} type={shown ? 'text' : 'password'} autoComplete="off" value={value} onChange={onChange} placeholder={placeholder} required={required} className="pr-10 font-mono text-xs" />
      <button type="button" onClick={() => setShown((s) => !s)} className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-muted-foreground hover:text-foreground" aria-label={shown ? 'Hide value' : 'Show value'}>
        {shown ? <FiEyeOff className="size-4" /> : <FiEye className="size-4" />}
      </button>
    </div>
  );
}

function copy(text) {
  navigator.clipboard?.writeText(text).then(() => toast.success('Copied'), () => toast.error('Could not copy'));
}

export default function ApiSettings() {
  const [configs, setConfigs] = useState([]);
  const [events, setEvents] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const pick = (c) => {
    setForm(c ? { ...EMPTY, ...c, verify_token: c.verify_token || '', access_token: '', app_secret: '' } : EMPTY);
    setFormError('');
  };

  const loadEvents = useCallback(() => {
    metaApi.latestWebhookEvents().then((res) => setEvents(res.data || [])).catch(() => setEvents([]));
  }, []);

  const load = useCallback(async (selectId) => {
    setLoading(true);
    setLoadError('');
    try {
      const res = await metaApi.getConfigs();
      const list = res.data.results || res.data || [];
      setConfigs(list);
      pick(list.find((c) => c.id === selectId) || list.find((c) => c.is_active) || list[0]);
      loadEvents();
    } catch (err) {
      setLoadError(err.response?.status === 403 ? 'Only staff accounts can view or change WhatsApp credentials.' : apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [loadEvents]);

  useEffect(() => { load(); }, [load]);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e?.target ? e.target.value : e }));

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError('');
    const payload = {
      name: form.name.trim(), phone_number_id: form.phone_number_id.trim(), waba_id: form.waba_id.trim(),
      api_version: form.api_version.trim(), verify_token: form.verify_token, is_active: form.is_active,
    };
    // Secrets are write-only: blank means "keep what's stored".
    if (form.access_token) payload.access_token = form.access_token.trim();
    if (form.app_secret) payload.app_secret = form.app_secret.trim();
    try {
      const res = form.id ? await metaApi.patchConfig(form.id, payload) : await metaApi.createConfig(payload);
      toast.success(form.id ? 'Configuration saved' : 'Configuration added');
      await load(res.data.id);
    } catch (err) {
      setFormError(apiErrorMessage(err, 'Could not save the configuration'));
    } finally {
      setSaving(false);
    }
  };

  const activate = async (c) => {
    try {
      await metaApi.setActive(c.id);
      toast.success(`${c.name} is now the active number`);
      await load(c.id);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete “${form.name}”?${form.is_active ? ' It is the active configuration — WhatsApp messages will stop until another is activated.' : ''}`)) return;
    try {
      await metaApi.deleteConfig(form.id);
      toast.success('Configuration deleted');
      await load();
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  if (loading && !configs.length) return <LoadingState label="Loading WhatsApp settings…" />;
  if (loadError) return <ErrorState message={loadError} onRetry={() => load()} />;

  const isNew = !form.id;

  return (
    <>
      <PageHeader title="WhatsApp API" description="Credentials for the WhatsApp Business number the bot sends from. Only one configuration is active at a time." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[18rem_1fr]">
        <aside className="space-y-4">
          <nav aria-label="Configurations" className="overflow-hidden rounded-xl border bg-card">
            {configs.length === 0 && <p className="p-4 text-sm text-muted-foreground">No configurations yet.</p>}
            <ul className="divide-y">
              {configs.map((c) => (
                <li key={c.id}>
                  <button type="button" onClick={() => pick(c)} aria-current={form.id === c.id ? 'true' : undefined}
                    className={`flex w-full items-start gap-2 px-4 py-3 text-left hover:bg-muted/50 ${form.id === c.id ? 'bg-muted' : ''}`}>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{c.name}</span>
                      <span className="block truncate font-mono text-xs text-muted-foreground">{c.phone_number_id}</span>
                    </span>
                    {c.is_active && <span className="rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-medium text-success">Active</span>}
                  </button>
                </li>
              ))}
            </ul>
            <button type="button" onClick={() => pick(null)} className={`flex w-full items-center gap-2 border-t px-4 py-3 text-sm text-primary hover:bg-muted/50 ${isNew ? 'bg-muted' : ''}`}>
              <FiPlus className="size-4" /> Add configuration
            </button>
          </nav>

          <div className="rounded-xl border bg-card p-4">
            <p className="text-sm font-medium">Webhook callback URL</p>
            <p className="mt-1 text-xs text-muted-foreground">Paste this and the verify token into Meta › WhatsApp › Configuration.</p>
            <div className="mt-2 flex items-center gap-1 rounded-md bg-muted px-2 py-1.5">
              <code className="min-w-0 flex-1 truncate font-mono text-xs" title={WEBHOOK_URL}>{WEBHOOK_URL}</code>
              <Button type="button" size="icon" variant="ghost" className="size-7" onClick={() => copy(WEBHOOK_URL)} aria-label="Copy webhook URL"><FiCopy className="size-3.5" /></Button>
            </div>
          </div>
        </aside>

        <div className="space-y-6">
          <form onSubmit={save} className="rounded-xl border bg-card">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4">
              <div>
                <h2 className="font-semibold">{isNew ? 'New configuration' : form.name}</h2>
                {!isNew && <p className="text-xs text-muted-foreground">Updated {formatRelative(form.updated_at)}</p>}
              </div>
              {!isNew && !form.is_active && (
                <Button type="button" size="sm" variant="outline" onClick={() => activate(form)}><FiCheckCircle /> Make active</Button>
              )}
            </div>
            <div className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Label htmlFor="mc-name" className="mb-1.5">Name <span className="text-destructive">*</span></Label>
                <Input id="mc-name" value={form.name} onChange={set('name')} placeholder="Kalai Safaris main line" required />
              </div>
              <div>
                <Label htmlFor="mc-phone" className="mb-1.5">Phone number ID <span className="text-destructive">*</span></Label>
                <Input id="mc-phone" className="font-mono text-xs" value={form.phone_number_id} onChange={set('phone_number_id')} required />
              </div>
              <div>
                <Label htmlFor="mc-waba" className="mb-1.5">WhatsApp Business Account ID <span className="text-destructive">*</span></Label>
                <Input id="mc-waba" className="font-mono text-xs" value={form.waba_id} onChange={set('waba_id')} required />
              </div>
              <div>
                <Label htmlFor="mc-access" className="mb-1.5">Access token {isNew && <span className="text-destructive">*</span>}</Label>
                <SecretInput id="mc-access" value={form.access_token} onChange={set('access_token')} required={isNew} placeholder={isNew ? 'Permanent system-user token' : 'Saved — leave blank to keep'} />
              </div>
              <div>
                <Label htmlFor="mc-secret" className="mb-1.5">App secret</Label>
                <SecretInput id="mc-secret" value={form.app_secret} onChange={set('app_secret')} placeholder={isNew ? 'Used to verify webhook signatures' : 'Saved — leave blank to keep'} />
              </div>
              <div>
                <Label htmlFor="mc-verify" className="mb-1.5">Webhook verify token <span className="text-destructive">*</span></Label>
                <SecretInput id="mc-verify" value={form.verify_token} onChange={set('verify_token')} required />
              </div>
              <div>
                <Label htmlFor="mc-version" className="mb-1.5">Graph API version <span className="text-destructive">*</span></Label>
                <Input id="mc-version" className="font-mono text-xs" value={form.api_version} onChange={set('api_version')} placeholder="v19.0" pattern="v\d+\.\d+" required />
              </div>
              {isNew && (
                <div className="flex items-center gap-2 sm:col-span-2">
                  <Switch id="mc-active" checked={form.is_active} onCheckedChange={set('is_active')} />
                  <Label htmlFor="mc-active">Make this the active configuration</Label>
                </div>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2 border-t px-5 py-3">
              {formError && <p role="alert" className="mr-auto text-sm text-destructive">{formError}</p>}
              {!isNew && <Button type="button" variant="ghost" className="text-destructive" onClick={remove}><FiTrash2 /> Delete</Button>}
              <Button type="submit" className="ml-auto" disabled={saving}>{saving ? 'Saving…' : isNew ? 'Add configuration' : 'Save changes'}</Button>
            </div>
          </form>

          <section aria-label="Recent webhook events" className="rounded-xl border bg-card">
            <div className="flex items-center justify-between border-b px-5 py-3">
              <div>
                <h2 className="font-semibold">Recent webhook events</h2>
                <p className="text-xs text-muted-foreground">If customers message the number and nothing shows here, Meta isn’t reaching the webhook.</p>
              </div>
              <Button size="icon" variant="ghost" onClick={loadEvents} aria-label="Refresh events"><FiRefreshCw /></Button>
            </div>
            {events.length === 0 ? <EmptyState title="No events received yet" /> : (
              <ul className="divide-y text-sm">
                {events.map((ev) => (
                  <li key={ev.id} className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5 px-5 py-2.5">
                    <span className="font-medium">{ev.event_type_display || ev.event_type}</span>
                    <span className={`text-xs ${EVENT_TONE[ev.processing_status] || 'text-muted-foreground'}`}>{ev.processing_status}</span>
                    <span className="ml-auto text-xs text-muted-foreground">{formatRelative(ev.received_at)}</span>
                    {ev.processing_notes && ['error', 'failed'].includes(ev.processing_status) && (
                      <p className="w-full truncate text-xs text-muted-foreground" title={ev.processing_notes}>{ev.processing_notes}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </>
  );
}

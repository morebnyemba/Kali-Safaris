// src/pages/MediaLibraryPage.jsx
import React, { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import {
  FiCopy, FiFile, FiFilm, FiImage, FiMoreHorizontal, FiMusic, FiRefreshCw, FiSmile, FiTrash2, FiUpload,
} from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import PageHeader from '@/components/app/PageHeader';
import StatusBadge from '@/components/app/StatusBadge';
import { EmptyState, ErrorState, LoadingState } from '@/components/app/States';
import { mediaAssetsApi } from '@/lib/api';
import { apiErrorMessage, formatDate } from '@/lib/format';

const TYPES = [
  { key: '', label: 'All' },
  { key: 'image', label: 'Images', icon: FiImage },
  { key: 'video', label: 'Videos', icon: FiFilm },
  { key: 'document', label: 'Documents', icon: FiFile },
  { key: 'audio', label: 'Audio', icon: FiMusic },
  { key: 'sticker', label: 'Stickers', icon: FiSmile },
];
const TYPE_ICON = Object.fromEntries(TYPES.filter((t) => t.icon).map((t) => [t.key, t.icon]));

// WhatsApp Cloud API media limits (MB) per type.
const LIMIT_MB = { image: 5, video: 16, audio: 16, document: 100, sticker: 0.5 };

const guessType = (file) => {
  if (!file) return 'document';
  if (file.type === 'image/webp') return 'sticker';
  if (file.type.startsWith('image/')) return 'image';
  if (file.type.startsWith('video/')) return 'video';
  if (file.type.startsWith('audio/')) return 'audio';
  return 'document';
};

const formatSize = (bytes) => {
  if (!bytes && bytes !== 0) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
};

const selectClass = 'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';

function UploadDialog({ open, onOpenChange, onUploaded }) {
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [type, setType] = useState('image');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (open) { setFile(null); setName(''); setType('image'); setNotes(''); setError(''); }
  }, [open]);

  const pick = (f) => {
    setFile(f);
    setError('');
    if (f) {
      setType(guessType(f));
      setName((n) => n || f.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' '));
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!file) { setError('Choose a file to upload.'); return; }
    const limit = LIMIT_MB[type];
    if (limit && file.size > limit * 1024 * 1024) {
      setError(`WhatsApp limits ${type}s to ${limit} MB — this file is ${formatSize(file.size)}.`);
      return;
    }
    const data = new FormData();
    data.append('file', file);
    data.append('name', name.trim() || file.name);
    data.append('media_type', type);
    if (notes.trim()) data.append('notes', notes.trim());
    setBusy(true);
    setError('');
    try {
      await mediaAssetsApi.create(data);
      toast.success('Uploaded — syncing with WhatsApp');
      onOpenChange(false);
      onUploaded();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Upload media</DialogTitle>
            <DialogDescription>Images, videos and documents your WhatsApp flows can send to customers.</DialogDescription>
          </DialogHeader>
          <label
            htmlFor="m-file"
            className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center text-sm hover:border-primary/50 hover:bg-muted/40"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files?.[0] || null); }}
          >
            <FiUpload className="size-6 text-muted-foreground" aria-hidden />
            {file ? (
              <span><span className="font-medium">{file.name}</span> · {formatSize(file.size)}</span>
            ) : (
              <span><span className="font-medium text-primary">Choose a file</span> or drag it here</span>
            )}
            <input id="m-file" type="file" className="sr-only" onChange={(e) => pick(e.target.files?.[0] || null)} />
          </label>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="m-name" className="mb-1.5">Name</Label>
              <Input id="m-name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="m-type" className="mb-1.5">Type</Label>
              <select id="m-type" className={selectClass} value={type} onChange={(e) => setType(e.target.value)}>
                {TYPES.filter((t) => t.key).map((t) => <option key={t.key} value={t.key}>{t.label.replace(/s$/, '')} (max {LIMIT_MB[t.key]} MB)</option>)}
              </select>
            </div>
          </div>
          <div>
            <Label htmlFor="m-notes" className="mb-1.5">Notes (optional)</Label>
            <Textarea id="m-notes" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Where is this used?" />
          </div>
          {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={busy}>{busy ? 'Uploading…' : 'Upload'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function MediaLibraryPage() {
  const [assets, setAssets] = useState([]);
  const [type, setType] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploadOpen, setUploadOpen] = useState(false);
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await mediaAssetsApi.list({ media_type: type || undefined, page_size: 100 });
      setAssets(res.data.results || res.data || []);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [type]);

  useEffect(() => { load(); }, [load]);

  const sync = async (asset) => {
    setBusyId(asset.id);
    try {
      await mediaAssetsApi.sync(asset.id);
      toast.success(`Re-syncing “${asset.name}” with WhatsApp`);
      load();
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (asset) => {
    if (!window.confirm(`Delete “${asset.name}”? Flows that send it will fail until you pick another file.`)) return;
    try {
      await mediaAssetsApi.delete(asset.id);
      toast.success('Deleted');
      setAssets((list) => list.filter((a) => a.id !== asset.id));
    } catch {
      // Interceptor shows the error.
    }
  };

  const copyId = async (asset) => {
    try {
      await navigator.clipboard.writeText(asset.whatsapp_media_id);
      toast.success('WhatsApp media ID copied');
    } catch {
      toast.error('Copy failed — select and copy the ID manually.');
    }
  };

  return (
    <>
      <PageHeader
        title="Media library"
        description="Files your WhatsApp flows send to customers. Each file is uploaded to WhatsApp so it can be sent instantly."
        actions={<Button onClick={() => setUploadOpen(true)}><FiUpload /> Upload</Button>}
      />

      <div className="-mx-1 mb-4 flex gap-1 overflow-x-auto px-1" role="tablist" aria-label="Filter by type">
        {TYPES.map((t) => (
          <Button key={t.key || 'all'} role="tab" aria-selected={type === t.key} size="sm" className="shrink-0"
            variant={type === t.key ? 'secondary' : 'ghost'} onClick={() => setType(t.key)}>
            {t.label}
          </Button>
        ))}
      </div>

      {error ? <ErrorState message={error} onRetry={load} /> : loading ? <LoadingState label="Loading media…" /> : assets.length === 0 ? (
        <div className="rounded-xl border bg-card">
          <EmptyState
            icon={FiImage}
            title={type ? `No ${TYPES.find((t) => t.key === type)?.label.toLowerCase()} yet` : 'No media yet'}
            description="Upload tour photos, brochures or videos to use them in WhatsApp flows."
            action={<Button onClick={() => setUploadOpen(true)}><FiUpload /> Upload</Button>}
          />
        </div>
      ) : (
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {assets.map((a) => {
            const Icon = TYPE_ICON[a.media_type] || FiFile;
            return (
              <li key={a.id} className="flex flex-col overflow-hidden rounded-xl border bg-card">
                <div className="flex aspect-video items-center justify-center bg-muted">
                  {a.media_type === 'image' || a.media_type === 'sticker' ? (
                    <img src={a.file_url} alt="" loading="lazy" className="size-full object-cover"
                      onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                  ) : (
                    <Icon className="size-10 text-muted-foreground" aria-hidden />
                  )}
                </div>
                <div className="flex flex-1 flex-col gap-2 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate font-medium" title={a.name}>{a.name}</p>
                      <p className="text-xs text-muted-foreground">{a.media_type_display} · {formatSize(a.file_size)} · {formatDate(a.created_at)}</p>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="-mr-2 -mt-1 shrink-0" aria-label={`Actions for ${a.name}`}><FiMoreHorizontal /></Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {a.file_url && <DropdownMenuItem asChild><a href={a.file_url} target="_blank" rel="noreferrer">Open file</a></DropdownMenuItem>}
                        {a.whatsapp_media_id && <DropdownMenuItem onClick={() => copyId(a)}><FiCopy className="size-4" /> Copy WhatsApp media ID</DropdownMenuItem>}
                        <DropdownMenuItem onClick={() => sync(a)} disabled={busyId === a.id}><FiRefreshCw className="size-4" /> Re-sync with WhatsApp</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => remove(a)} className="text-destructive focus:text-destructive"><FiTrash2 className="size-4" /> Delete</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                  <div className="mt-auto flex items-center justify-between gap-2">
                    <StatusBadge status={a.status} />
                    {a.status !== 'synced' && a.status !== 'uploading' && (
                      <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={() => sync(a)} disabled={busyId === a.id}>
                        <FiRefreshCw className={busyId === a.id ? 'animate-spin' : ''} /> Sync
                      </Button>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <UploadDialog open={uploadOpen} onOpenChange={setUploadOpen} onUploaded={load} />
    </>
  );
}

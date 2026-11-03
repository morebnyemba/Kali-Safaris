// src/pages/WebsiteGalleryPage.jsx
import React, { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { FiEdit2, FiExternalLink, FiEyeOff, FiImage, FiMoreHorizontal, FiTrash2, FiUpload } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import PageHeader from '@/components/app/PageHeader';
import { EmptyState, ErrorState, LoadingState } from '@/components/app/States';
import { galleryApi } from '@/lib/api';
import { apiErrorMessage } from '@/lib/format';

const WEBSITE_GALLERY_URL = 'https://kalaisafaris.com/gallery';

const CATEGORIES = [
  { key: 'boat', label: 'Boats & Cruises' },
  { key: 'sunset', label: 'Sunset' },
  { key: 'sunrise', label: 'Sunrise' },
  { key: 'jetty', label: 'Jetty Venue' },
];
const MAX_MB = 15;

const selectClass = 'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';

/** Year input value → API value: blank clears it. */
const yearValue = (text) => (text.trim() ? Number(text) : null);

function CategorySelect({ id, value, onChange }) {
  return (
    <select id={id} className={selectClass} value={value} onChange={(e) => onChange(e.target.value)}>
      {CATEGORIES.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
    </select>
  );
}

function YearInput({ id, value, onChange }) {
  return (
    <Input id={id} inputMode="numeric" pattern="\d{4}" maxLength={4} placeholder="e.g. 2025"
      value={value} onChange={(e) => onChange(e.target.value.replace(/\D/g, ''))} />
  );
}

function UploadDialog({ open, onOpenChange, onUploaded, defaultCategory }) {
  const [files, setFiles] = useState([]);
  const [category, setCategory] = useState('boat');
  const [caption, setCaption] = useState('');
  const [year, setYear] = useState('');
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(null);

  useEffect(() => {
    if (open) {
      setFiles([]); setCaption(''); setYear(''); setError(''); setProgress(null);
      setCategory(defaultCategory || 'boat');
    }
  }, [open, defaultCategory]);

  const pick = (list) => {
    const picked = Array.from(list || []).filter((f) => f.type.startsWith('image/'));
    setFiles(picked);
    setError(list?.length && !picked.length ? 'Only image files can go in the gallery.' : '');
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!files.length) { setError('Choose at least one photo.'); return; }
    const tooBig = files.find((f) => f.size > MAX_MB * 1024 * 1024);
    if (tooBig) { setError(`“${tooBig.name}” is over ${MAX_MB} MB. Please resize it first.`); return; }
    if (year && year.length !== 4) { setError('Year must have four digits, or be left blank.'); return; }

    setError('');
    let done = 0;
    for (const file of files) {
      setProgress({ done, total: files.length });
      const data = new FormData();
      data.append('image', file);
      data.append('category', category);
      // One caption can't describe several photos; add those per photo afterwards.
      if (files.length === 1 && caption.trim()) data.append('caption', caption.trim());
      if (year) data.append('year', year);
      try {
        await galleryApi.create(data);
        done += 1;
      } catch (err) {
        setError(`${file.name}: ${apiErrorMessage(err)}`);
        setProgress(null);
        if (done) onUploaded();
        setFiles(files.slice(done));
        return;
      }
    }
    toast.success(done === 1 ? 'Photo added to the website gallery' : `${done} photos added to the website gallery`);
    onOpenChange(false);
    onUploaded();
  };

  const busy = progress !== null;

  return (
    <Dialog open={open} onOpenChange={(v) => !busy && onOpenChange(v)}>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Add photos</DialogTitle>
            <DialogDescription>Photos appear on the website gallery as soon as they’re uploaded.</DialogDescription>
          </DialogHeader>
          <label
            htmlFor="g-files"
            className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center text-sm hover:border-primary/50 hover:bg-muted/40"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files); }}
          >
            <FiUpload className="size-6 text-muted-foreground" aria-hidden />
            {files.length ? (
              <span><span className="font-medium">{files.length === 1 ? files[0].name : `${files.length} photos selected`}</span></span>
            ) : (
              <span><span className="font-medium text-primary">Choose photos</span> or drag them here</span>
            )}
            <span className="text-xs text-muted-foreground">JPG or PNG, up to {MAX_MB} MB each</span>
            <input id="g-files" type="file" accept="image/*" multiple className="sr-only" onChange={(e) => pick(e.target.files)} />
          </label>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="g-category" className="mb-1.5">Category</Label>
              <CategorySelect id="g-category" value={category} onChange={setCategory} />
            </div>
            <div>
              <Label htmlFor="g-year" className="mb-1.5">Year <span className="font-normal text-muted-foreground">(optional)</span></Label>
              <YearInput id="g-year" value={year} onChange={setYear} />
            </div>
          </div>
          {files.length > 1 ? (
            <p className="text-xs text-muted-foreground">Uploading several photos at once? Add a caption to each one afterwards with <span className="font-medium">Edit</span>.</p>
          ) : (
            <div>
              <Label htmlFor="g-caption" className="mb-1.5">Caption <span className="font-normal text-muted-foreground">(optional)</span></Label>
              <Input id="g-caption" maxLength={200} value={caption} onChange={(e) => setCaption(e.target.value)} placeholder="e.g. Elephants crossing at sunset" />
            </div>
          )}
          {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" disabled={busy} onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={busy}>
              {busy ? `Uploading ${progress.done + 1} of ${progress.total}…` : files.length > 1 ? `Upload ${files.length} photos` : 'Upload'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function EditDialog({ photo, onOpenChange, onSaved }) {
  const [form, setForm] = useState(null);
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [filePreview, setFilePreview] = useState('');

  useEffect(() => {
    if (!file) { setFilePreview(''); return undefined; }
    const url = URL.createObjectURL(file);
    setFilePreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    if (photo) {
      setForm({
        caption: photo.caption, year: photo.year ? String(photo.year) : '', category: photo.category,
        sort_order: String(photo.sort_order), is_active: photo.is_active,
      });
      setFile(null);
      setError('');
    }
  }, [photo]);

  if (!photo || !form) return null;
  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }));

  const submit = async (e) => {
    e.preventDefault();
    if (form.year && form.year.length !== 4) { setError('Year must have four digits, or be left blank.'); return; }
    if (file && file.size > MAX_MB * 1024 * 1024) { setError(`The new photo is over ${MAX_MB} MB. Please resize it first.`); return; }
    const fields = {
      caption: form.caption.trim(), year: yearValue(form.year), category: form.category,
      sort_order: Number(form.sort_order) || 0, is_active: form.is_active,
    };
    let data = fields;
    if (file) {
      // A replacement photo has to go as multipart; blank year is sent as '' (cleared).
      data = new FormData();
      data.append('image', file);
      Object.entries(fields).forEach(([k, v]) => data.append(k, v ?? ''));
    }
    setBusy(true);
    setError('');
    try {
      const res = await galleryApi.update(photo.id, data);
      toast.success('Photo updated');
      onSaved(res.data);
      onOpenChange(false);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const preview = filePreview || photo.image_url;

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Edit photo</DialogTitle>
            <DialogDescription>Caption and year are optional. Leave them blank to hide them on the website.</DialogDescription>
          </DialogHeader>
          <div className="relative overflow-hidden rounded-lg bg-muted">
            <img src={preview} alt="" className="max-h-56 w-full object-contain" />
            <label htmlFor="g-replace" className="absolute bottom-2 right-2 inline-flex cursor-pointer items-center gap-1.5 rounded-md bg-background/90 px-2.5 py-1.5 text-xs font-medium shadow-sm hover:bg-background">
              <FiUpload className="size-3.5" aria-hidden /> {file ? 'Choose another' : 'Replace photo'}
              <input id="g-replace" type="file" accept="image/*" className="sr-only" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            </label>
          </div>
          <div>
            <Label htmlFor="g-edit-caption" className="mb-1.5">Caption <span className="font-normal text-muted-foreground">(optional)</span></Label>
            <Input id="g-edit-caption" maxLength={200} value={form.caption} onChange={(e) => set('caption')(e.target.value)} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-3 sm:col-span-1">
              <Label htmlFor="g-edit-category" className="mb-1.5">Category</Label>
              <CategorySelect id="g-edit-category" value={form.category} onChange={set('category')} />
            </div>
            <div>
              <Label htmlFor="g-edit-year" className="mb-1.5">Year</Label>
              <YearInput id="g-edit-year" value={form.year} onChange={set('year')} />
            </div>
            <div>
              <Label htmlFor="g-edit-order" className="mb-1.5">Position</Label>
              <Input id="g-edit-order" type="number" min={0} value={form.sort_order} onChange={(e) => set('sort_order')(e.target.value)} />
            </div>
          </div>
          <p className="-mt-2 text-xs text-muted-foreground">Lower positions appear first.</p>
          <label className="flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-sm">
            <span>
              <span className="block font-medium">Show on website</span>
              <span className="block text-xs text-muted-foreground">Turn off to hide it without deleting.</span>
            </span>
            <Switch checked={form.is_active} onCheckedChange={set('is_active')} />
          </label>
          {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={busy}>{busy ? 'Saving…' : 'Save'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function WebsiteGalleryPage() {
  const [photos, setPhotos] = useState([]);
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploadOpen, setUploadOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await galleryApi.list({ category: category || undefined });
      setPhotos(res.data.results || res.data || []);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => { load(); }, [load]);

  const replace = (updated) => setPhotos((list) => list.map((p) => (p.id === updated.id ? updated : p)));

  const toggleVisible = async (photo, is_active) => {
    replace({ ...photo, is_active });
    try {
      replace((await galleryApi.update(photo.id, { is_active })).data);
      toast.success(is_active ? 'Now showing on the website' : 'Hidden from the website');
    } catch {
      replace(photo); // Interceptor shows the error.
    }
  };

  const remove = async (photo) => {
    if (!window.confirm(`Delete ${photo.caption ? `“${photo.caption}”` : 'this photo'}? It will be removed from the website and can’t be recovered.`)) return;
    try {
      await galleryApi.delete(photo.id);
      toast.success('Photo deleted');
      setPhotos((list) => list.filter((p) => p.id !== photo.id));
    } catch {
      // Interceptor shows the error.
    }
  };

  const visibleCount = photos.filter((p) => p.is_active).length;

  return (
    <>
      <PageHeader
        title="Website gallery"
        description="Photos on the public website’s gallery page. Changes show on the site straight away."
        actions={(
          <>
            <Button variant="outline" asChild>
              <a href={WEBSITE_GALLERY_URL} target="_blank" rel="noreferrer"><FiExternalLink /> View gallery</a>
            </Button>
            <Button onClick={() => setUploadOpen(true)}><FiUpload /> Add photos</Button>
          </>
        )}
      />

      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="-mx-1 flex gap-1 overflow-x-auto px-1" role="tablist" aria-label="Filter by category">
          {[{ key: '', label: 'All' }, ...CATEGORIES].map((c) => (
            <Button key={c.key || 'all'} role="tab" aria-selected={category === c.key} size="sm" className="shrink-0"
              variant={category === c.key ? 'secondary' : 'ghost'} onClick={() => setCategory(c.key)}>
              {c.label}
            </Button>
          ))}
        </div>
        {!loading && !error && photos.length > 0 && (
          <p className="text-sm text-muted-foreground">
            {visibleCount} of {photos.length} showing on the website
          </p>
        )}
      </div>

      {error ? <ErrorState message={error} onRetry={load} /> : loading ? <LoadingState label="Loading photos…" /> : photos.length === 0 ? (
        <div className="rounded-xl border bg-card">
          <EmptyState
            icon={FiImage}
            title={category ? `No ${CATEGORIES.find((c) => c.key === category)?.label} photos yet` : 'No photos yet'}
            description="Add photos of the boats, sunsets and jetty to show them on the website gallery."
            action={<Button onClick={() => setUploadOpen(true)}><FiUpload /> Add photos</Button>}
          />
        </div>
      ) : (
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {photos.map((p) => (
            <li key={p.id} className={`flex flex-col overflow-hidden rounded-xl border bg-card ${p.is_active ? '' : 'opacity-70'}`}>
              <button type="button" onClick={() => setEditing(p)} className="relative aspect-[4/3] overflow-hidden bg-muted" aria-label={`Edit ${p.caption || 'photo'}`}>
                <img src={p.image_url} alt={p.caption || p.category_display} loading="lazy" className="size-full object-cover" />
                {!p.is_active && (
                  <span className="absolute left-2 top-2 inline-flex items-center gap-1 rounded-full bg-background/90 px-2 py-0.5 text-xs font-medium">
                    <FiEyeOff className="size-3" aria-hidden /> Hidden
                  </span>
                )}
              </button>
              <div className="flex flex-1 flex-col gap-2 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className={`truncate font-medium ${p.caption ? '' : 'italic text-muted-foreground'}`} title={p.caption}>{p.caption || 'No caption'}</p>
                    <p className="text-xs text-muted-foreground">{p.category_display}{p.year ? ` · ${p.year}` : ''}</p>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="-mr-2 -mt-1 shrink-0" aria-label={`Actions for ${p.caption || 'photo'}`}><FiMoreHorizontal /></Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => setEditing(p)}><FiEdit2 className="size-4" /> Edit</DropdownMenuItem>
                      <DropdownMenuItem asChild><a href={p.image_url} target="_blank" rel="noreferrer"><FiExternalLink className="size-4" /> Open full size</a></DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => remove(p)} className="text-destructive focus:text-destructive"><FiTrash2 className="size-4" /> Delete</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <label className="mt-auto flex items-center justify-between gap-2 text-sm">
                  <span className="text-muted-foreground">Show on website</span>
                  <Switch checked={p.is_active} onCheckedChange={(v) => toggleVisible(p, v)} />
                </label>
              </div>
            </li>
          ))}
        </ul>
      )}

      <UploadDialog open={uploadOpen} onOpenChange={setUploadOpen} onUploaded={load} defaultCategory={category} />
      <EditDialog photo={editing} onOpenChange={(v) => !v && setEditing(null)} onSaved={replace} />
    </>
  );
}

// src/components/bot_builder/MediaAssetSelector.jsx
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { mediaAssetsApi } from '@/lib/api';

const selectClass = 'h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs dark:bg-input/30';

/** Picks a synced media asset of one type; the flow engine sends it by `asset_pk`. */
export default function MediaAssetSelector({ id, currentAssetPk, mediaTypeFilter, onAssetSelect, disabled = false }) {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    mediaAssetsApi.list({ media_type: mediaTypeFilter, page_size: 100 })
      .then((res) => { if (!cancelled) setAssets(res.data.results || res.data || []); })
      .catch(() => { if (!cancelled) setAssets([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [mediaTypeFilter]);

  const selected = assets.find((a) => a.id === currentAssetPk);
  const missing = currentAssetPk && !loading && !selected;

  return (
    <div className="space-y-1.5">
      <select
        id={id}
        className={selectClass}
        value={currentAssetPk ?? ''}
        disabled={disabled || loading}
        onChange={(e) => onAssetSelect(e.target.value ? Number(e.target.value) : null)}
      >
        <option value="">{loading ? 'Loading…' : `Choose a ${mediaTypeFilter}…`}</option>
        {missing && <option value={currentAssetPk}>Asset #{currentAssetPk} (not found)</option>}
        {assets.map((a) => (
          <option key={a.id} value={a.id}>{a.name}{a.status !== 'synced' ? ` — ${a.status_display || a.status}` : ''}</option>
        ))}
      </select>
      {!loading && assets.length === 0 && (
        <p className="text-xs text-muted-foreground">
          No {mediaTypeFilter} files yet. <Link to="/media-library" className="text-primary hover:underline">Upload one in the media library</Link>.
        </p>
      )}
      {selected && selected.status !== 'synced' && (
        <p className="text-xs text-warning">This file isn’t synced with WhatsApp, so the message won’t send. Sync it in the media library first.</p>
      )}
    </div>
  );
}

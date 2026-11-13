import { useMemo, useState } from 'react';

/**
 * Fetch every page of a DRF list (by page number, not the absolute `next` URL, which can be http:// behind the proxy), for small catalogues that are
 * filtered in the browser (flows, gallery). Capped so a runaway table can't hang the page.
 */
export async function fetchAllPages(listFn, params = {}, { pageSize = 100, maxPages = 50 } = {}) {
  let res = await listFn({ ...params, page_size: pageSize });
  let data = res.data;
  if (Array.isArray(data)) return data;
  const all = [...(data?.results || [])];
  for (let page = 2; data?.next && page <= maxPages; page += 1) {
    res = await listFn({ ...params, page_size: pageSize, page });
    data = res.data;
    all.push(...(data?.results || []));
  }
  return all;
}

/** Page an in-memory list; goes back to page 1 when `resetKey` changes. */
export function useClientPage(items, resetKey, pageSize = 50) {
  const [page, setPage] = useState(1);
  const [lastKey, setLastKey] = useState(resetKey);
  if (resetKey !== lastKey) { setLastKey(resetKey); setPage(1); }
  const pages = Math.max(1, Math.ceil(items.length / pageSize));
  const current = Math.min(page, pages); // deleting the last row of the last page steps back
  const slice = useMemo(() => items.slice((current - 1) * pageSize, current * pageSize), [items, current, pageSize]);
  return { slice, page: current, setPage, pageSize, count: items.length };
}

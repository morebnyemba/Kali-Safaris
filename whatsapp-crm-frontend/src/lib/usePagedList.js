import { useCallback, useEffect, useRef, useState } from 'react';
import { apiErrorMessage } from '@/lib/format';

/**
 * Server-side paginated list for a DRF endpoint.
 *
 *   const list = usePagedList((params) => inquiriesApi.list({ ...params, search }), [search]);
 *   list.items, list.count, list.page, list.setPage, list.loading, list.error, list.reload()
 *
 * `fetchPage` gets { page, page_size } and returns an axios response (or the
 * data) shaped { results, count } or a plain array. Changing `deps` (filters,
 * search) goes back to page 1. Stale responses from an earlier page or filter
 * are ignored.
 */
export default function usePagedList(fetchPage, deps = [], { pageSize = 50 } = {}) {
  const [page, setPage] = useState(1);
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const requestId = useRef(0);
  const fetchRef = useRef(fetchPage);
  fetchRef.current = fetchPage;

  // New filters: back to page 1 *during render* (not in an effect), so the fetch
  // never asks for page 2 of the new filter, which DRF answers with a 404.
  const depsKey = JSON.stringify(deps);
  const [lastDepsKey, setLastDepsKey] = useState(depsKey);
  if (depsKey !== lastDepsKey) {
    setLastDepsKey(depsKey);
    setPage(1);
  }

  const load = useCallback(async ({ quiet = false } = {}) => {
    const id = ++requestId.current;
    if (!quiet) setLoading(true);
    setError('');
    try {
      const res = await fetchRef.current({ page, page_size: pageSize });
      if (id !== requestId.current) return;
      const data = res && 'data' in res && res.status !== undefined ? res.data : res;
      const results = Array.isArray(data) ? data : (data?.results || []);
      setItems(results);
      setCount(Array.isArray(data) ? results.length : (data?.count ?? results.length));
    } catch (err) {
      if (id === requestId.current) setError(apiErrorMessage(err));
    } finally {
      if (id === requestId.current) setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, ...deps]);

  useEffect(() => { load(); }, [load]);

  return { items, setItems, count, page, setPage, pageSize, loading, error, reload: load };
}

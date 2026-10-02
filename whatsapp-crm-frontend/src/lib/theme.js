import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'theme';
const media = () => window.matchMedia?.('(prefers-color-scheme: dark)');

const read = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) || 'system';
  } catch {
    return 'system';
  }
};

/** Applies 'light' | 'dark' | 'system' to <html>. Called before first render to avoid a flash. */
export function applyTheme(mode = read()) {
  const dark = mode === 'dark' || (mode === 'system' && media()?.matches);
  document.documentElement.classList.toggle('dark', Boolean(dark));
}

export function useTheme() {
  const [mode, setModeState] = useState(read);

  useEffect(() => {
    applyTheme(mode);
    if (mode !== 'system') return undefined;
    const mq = media();
    const onChange = () => applyTheme('system');
    mq?.addEventListener?.('change', onChange);
    return () => mq?.removeEventListener?.('change', onChange);
  }, [mode]);

  const setMode = useCallback((next) => {
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Storage unavailable (private mode): the choice lasts for this tab only.
    }
    setModeState(next);
  }, []);

  return { mode, setMode };
}

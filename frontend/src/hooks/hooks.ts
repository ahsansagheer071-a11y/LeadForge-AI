/**
 * Hook helpers for this app.
 */

import { useEffect, useRef, useState, type DependencyList, useMemo } from 'react';

/** Debounce a value — returns the value after ms of stability. */
export function useDebounce<T>(value: T, ms = 200): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

/** Previous value hook. */
export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T | undefined>(undefined);
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}

/** True while the document is hidden. */
export function useDocumentHidden(): boolean {
  const [hidden, setHidden] = useState(typeof document !== 'undefined' ? document.hidden : false);
  useEffect(() => {
    const onVis = () => setHidden(document.hidden);
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, []);
  return hidden;
}

/** Stable callback that runs when dependencies change. */
export function useEffectOnce(cb: () => void, deps: DependencyList = []) {
  useEffect(() => {
    cb();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

/** Boolean — true when viewport is below md (768px). */
export function useIsMobile(bp = 768): boolean {
  const isMobile = useMemo(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(`(max-width: ${bp}px)`).matches;
  }, [bp]);
  const [v, setV] = useState(isMobile);
  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${bp}px)`);
    const onChange = () => setV(mql.matches);
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, [bp]);
  return v;
}

/** Boolean — true for `lg+` (>= 1280). */
export function useIsLarge(): boolean {
  return useMedia('(min-width: 1280px)');
}

/** Generic media-query hook. */
export function useMedia(query: string): boolean {
  const match = useMemo(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  }, [query]);
  const [v, setV] = useState(match);
  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = () => setV(mql.matches);
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, [query]);
  return v;
}

/** Local-storage state hook. */
export function useLocalStorage<T>(key: string, initial: T): [T, (v: T | ((cur: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(key);
      return raw == null ? initial : (JSON.parse(raw) as T);
    } catch {
      return initial;
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch { /* ignore */ }
  }, [key, value]);
  return [value, setValue];
}

/** Outside-click detector — pass ref + (optional) enabled flag. */
export function useOutsideClick<T extends HTMLElement>(
  ref: React.RefObject<T | null>,
  enabled = true,
  handler?: () => void,
) {
  useEffect(() => {
    if (!enabled) return;
    const onClick = (e: MouseEvent) => {
      if (!ref.current) return;
      if (e.target instanceof Node && ref.current.contains(e.target)) return;
      handler?.();
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [enabled, handler, ref]);
}

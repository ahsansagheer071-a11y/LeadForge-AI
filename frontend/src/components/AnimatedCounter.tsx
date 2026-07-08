import { useEffect, useRef, useState } from 'react';
import { cn } from '@/utils';

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  decimals?: number;
  className?: string;
}

export function AnimatedCounter({ value, duration = 900, decimals = 0, className }: AnimatedCounterProps) {
  const [display, setDisplay] = useState(0);
  const startRef = useRef(0);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    const start = startRef.current;
    const diff = value - start;
    if (diff === 0) return;

    const t0 = performance.now();
    let frame: number;

    const tick = (now: number) => {
      if (!mountedRef.current) return;
      const p = Math.min((now - t0) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      const current = start + diff * eased;
      setDisplay(current);
      if (p < 1) {
        frame = requestAnimationFrame(tick);
      } else {
        startRef.current = value;
      }
    };

    frame = requestAnimationFrame(tick);
    return () => {
      mountedRef.current = false;
      cancelAnimationFrame(frame);
    };
  }, [value, duration]);

  const formatted = decimals > 0 ? display.toFixed(decimals) : Math.round(display).toLocaleString();
  return <span className={cn('tabular-nums', className)}>{formatted}</span>;
}

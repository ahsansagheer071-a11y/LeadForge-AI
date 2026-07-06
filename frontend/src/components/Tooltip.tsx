/**
 * Tooltip — accessible hover-and-focus tooltip built on CSS only
 * (no Radix). Looks premium and matches shadcn-style.
 */

import * as React from 'react';
import { cn } from '@/utils';

interface TooltipProps {
  content: React.ReactNode;
  side?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  className?: string;
  children: React.ReactElement;
}

const sideClass: Record<NonNullable<TooltipProps['side']>, string> = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-1.5',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-1.5',
  left: 'right-full top-1/2 -translate-y-1/2 mr-1.5',
  right: 'left-full top-1/2 -translate-y-1/2 ml-1.5',
};

export function Tooltip({ content, side = 'top', delay = 120, className, children }: TooltipProps) {
  const [visible, setVisible] = React.useState(false);
  const timer = React.useRef<number | null>(null);
  const childRef = React.useRef<HTMLElement | null>(null);

  const show = React.useCallback(() => {
    timer.current = window.setTimeout(() => setVisible(true), delay);
  }, [delay]);
  const hide = React.useCallback(() => {
    if (timer.current) window.clearTimeout(timer.current);
    setVisible(false);
  }, []);

  React.useEffect(() => () => {
    if (timer.current) window.clearTimeout(timer.current);
  }, []);

  const childEl = children as React.ReactElement<{
    onMouseEnter?: (e: React.MouseEvent) => void;
    onMouseLeave?: (e: React.MouseEvent) => void;
    onFocus?: (e: React.FocusEvent) => void;
    onBlur?: (e: React.FocusEvent) => void;
  }>;
  const cloned = React.cloneElement(childEl, {
    onMouseEnter: (e: React.MouseEvent) => {
      show();
      childEl.props.onMouseEnter?.(e);
    },
    onMouseLeave: (e: React.MouseEvent) => {
      hide();
      childEl.props.onMouseLeave?.(e);
    },
    onFocus: (e: React.FocusEvent) => {
      show();
      childEl.props.onFocus?.(e);
    },
    onBlur: (e: React.FocusEvent) => {
      hide();
      childEl.props.onBlur?.(e);
    },
    ref: (n: HTMLElement | null) => {
      childRef.current = n;
    },
  } as Record<string, unknown>);

  return (
    <span className="relative inline-flex">
      {cloned}
      {visible && (
        <span
          role="tooltip"
          className={cn(
            'pointer-events-none absolute z-50 whitespace-nowrap',
            'rounded-md px-2 py-1 text-[11px] font-medium',
            'bg-[var(--color-bg-elevated)] border border-[var(--color-border)] text-[var(--color-text)]',
            'shadow-[var(--shadow-pop)]',
            sideClass[side],
            className,
          )}
        >
          {content}
        </span>
      )}
    </span>
  );
}

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
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

export function Tooltip({ content, side = 'top', delay = 120, className, children }: TooltipProps) {
  const [visible, setVisible] = React.useState(false);
  const timer = React.useRef<number | null>(null);

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
  } as Record<string, unknown>);

  return (
    <span className="relative inline-flex">
      {cloned}
      {visible && (
        <span
          role="tooltip"
          className={cn(
            'pointer-events-none absolute z-50 whitespace-nowrap lf-scale-up',
            'rounded-[var(--radius-sm)] px-2.5 py-1.5 text-[11px] font-medium',
            'bg-[var(--color-glass-strong)] backdrop-blur-[var(--blur-md)] border border-[var(--color-border-strong)] text-[var(--color-text)]',
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

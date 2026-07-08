import * as React from 'react';
import { cn } from '@/utils';

interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  colorClass?: string; // e.g. 'bg-emerald-500'
}

export function ProgressBar({ value, colorClass = 'bg-[var(--color-brand)]', className, ...rest }: ProgressBarProps) {
  return (
    <div className={cn('h-2 w-full bg-[var(--color-surface-hover)] rounded-full overflow-hidden', className)} {...rest}>
      <div 
        className={cn('h-full transition-all duration-500 ease-out', colorClass)}
        style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </div>
  );
}

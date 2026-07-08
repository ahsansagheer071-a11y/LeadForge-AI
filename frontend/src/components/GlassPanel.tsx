import * as React from 'react';
import { cn } from '@/utils';

export function GlassPanel({ className, children, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div 
      className={cn(
        'bg-[var(--color-glass)] backdrop-blur-[var(--blur-md)] border border-[var(--color-glass-border)] rounded-[var(--radius-xl)] shadow-[var(--shadow-card)]', 
        className
      )} 
      {...rest}
    >
      {children}
    </div>
  );
}

import * as React from 'react';
import { cn } from '@/utils';

export const Separator = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & {
  orientation?: 'horizontal' | 'vertical';
}>(({ className, orientation = 'horizontal', ...rest }, ref) => (
  <div
    ref={ref}
    role="separator"
    aria-orientation={orientation}
    className={cn(
      'bg-[var(--color-border)] flex-shrink-0',
      orientation === 'horizontal' ? 'h-px w-full' : 'w-px h-full',
      className,
    )}
    {...rest}
  />
));
Separator.displayName = 'Separator';

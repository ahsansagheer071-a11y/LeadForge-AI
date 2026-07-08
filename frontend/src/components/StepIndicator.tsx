import * as React from 'react';
import { cn } from '@/utils';
import { Check } from 'lucide-react';

export interface Step {
  id: string;
  label: string;
  status: 'upcoming' | 'current' | 'complete' | 'error';
}

export function StepIndicator({ steps, className }: { steps: Step[], className?: string }) {
  return (
    <div className={cn("flex items-center w-full", className)}>
      {steps.map((step, idx) => {
        const isLast = idx === steps.length - 1;
        
        return (
          <React.Fragment key={step.id}>
            <div className="flex flex-col items-center gap-2 relative z-10">
              <div 
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center border-2 text-[13px] font-medium transition-colors duration-300",
                  step.status === 'complete' && "bg-[var(--color-brand)] border-[var(--color-brand)] text-white shadow-[var(--shadow-glow)]",
                  step.status === 'current' && "bg-[var(--color-surface)] border-[var(--color-brand)] text-[var(--color-brand)] shadow-[0_0_0_4px_var(--color-brand-soft)]",
                  step.status === 'upcoming' && "bg-[var(--color-surface-hover)] border-transparent text-[var(--color-text-muted)]",
                  step.status === 'error' && "bg-[var(--color-danger)] border-[var(--color-danger)] text-white shadow-[0_0_15px_rgba(220,38,38,0.3)]"
                )}
              >
                {step.status === 'complete' ? <Check className="w-4 h-4" /> : idx + 1}
              </div>
              <span className={cn(
                "text-[12px] whitespace-nowrap absolute -bottom-6",
                step.status === 'current' ? "text-[var(--color-text)] font-medium" : "text-[var(--color-text-muted)]"
              )}>
                {step.label}
              </span>
            </div>
            
            {!isLast && (
              <div className="flex-1 h-0.5 mx-2 bg-[var(--color-border)] relative">
                <div 
                  className={cn(
                    "absolute top-0 left-0 h-full transition-all duration-500",
                    step.status === 'complete' ? "w-full bg-[var(--color-brand)]" : "w-0 bg-[var(--color-brand)]"
                  )}
                />
              </div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

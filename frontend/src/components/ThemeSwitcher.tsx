import { Moon, Sun, Monitor } from 'lucide-react';
import { cn } from '@/utils';
import { useTheme, type ThemeMode } from '@/contexts/ThemeContext';

const modes: { value: ThemeMode; icon: typeof Sun; label: string }[] = [
  { value: 'dark', icon: Moon, label: 'Dark' },
  { value: 'light', icon: Sun, label: 'Light' },
  { value: 'system', icon: Monitor, label: 'System' },
];

export function ThemeSwitcher({ className }: { className?: string }) {
  const { mode, setMode } = useTheme();

  return (
    <div className={cn('flex items-center gap-1 p-0.5 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)]', className)}>
      {modes.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setMode(value)}
          className={cn(
            'flex items-center justify-center size-7 rounded-[var(--radius-sm)] transition-all duration-[var(--anim-fast)]',
            mode === value
              ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-[var(--shadow-sm)]'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]',
          )}
          aria-label={`${label} mode`}
          title={`${label} mode`}
        >
          <Icon className="size-3.5" />
        </button>
      ))}
    </div>
  );
}

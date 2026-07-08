import { scoreColour } from '@/utils';

interface ScoreGaugeProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export function ScoreGauge({ score, size = 140, strokeWidth = 10, label = 'Avg / 100' }: ScoreGaugeProps) {
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score));
  const offset = circumference * (1 - pct / 100);
  const colour = scoreColour(score);

  return (
    <div className="flex flex-col items-center justify-center" style={{ minHeight: 200 }}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--color-border)" strokeWidth={strokeWidth} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={colour}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dashoffset 0.8s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[2.25rem] font-extrabold tracking-tight" style={{ color: colour }}>
            {pct.toFixed(1)}
          </span>
          <span className="text-[11px] text-[var(--color-text-muted)] uppercase tracking-wider">{label}</span>
        </div>
      </div>
    </div>
  );
}

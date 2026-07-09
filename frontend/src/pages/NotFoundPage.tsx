import { useNavigate } from 'react-router-dom';
import { Home } from 'lucide-react';
import { LeadForgeLogo } from '@/components/LeadForgeLogo';
import { Button } from '@/components/Button';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-10 text-center relative overflow-hidden bg-[var(--color-bg)]">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] max-w-[800px] rounded-full bg-[rgba(14,165,233,0.04)] blur-[120px] pointer-events-none" />

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(255,255,255,0.03) 39px, rgba(255,255,255,0.03) 40px), repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(255,255,255,0.03) 39px, rgba(255,255,255,0.03) 40px)',
          backgroundSize: '40px 40px',
        }}
      />

      {/* Animated lost-signal rings */}
      <div className="relative z-10 mb-10">
        <div className="relative size-40 flex items-center justify-center">
          {/* Outer pulsing rings */}
          <div className="absolute inset-0 rounded-full border border-[#0ea5e9]/10 animate-ping" style={{ animationDuration: '3s' }} />
          <div className="absolute inset-4 rounded-full border border-[#0ea5e9]/15 animate-ping" style={{ animationDuration: '4s', animationDelay: '0.5s' }} />
          <div className="absolute inset-8 rounded-full border border-[#0ea5e9]/20 animate-ping" style={{ animationDuration: '5s', animationDelay: '1s' }} />

          {/* Orbital ring */}
          <div
            className="absolute inset-2 rounded-full border-2 border-transparent border-t-[#0ea5e9] border-r-[#8b5cf6] animate-spin"
            style={{ animationDuration: '6s' }}
          />
          <div
            className="absolute inset-6 rounded-full border border-transparent border-b-[#06b6d4] border-l-[#06b6d4] animate-spin"
            style={{ animationDuration: '8s', animationDirection: 'reverse' }}
          />

          {/* Central logo */}
          <div className="relative z-10 size-20 rounded-full bg-gradient-to-br from-[rgba(14,165,233,0.12)] to-[rgba(139,92,246,0.12)] border border-[rgba(14,165,233,0.3)] flex items-center justify-center shadow-[0_0_40px_rgba(14,165,233,0.15)]">
            <LeadForgeLogo variant="compact" size={36} />
          </div>

          {/* Scanline dots */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1 size-1.5 rounded-full bg-[#0ea5e9] shadow-[0_0_6px_#0ea5e9]" />
          <div className="absolute bottom-0 right-1/4 size-1 rounded-full bg-[#8b5cf6] shadow-[0_0_4px_#8b5cf6]" />
          <div className="absolute top-1/3 -right-2 size-1 rounded-full bg-[#06b6d4] shadow-[0_0_4px_#06b6d4]" />
        </div>
      </div>

      {/* Error code */}
      <div className="relative z-10">
        <h1 className="text-[clamp(4rem,10vw,7rem)] font-extrabold tracking-tight leading-none mb-2">
          <span className="bg-gradient-to-r from-[#0ea5e9] via-[#8b5cf6] to-[#06b6d4] bg-clip-text text-transparent">
            404
          </span>
        </h1>
        <h2 className="text-[22px] font-bold text-white mb-3">Signal Lost</h2>
        <p className="text-[14px] text-[var(--color-text-secondary)] max-w-md mx-auto leading-relaxed">
          The node you're looking for has drifted from the network. This route doesn't exist or has been relocated.
        </p>
      </div>

      {/* Actions */}
      <div className="relative z-10 mt-8 flex flex-col sm:flex-row items-center gap-4">
        <Button
          variant="neon"
          size="lg"
          leftIcon={<Home size={16} />}
          onClick={() => navigate('/dashboard')}
        >
          Return to Command Center
        </Button>
        <Button
          variant="glass"
          size="lg"
          onClick={() => navigate(-1)}
        >
          Go Back
        </Button>
      </div>

      {/* Footer */}
      <p className="relative z-10 mt-12 text-[10px] font-mono text-[var(--color-text-muted)] tracking-wider uppercase">
        LeadForge AI &middot; Intelligence Command
      </p>
    </div>
  );
}

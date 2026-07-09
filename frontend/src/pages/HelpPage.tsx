import { useNavigate } from 'react-router-dom';
import {
  Search, Camera, BarChart3, Shield, Globe, Eye, Download, Send,
} from 'lucide-react';
import { PremiumCard } from '@/components/PremiumCard';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';

interface WorkflowStep {
  step: number;
  title: string;
  description: string;
  icon: typeof Search;
  route: string;
  color: string;
  action: string;
}

const WORKFLOW_STEPS: WorkflowStep[] = [
  { step: 1, title: 'Discover or Create a Lead', description: 'Search Google Maps for businesses in your target market, or manually enter lead details. This is the entry point for all workflows.', icon: Search, route: '/projects', color: '#0ea5e9', action: 'Open Projects' },
  { step: 2, title: 'Capture Screenshots', description: 'Take automated screenshots of the lead\'s website — desktop and mobile views. Visual reference for analysis and website generation.', icon: Camera, route: '/projects', color: '#6366f1', action: 'Open Projects' },
  { step: 3, title: 'Run Website Analysis', description: 'Analyze the lead\'s website structure: headings, meta tags, contact info, social links, SEO fundamentals, and performance metrics.', icon: BarChart3, route: '/projects', color: '#f59e0b', action: 'Open Projects' },
  { step: 4, title: 'Generate AI Audit', description: 'AI-powered audit evaluates design, UX, branding, SEO, trust signals, and conversion readiness. Produces a score and actionable recommendations.', icon: Shield, route: '/projects', color: '#8b5cf6', action: 'Open Projects' },
  { step: 5, title: 'Generate Website', description: 'Create a premium AI-generated website for the lead. Based on their audit data and your preferences. Accessible from the Generation page.', icon: Globe, route: '/generation', color: '#06b6d4', action: 'Open Generation' },
  { step: 6, title: 'Open Preview', description: 'Preview the generated website in desktop, tablet, and mobile viewports. Review the design before downloading or deploying.', icon: Eye, route: '/preview', color: '#10b981', action: 'Open Preview' },
  { step: 7, title: 'Download ZIP Package', description: 'Download the complete website as a ZIP package containing HTML, CSS, JS, and assets. Ready for deployment or self-hosting.', icon: Download, route: '/deployment', color: '#22c55e', action: 'Open Deployment' },
  { step: 8, title: 'Generate Outreach', description: 'Create AI-crafted outreach messages — cold email, LinkedIn, WhatsApp — based on the audit findings. Convert analysis into conversations.', icon: Send, route: '/projects', color: '#22d3ee', action: 'Open Projects' },
];

export function HelpPage() {
  const navigate = useNavigate();

  return (
    <div className="space-y-8 lf-fade-in">
      {/* Header */}
      <div>
        <h1 className="lf-display text-white mb-1">Workflow <span className="lf-display-gradient">Guide</span></h1>
        <p className="text-[13px] text-[var(--color-text-secondary)] font-mono">Learn how to use the LeadForge AI platform step by step</p>
      </div>

      {/* Workflow steps */}
      <PremiumCard variant="featured" innerClassName="p-6 lg:p-8">
        <div className="relative">
          {/* Vertical connecting line */}
          <div className="absolute left-7 top-0 bottom-0 w-px bg-gradient-to-b from-[#0ea5e9] via-[#8b5cf6] via-[#06b6d4] to-[#22d3ee] opacity-20 hidden md:block" />

          <div className="space-y-8 md:space-y-0">
            {WORKFLOW_STEPS.map((step, i) => (
              <div key={step.step} className="relative md:flex items-start gap-6 md:py-6">
                {/* Step number + icon */}
                <div className="flex items-center gap-4 md:flex-col md:items-center md:w-14 shrink-0">
                  <div
                    className="relative z-10 size-14 rounded-full flex items-center justify-center shrink-0"
                    style={{
                      background: `linear-gradient(135deg, ${step.color}20, ${step.color}08)`,
                      border: `1px solid ${step.color}40`,
                      boxShadow: `0 0 20px ${step.color}20`,
                    }}
                  >
                    <step.icon size={22} style={{ color: step.color }} />
                  </div>
                  <div className="md:hidden">
                    <Badge tone="info" className="text-[9px]">Step {step.step}</Badge>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 mt-3 md:mt-0">
                  <div className="hidden md:flex items-center gap-3 mb-2">
                    <Badge tone="info" className="text-[9px]">Step {step.step}</Badge>
                    <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
                      {i < WORKFLOW_STEPS.length - 1 ? `Next: ${WORKFLOW_STEPS[i + 1].title}` : 'Final step'}
                    </span>
                  </div>
                  <h3 className="text-[16px] font-bold text-white mb-1.5">{step.title}</h3>
                  <p className="text-[13px] text-[var(--color-text-secondary)] leading-relaxed mb-3 max-w-xl">
                    {step.description}
                  </p>
                  <Button
                    size="sm"
                    variant="glass"
                    leftIcon={<step.icon size={13} />}
                    onClick={() => navigate(step.route)}
                  >
                    {step.action}
                  </Button>
                </div>

                {/* Desktop connector */}
                {i < WORKFLOW_STEPS.length - 1 && (
                  <div className="hidden md:flex items-center justify-center w-full mt-2">
                    <div className="h-6 w-px bg-gradient-to-b from-transparent via-[var(--color-border)] to-transparent opacity-30" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </PremiumCard>

      {/* Quick Reference */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PremiumCard innerClassName="p-6">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white mb-4 border-b border-[var(--color-border)] pb-3 flex items-center gap-2">
            <Globe size={13} className="text-[#0ea5e9]" /> Key Pages
          </h3>
          <div className="space-y-2.5">
            {[
              { label: 'Dashboard', path: '/dashboard', desc: 'Command center and KPIs' },
              { label: 'Projects / Leads', path: '/projects', desc: 'Lead discovery and management' },
              { label: 'Generation', path: '/generation', desc: 'AI website synthesis' },
              { label: 'Preview', path: '/preview', desc: 'Website preview studio' },
              { label: 'Deployment', path: '/deployment', desc: 'ZIP package delivery' },
              { label: 'Analytics', path: '/analytics', desc: 'Pipeline metrics and insights' },
              { label: 'History', path: '/history', desc: 'Activity timeline' },
            ].map((link) => (
              <button
                key={link.path}
                onClick={() => navigate(link.path)}
                className="w-full flex items-center justify-between p-2.5 rounded-[var(--radius-sm)] bg-[var(--color-surface-hover)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] transition-all group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="size-6 rounded-[var(--radius-sm)] bg-[rgba(14,165,233,0.1)] border border-[rgba(14,165,233,0.2)] flex items-center justify-center">
                    <Search size={11} className="text-[#0ea5e9]" />
                  </div>
                  <span className="text-[12px] font-medium text-white group-hover:text-[#0ea5e9] transition-colors">{link.label}</span>
                </div>
                <span className="text-[10px] font-mono text-[var(--color-text-muted)]">{link.desc}</span>
              </button>
            ))}
          </div>
        </PremiumCard>

        <PremiumCard innerClassName="p-6">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white mb-4 border-b border-[var(--color-border)] pb-3 flex items-center gap-2">
            <Shield size={13} className="text-[#8b5cf6]" /> Tips & Notes
          </h3>
          <div className="space-y-3">
            {[
              'Leads must be discovered or created before screenshots, analysis, or audits.',
              'Screenshots are required before website analysis can be performed.',
              'AI audit requires a completed website analysis.',
              'Website generation requires an AI audit with score data.',
              'Outreach generation requires an AI audit with findings.',
              'Preview and deployment are available after website generation.',
              'All data is persisted to your workspace and accessible across sessions.',
            ].map((tip, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <div className="size-1.5 rounded-full bg-[#0ea5e9] mt-1.5 shrink-0 shadow-[0_0_4px_#0ea5e9]" />
                <p className="text-[12px] text-[var(--color-text-secondary)] leading-relaxed">{tip}</p>
              </div>
            ))}
          </div>
        </PremiumCard>
      </div>

      {/* Disclaimer */}
      <PremiumCard variant="subtle" innerClassName="p-5 flex items-center gap-3">
        <Globe size={16} className="text-[#0ea5e9] shrink-0" />
        <p className="text-[12px] text-[var(--color-text-secondary)]">
          This guide covers all workflows available in the current version. Feature availability depends on your workspace plan and permissions.
        </p>
      </PremiumCard>
    </div>
  );
}

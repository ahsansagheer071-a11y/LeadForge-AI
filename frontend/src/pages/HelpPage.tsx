import { useNavigate } from 'react-router-dom';
import {
  Search, Camera, BarChart3, Shield, Globe, Eye, Download, Send,
} from 'lucide-react';
import { Button } from '@/components/Button';

interface WorkflowStep {
  step: number;
  title: string;
  description: string;
  icon: typeof Search;
  route: string;
  action: string;
}

const WORKFLOW_STEPS: WorkflowStep[] = [
  { step: 1, title: 'Discover or Create a Lead', description: 'Search Google Maps for businesses in your target market, or manually enter lead details. This is the entry point for all workflows.', icon: Search, route: '/projects', action: 'Open Projects' },
  { step: 2, title: 'Capture Screenshots', description: 'Take automated screenshots of the lead\'s website \u2014 desktop and mobile views. Visual reference for analysis and website generation.', icon: Camera, route: '/projects', action: 'Open Projects' },
  { step: 3, title: 'Run Website Analysis', description: 'Analyze the lead\'s website structure: headings, meta tags, contact info, social links, SEO fundamentals, and performance metrics.', icon: BarChart3, route: '/projects', action: 'Open Projects' },
  { step: 4, title: 'Generate AI Audit', description: 'AI-powered audit evaluates design, UX, branding, SEO, trust signals, and conversion readiness. Produces a score and actionable recommendations.', icon: Shield, route: '/projects', action: 'Open Projects' },
  { step: 5, title: 'Generate Website', description: 'Create a premium AI-generated website for the lead. Based on their audit data and your preferences. Accessible from the Generation page.', icon: Globe, route: '/generation', action: 'Open Generation' },
  { step: 6, title: 'Open Preview', description: 'Preview the generated website in desktop, tablet, and mobile viewports. Review the design before downloading or deploying.', icon: Eye, route: '/preview', action: 'Open Preview' },
  { step: 7, title: 'Download ZIP Package', description: 'Download the complete website as a ZIP package containing HTML, CSS, JS, and assets. Ready for deployment or self-hosting.', icon: Download, route: '/deployment', action: 'Open Deployment' },
  { step: 8, title: 'Generate Outreach', description: 'Create AI-crafted outreach messages \u2014 cold email, LinkedIn, WhatsApp \u2014 based on the audit findings. Convert analysis into conversations.', icon: Send, route: '/projects', action: 'Open Projects' },
];

const KEY_PAGES = [
  { label: 'Dashboard', path: '/dashboard', desc: 'Command center and KPIs' },
  { label: 'Projects / Leads', path: '/projects', desc: 'Lead discovery and management' },
  { label: 'Generation', path: '/generation', desc: 'AI website synthesis' },
  { label: 'Preview', path: '/preview', desc: 'Website preview studio' },
  { label: 'Deployment', path: '/deployment', desc: 'ZIP package delivery' },
  { label: 'Analytics', path: '/analytics', desc: 'Pipeline metrics and insights' },
  { label: 'History', path: '/history', desc: 'Activity timeline' },
];

const TIPS = [
  'Leads must be discovered or created before screenshots, analysis, or audits.',
  'Screenshots are required before website analysis can be performed.',
  'AI audit requires a completed website analysis.',
  'Website generation requires an AI audit with score data.',
  'Outreach generation requires an AI audit with findings.',
  'Preview and deployment are available after website generation.',
  'All data is persisted to your workspace and accessible across sessions.',
];

export function HelpPage() {
  const navigate = useNavigate();

  return (
    <div className="space-y-5 lf-fade-in">
      {/* ── Header ──────────────────────────────────────────── */}
      <div>
        <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-[var(--color-text)]">Help & Support</h1>
        <p className="text-[13px] text-[var(--color-text-secondary)] mt-0.5">Learn how to use the LeadForge AI platform step by step</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
        {/* ── Main content ────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-5">
          {/* Workflow Guide */}
          <Panel title="Workflow Guide" subtitle="Complete step-by-step process">
            <div className="space-y-0">
              {WORKFLOW_STEPS.map((step, i) => (
                <div key={step.step} className="relative">
                  <div className="flex items-start gap-4 py-3">
                    {/* Step number */}
                    <div className="flex flex-col items-center shrink-0">
                      <div className="size-8 rounded-full bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center">
                        <span className="text-[11px] font-bold text-[var(--color-brand)] font-mono">{step.step}</span>
                      </div>
                      {i < WORKFLOW_STEPS.length - 1 && (
                        <div className="w-px h-full min-h-[24px] bg-[var(--color-border)] mt-1" />
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0 pt-0.5">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <h3 className="text-[13px] font-semibold text-[var(--color-text)]">{step.title}</h3>
                          <p className="text-[12px] text-[var(--color-text-secondary)] leading-relaxed mt-0.5 max-w-lg">
                            {step.description}
                          </p>
                        </div>
                        <Button
                          size="xs"
                          variant="ghost"
                          leftIcon={<step.icon size={12} />}
                          onClick={() => navigate(step.route)}
                          className="shrink-0"
                        >
                          {step.action}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* ── Sidebar ─────────────────────────────────────── */}
        <div className="space-y-5 lg:sticky lg:top-24">
          {/* Key Pages */}
          <Panel title="Key Pages" subtitle="Quick navigation">
            <div className="space-y-1">
              {KEY_PAGES.map((link) => (
                <button
                  key={link.path}
                  onClick={() => navigate(link.path)}
                  className="w-full text-left flex items-center justify-between px-3 py-2 rounded-[var(--radius-md)] hover:bg-[var(--color-surface-hover)] transition-colors group"
                >
                  <span className="text-[12px] font-medium text-[var(--color-text-secondary)] group-hover:text-[var(--color-brand)] transition-colors">
                    {link.label}
                  </span>
                  <span className="text-[10px] font-mono text-[var(--color-text-muted)]">{link.desc}</span>
                </button>
              ))}
            </div>
          </Panel>

          {/* Tips & Notes */}
          <Panel title="Tips & Notes" subtitle="Important workflow details">
            <div className="space-y-2.5">
              {TIPS.map((tip, i) => (
                <div key={i} className="flex items-start gap-2">
                  <div className="size-1 rounded-full bg-[var(--color-brand)] mt-1.5 shrink-0" />
                  <p className="text-[12px] text-[var(--color-text-secondary)] leading-relaxed">{tip}</p>
                </div>
              ))}
            </div>
          </Panel>

          {/* Disclaimer */}
          <div className="p-3 rounded-[var(--radius-xl)] bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)]">
            <div className="flex items-start gap-2">
              <Globe size={14} className="text-[var(--color-brand)] shrink-0 mt-0.5" />
              <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
                This guide covers all workflows available in the current version. Feature availability depends on your workspace plan and permissions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Sub-component ──────────────────────────────────────────── */

function Panel({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] transition-colors hover:border-[var(--color-border-strong)]">
      <div className="px-4 py-3 border-b border-[var(--color-border)]">
        <h3 className="text-[12px] font-bold text-[var(--color-text)] font-mono uppercase tracking-wider">{title}</h3>
        {subtitle && <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{subtitle}</p>}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

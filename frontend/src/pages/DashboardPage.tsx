import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import {
  Users,
  Target,
  Bot,
  MessageSquare,
  Sparkles,
  Search,
  Download,
  ArrowRight,
  TrendingUp,
  MapPin,
  Building2,
  Zap,
  BarChart3,
  Activity,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import PremiumCard from '@/components/PremiumCard'
import AnimatedCounter from '@/components/AnimatedCounter'
import { dashboardApi } from '@/services/apiServices'
import { leadsApi } from '@/services/leadsService'
import {
  queryKeys,
  formatDateRelative,
  statusBadgeClass,
  scoreColour,
} from '@/utils'
import type { LeadStatus } from '@/types'
import '@/styles/dashboard.css'

const PIPELINE_COLORS: Record<string, string> = {
  NEW: '#3b82f6',
  SCRAPED: '#6366f1',
  ANALYZED: '#f59e0b',
  OUTREACH_READY: '#22c55e',
  CONTACTED: '#8b5cf6',
  CLOSED: '#5c5c74',
}

function getGreeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

function getUserDisplayName(fullName: string | null | undefined, email: string | undefined): string {
  if (fullName?.trim()) return fullName.trim().split(' ')[0]
  return email?.split('@')[0] ?? 'there'
}

function getAiInsight(summary: {
  total_leads: number
  high_priority_leads: number
  audited_leads: number
  outreach_generated: number
  new_leads: number
}): { title: string; body: string; cta: string; path: string } {
  if (summary.high_priority_leads > 0) {
    return {
      title: 'Priority action recommended',
      body: `You have ${summary.high_priority_leads} high-priority lead${summary.high_priority_leads !== 1 ? 's' : ''} waiting. These scored 90+ on AI audit — ideal candidates for personalized outreach today.`,
      cta: 'Review high-priority leads',
      path: '/leads',
    }
  }
  if (summary.audited_leads > summary.outreach_generated) {
    return {
      title: 'Outreach opportunity detected',
      body: `${summary.audited_leads - summary.outreach_generated} audited business${summary.audited_leads - summary.outreach_generated !== 1 ? 'es' : ''} still need outreach. Generate AI-crafted emails to convert analysis into conversations.`,
      cta: 'Generate outreach',
      path: '/outreach',
    }
  }
  if (summary.total_leads > 0 && summary.audited_leads === 0) {
    return {
      title: 'Unlock AI intelligence',
      body: 'Your pipeline has leads without AI audits. Run website analysis and scoring to uncover weaknesses, opportunities, and conversion gaps.',
      cta: 'Run AI audit',
      path: '/audit',
    }
  }
  if (summary.new_leads > 0) {
    return {
      title: 'Fresh leads need attention',
      body: `${summary.new_leads} new lead${summary.new_leads !== 1 ? 's' : ''} in your pipeline. Start with website analysis to prioritize who to contact first.`,
      cta: 'Analyze websites',
      path: '/analysis',
    }
  }
  return {
    title: 'Start building your pipeline',
    body: 'Discover businesses on Google Maps, run AI audits, and generate outreach — all from one workspace. Your next high-value lead is one search away.',
    cta: 'Discover leads',
    path: '/discover',
  }
}

function activityIcon(status: LeadStatus) {
  switch (status) {
    case 'OUTREACH_READY':
      return MessageSquare
    case 'ANALYZED':
      return Bot
    case 'CONTACTED':
      return Activity
    default:
      return Building2
  }
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ value: number; name: string; color?: string }>
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div
      style={{
        background: 'var(--color-surface-overlay)',
        border: '1px solid var(--color-border)',
        borderRadius: 10,
        padding: '10px 14px',
        fontSize: 12,
        boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
      }}
    >
      {label && (
        <div style={{ color: 'var(--color-text-muted)', marginBottom: 6, fontWeight: 500 }}>{label}</div>
      )}
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color ?? 'var(--color-text-primary)', fontWeight: 600 }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  )
}

function KpiSkeleton() {
  return (
    <div className="dash-kpi-grid">
      {[...Array(4)].map((_, i) => (
        <PremiumCard key={i}>
          <div className="dash-skeleton" style={{ height: 100 }} />
        </PremiumCard>
      ))}
    </div>
  )
}

function ChartEmpty({ icon: Icon, title, desc, cta, onCta }: {
  icon: React.ElementType
  title: string
  desc: string
  cta: string
  onCta: () => void
}) {
  return (
    <div className="dash-empty" style={{ padding: '32px 16px' }}>
      <div className="dash-empty__icon"><Icon size={22} /></div>
      <div className="dash-empty__title">{title}</div>
      <div className="dash-empty__desc">{desc}</div>
      <button type="button" className="btn btn-primary btn-sm" onClick={onCta}>{cta}</button>
    </div>
  )
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()

  const { data: summaryData, isLoading: sumLoading } = useQuery({
    queryKey: queryKeys.dashboard.summary,
    queryFn: dashboardApi.summary,
  })
  const { data: recentData, isLoading: recentLoading } = useQuery({
    queryKey: queryKeys.dashboard.recentLeads(8, 0),
    queryFn: () => dashboardApi.recentLeads(8, 0),
  })
  const { data: statusData, isLoading: statusLoading } = useQuery({
    queryKey: queryKeys.dashboard.statusDist,
    queryFn: dashboardApi.statusDistribution,
  })
  const { data: industryData, isLoading: industryLoading } = useQuery({
    queryKey: queryKeys.dashboard.industryDist,
    queryFn: dashboardApi.industryDistribution,
  })
  const { data: cityData, isLoading: cityLoading } = useQuery({
    queryKey: queryKeys.dashboard.cityDist,
    queryFn: dashboardApi.cityDistribution,
  })
  const { data: priorityData, isLoading: priorityLoading } = useQuery({
    queryKey: ['leads', 'dashboard-priority'],
    queryFn: () =>
      leadsApi.list({
        min_score: 90,
        limit: 8,
        page: 1,
        sort_by: 'score',
        sort_order: 'desc',
      }),
  })

  const summary = summaryData?.data
  const recentLeads = recentData?.data?.leads ?? []
  const priorityLeads = priorityData?.data?.items ?? []
  const displayName = getUserDisplayName(user?.full_name, user?.email)
  const insight = summary
    ? getAiInsight(summary)
    : getAiInsight({
        total_leads: 0,
        high_priority_leads: 0,
        audited_leads: 0,
        outreach_generated: 0,
        new_leads: 0,
      })

  const statusChart = (statusData?.data?.distribution ?? []).map((d) => ({
    name: d.label.replace('_', ' '),
    value: d.count,
    fill: PIPELINE_COLORS[d.label] ?? '#6366f1',
  }))
  const industryChart = (industryData?.data?.distribution ?? []).slice(0, 8).map((d) => ({
    name: d.label?.slice(0, 16) ?? 'Other',
    count: d.count,
  }))
  const cityChart = (cityData?.data?.distribution ?? []).slice(0, 7).map((d) => ({
    name: d.label?.slice(0, 14) ?? 'Other',
    count: d.count,
  }))

  const avgScore = summary?.average_lead_score ?? 0
  const scorePercent = Math.min(Math.max(avgScore, 0), 100)
  const chartsLoading = statusLoading || industryLoading || cityLoading

  return (
    <div className="page-container dash-root animate-fade-in">
      {/* ── Hero ─────────────────────────────────────────── */}
      <header className="dash-hero">
        <div>
          <div className="dash-hero__greeting">{getGreeting()}</div>
          <h1 className="dash-hero__title">{displayName}</h1>
          <div className="dash-hero__brand">LeadForge AI</div>
          <div className="dash-hero__tagline">Discover • Analyze • Convert</div>
        </div>
        <div className="dash-hero__cta">
          <button type="button" className="btn btn-primary btn-lg" onClick={() => navigate('/discover')}>
            <Search size={16} /> Discover Leads
          </button>
        </div>
      </header>

      {/* ── Executive summary ─────────────────────────────── */}
      {sumLoading ? (
        <div className="dash-exec">
          <div className="dash-loading-msg">Preparing your executive summary…</div>
        </div>
      ) : (
        <section className="dash-exec">
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>Welcome back.</div>
            <div className="dash-exec__stat">
              <AnimatedCounter value={summary?.high_priority_leads ?? 0} />
            </div>
            <div className="dash-exec__label">High Priority Leads</div>
            <div className="dash-exec__meta">
              Score 90+ · {summary?.total_leads ?? 0} total in pipeline
              {avgScore > 0 && ` · Avg score ${avgScore.toFixed(1)}`}
            </div>
          </div>
          <button type="button" className="btn btn-primary" onClick={() => navigate('/leads')}>
            Continue Working <ArrowRight size={14} />
          </button>
        </section>
      )}

      {/* ── KPI Cards (4) ─────────────────────────────────── */}
      {sumLoading ? (
        <KpiSkeleton />
      ) : (
        <section className="dash-kpi-grid" aria-label="Key metrics">
          <PremiumCard className="dash-kpi">
            <div className="dash-kpi__head">
              <span className="dash-kpi__label">Total Leads</span>
              <div className="dash-kpi__icon" style={{ background: 'rgba(37,99,235,0.12)', border: '1px solid rgba(37,99,235,0.2)' }}>
                <Users size={17} color="#2563eb" />
              </div>
            </div>
            <div className="dash-kpi__value">
              <AnimatedCounter value={summary?.total_leads ?? 0} />
            </div>
            <span className="dash-kpi__trend dash-kpi__trend--muted">
              <TrendingUp size={11} /> Pipeline total
            </span>
          </PremiumCard>

          <PremiumCard className="dash-kpi">
            <div className="dash-kpi__head">
              <span className="dash-kpi__label">High Priority</span>
              <div className="dash-kpi__icon" style={{ background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.2)' }}>
                <Target size={17} color="#22c55e" />
              </div>
            </div>
            <div className="dash-kpi__value">
              <AnimatedCounter value={summary?.high_priority_leads ?? 0} />
            </div>
            <span className="dash-kpi__trend">
              <TrendingUp size={11} /> Score ≥ 90
            </span>
          </PremiumCard>

          <PremiumCard className="dash-kpi">
            <div className="dash-kpi__head">
              <span className="dash-kpi__label">AI Audited</span>
              <div className="dash-kpi__icon" style={{ background: 'rgba(124,58,237,0.12)', border: '1px solid rgba(124,58,237,0.2)' }}>
                <Bot size={17} color="#7c3aed" />
              </div>
            </div>
            <div className="dash-kpi__value">
              <AnimatedCounter value={summary?.audited_leads ?? 0} />
            </div>
            <span className="dash-kpi__trend dash-kpi__trend--muted">
              {summary?.new_leads ?? 0} awaiting review
            </span>
          </PremiumCard>

          <PremiumCard className="dash-kpi">
            <div className="dash-kpi__head">
              <span className="dash-kpi__label">Outreach Ready</span>
              <div className="dash-kpi__icon" style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)' }}>
                <MessageSquare size={17} color="#6366f1" />
              </div>
            </div>
            <div className="dash-kpi__value">
              <AnimatedCounter value={summary?.outreach_generated ?? 0} />
            </div>
            <span className="dash-kpi__trend dash-kpi__trend--muted">
              AI-generated templates
            </span>
          </PremiumCard>
        </section>
      )}

      {/* ── Quick Actions ─────────────────────────────────── */}
      <section className="dash-actions" aria-label="Quick actions">
        <button type="button" className="dash-action-btn" onClick={() => navigate('/discover')}>
          <Search size={18} /> Discover Leads
        </button>
        <button type="button" className="dash-action-btn" onClick={() => navigate('/audit')}>
          <Bot size={18} /> Run AI Audit
        </button>
        <button type="button" className="dash-action-btn" onClick={() => navigate('/outreach')}>
          <MessageSquare size={18} /> Generate Outreach
        </button>
        <button
          type="button"
          className="dash-action-btn"
          onClick={() => leadsApi.exportCsv({ page: 1, limit: 15, sort_by: 'created_at', sort_order: 'desc' })}
        >
          <Download size={18} /> Export CSV
        </button>
      </section>

      {/* ── Analytics ─────────────────────────────────────── */}
      <section className="dash-section">
        <div className="dash-section__head">
          <div>
            <h2 className="dash-section__title">Pipeline Analytics</h2>
            <p className="dash-section__sub">Where your leads are and how they score</p>
          </div>
        </div>
        {chartsLoading ? (
          <div className="dash-loading-msg">Loading analytics…</div>
        ) : (
          <div className="dash-analytics-grid">
            {/* Lead Pipeline */}
            <div className="dash-chart-card">
              <h3 className="dash-section__title" style={{ marginBottom: 16 }}>Lead Pipeline</h3>
              {statusChart.length === 0 ? (
                <ChartEmpty
                  icon={BarChart3}
                  title="No pipeline data yet"
                  desc="Discover leads to see how they move through your funnel."
                  cta="Discover leads"
                  onCta={() => navigate('/discover')}
                />
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={statusChart}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={52}
                      outerRadius={78}
                      paddingAngle={2}
                      stroke="none"
                    >
                      {statusChart.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                    <Legend
                      iconSize={8}
                      iconType="circle"
                      wrapperStyle={{ fontSize: 11, color: 'var(--color-text-secondary)', paddingTop: 8 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Industry */}
            <div className="dash-chart-card">
              <h3 className="dash-section__title" style={{ marginBottom: 16 }}>Industry Distribution</h3>
              {industryChart.length === 0 ? (
                <ChartEmpty
                  icon={Building2}
                  title="No industry breakdown"
                  desc="Import leads to see which sectors dominate your pipeline."
                  cta="Discover leads"
                  onCta={() => navigate('/discover')}
                />
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={industryChart} barSize={18}>
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} />
                    <YAxis tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} allowDecimals={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="count" fill="#2563eb" radius={[6, 6, 0, 0]} name="Leads" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Cities */}
            <div className="dash-chart-card">
              <h3 className="dash-section__title" style={{ marginBottom: 16 }}>City Distribution</h3>
              {cityChart.length === 0 ? (
                <ChartEmpty
                  icon={MapPin}
                  title="No geographic data"
                  desc="Search by city to build a regional view of opportunities."
                  cta="Discover leads"
                  onCta={() => navigate('/discover')}
                />
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={cityChart}>
                    <defs>
                      <linearGradient id="dashCityGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.35} />
                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} />
                    <YAxis tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} allowDecimals={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area
                      type="monotone"
                      dataKey="count"
                      stroke="#2563eb"
                      fill="url(#dashCityGrad)"
                      name="Leads"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Lead Score */}
            <div className="dash-chart-card">
              <h3 className="dash-section__title" style={{ marginBottom: 8 }}>Lead Score</h3>
              <p className="dash-section__sub" style={{ marginBottom: 8 }}>Average AI quality across scored leads</p>
              {avgScore <= 0 ? (
                <ChartEmpty
                  icon={Target}
                  title="No scores yet"
                  desc="Run AI audits on your leads to generate quality scores."
                  cta="Run AI audit"
                  onCta={() => navigate('/audit')}
                />
              ) : (
                <div className="dash-score-gauge">
                  <div className="dash-score-gauge__ring">
                    <svg width="140" height="140" viewBox="0 0 140 140" aria-hidden>
                      <circle cx="70" cy="70" r="58" fill="none" stroke="var(--color-border)" strokeWidth="10" />
                      <circle
                        cx="70"
                        cy="70"
                        r="58"
                        fill="none"
                        stroke={scoreColour(avgScore)}
                        strokeWidth="10"
                        strokeLinecap="round"
                        strokeDasharray={`${(scorePercent / 100) * 364} 364`}
                        transform="rotate(-90 70 70)"
                        style={{ transition: 'stroke-dasharray 0.8s ease' }}
                      />
                    </svg>
                    <div className="dash-score-gauge__value">
                      <span className="dash-score-gauge__num" style={{ color: scoreColour(avgScore) }}>
                        <AnimatedCounter value={avgScore} decimals={1} />
                      </span>
                      <span className="dash-score-gauge__cap">Avg / 100</span>
                    </div>
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 12, textAlign: 'center' }}>
                    {summary?.high_priority_leads ?? 0} leads scored 90+
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      {/* ── High Priority + Activity row ──────────────────── */}
      <div className="dash-analytics-grid dash-section">
        {/* High Priority Leads */}
        <div>
          <div className="dash-section__head">
            <div>
              <h2 className="dash-section__title">High Priority Leads</h2>
              <p className="dash-section__sub">Top-scored opportunities</p>
            </div>
            <Link to="/leads" className="link-brand" style={{ fontSize: 12 }}>View all</Link>
          </div>
          {priorityLoading ? (
            <div className="dash-skeleton" style={{ height: 200, borderRadius: 14 }} />
          ) : priorityLeads.length === 0 ? (
            <div className="dash-chart-card">
              <div className="dash-empty">
                <div className="dash-empty__icon"><Target size={22} /></div>
                <div className="dash-empty__title">No high-priority leads yet</div>
                <div className="dash-empty__desc">
                  Leads scoring 90+ appear here after AI audit. Discover and analyze businesses to populate this view.
                </div>
                <button type="button" className="btn btn-primary btn-sm" onClick={() => navigate('/audit')}>
                  Run AI Audit
                </button>
              </div>
            </div>
          ) : (
            <div className="dash-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Business</th>
                    <th>Industry</th>
                    <th>Location</th>
                    <th>Status</th>
                    <th>Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {priorityLeads.map((lead) => (
                    <tr key={lead.id} onClick={() => navigate(`/leads/${lead.id}`)}>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{lead.name}</div>
                      </td>
                      <td>{lead.industry}</td>
                      <td>{lead.city}, {lead.country}</td>
                      <td>
                        <span className={statusBadgeClass(lead.status as LeadStatus)}>
                          {lead.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td>
                        <span className="dash-score-badge dash-score-badge--hot">HOT</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div>
          <div className="dash-section__head">
            <div>
              <h2 className="dash-section__title">Recent Activity</h2>
              <p className="dash-section__sub">Latest pipeline updates</p>
            </div>
          </div>
          {recentLoading ? (
            <div className="dash-loading-msg">Loading activity…</div>
          ) : recentLeads.length === 0 ? (
            <div className="dash-chart-card">
              <div className="dash-empty">
                <div className="dash-empty__icon"><Activity size={22} /></div>
                <div className="dash-empty__title">No activity yet</div>
                <div className="dash-empty__desc">
                  Your timeline fills as you discover and process leads.
                </div>
                <button type="button" className="btn btn-primary btn-sm" onClick={() => navigate('/discover')}>
                  Discover Leads
                </button>
              </div>
            </div>
          ) : (
            <div className="dash-chart-card">
              <div className="dash-timeline">
                {recentLeads.map((lead) => {
                  const Icon = activityIcon(lead.status as LeadStatus)
                  return (
                    <div
                      key={lead.id}
                      className="dash-timeline__item"
                      style={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/leads/${lead.id}`)}
                      onKeyDown={(e) => e.key === 'Enter' && navigate(`/leads/${lead.id}`)}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="dash-timeline__icon">
                        <Icon size={16} color="var(--dash-blue)" />
                      </div>
                      <div className="dash-timeline__body">
                        <div className="dash-timeline__title">{lead.name}</div>
                        <div className="dash-timeline__meta">
                          {lead.industry} · {lead.city}
                          {' · '}
                          <span className={statusBadgeClass(lead.status as LeadStatus)}>
                            {lead.status.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                      <div className="dash-timeline__time">{formatDateRelative(lead.created_at)}</div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── AI Insights (signature) ─────────────────────────── */}
      <section className="dash-section">
        <PremiumCard>
          <div className="dash-insights">
            <div className="dash-insights__icon">
              <Sparkles size={22} color="#818cf8" />
            </div>
            <div className="dash-insights__content">
              <div className="dash-insights__heading">
                <Zap size={14} style={{ display: 'inline', marginRight: 6, verticalAlign: -2 }} />
                AI Insights
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 6 }}>
                {insight.title}
              </div>
              <p className="dash-insights__text">{insight.body}</p>
              <button type="button" className="btn btn-primary btn-sm" onClick={() => navigate(insight.path)}>
                {insight.cta} <ArrowRight size={13} />
              </button>
            </div>
          </div>
        </PremiumCard>
      </section>
    </div>
  )
}

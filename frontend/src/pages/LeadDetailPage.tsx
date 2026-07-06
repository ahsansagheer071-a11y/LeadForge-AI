import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Globe, MapPin, Phone, Star, Building, Play, Shield, AlertTriangle, CheckCircle, Search, Camera, Send, Copy } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { projectsService, generateWebsite, auditService, analysisService, screenshotService, outreachService } from '@/services/services';
import { usePreviewStore } from '@/store';
import { formatRelative } from '@/utils';
import { toast } from 'sonner';
import type { AuditAndScoreResult, WebsiteAnalysisResponse, CaptureScreenshotResponse, OutreachResponse } from '@/types';

const statusTone: Record<string, 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral'> = {
  NEW: 'info',
  SCRAPED: 'brand',
  ANALYZED: 'warning',
  OUTREACH_READY: 'success',
  CONTACTED: 'brand',
  CLOSED: 'success',
};

const scoreTone = (cat: string): 'success' | 'warning' | 'muted' => {
  if (cat === 'Hot Lead') return 'success';
  if (cat === 'Warm Lead') return 'warning';
  return 'muted';
};

export function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setHtmlContent = usePreviewStore((s) => s.setHtmlContent);
  const [analysisResult, setAnalysisResult] = useState<WebsiteAnalysisResponse | null>(null);
  const [auditResult, setAuditResult] = useState<AuditAndScoreResult | null>(null);
  const [screenshotResult, setScreenshotResult] = useState<CaptureScreenshotResponse | null>(null);
  const [outreachResult, setOutreachResult] = useState<OutreachResponse | null>(null);

  const { data: lead, isLoading, error } = useQuery({
    queryKey: ['lead', id],
    queryFn: () => projectsService.getById(id!),
    enabled: !!id,
  });

  useEffect(() => {
    if (lead) {
      if (lead.screenshot) {
        setScreenshotResult({
          lead_id: lead.id,
          desktop_url: lead.screenshot.desktop_cloudinary_url,
          mobile_url: lead.screenshot.mobile_cloudinary_url,
          full_page_url: lead.screenshot.full_page_cloudinary_url,
        });
      }
      if (lead.outreach) {
        setOutreachResult(lead.outreach);
      }
    }
  }, [lead]);

  const generateMutation = useMutation({
    mutationFn: () => generateWebsite(id!),
    onSuccess: (html) => {
      setHtmlContent(html);
      toast.success('Website generated successfully');
      navigate('/preview');
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'Generation failed');
    },
  });

  const analysisMutation = useMutation({
    mutationFn: () => analysisService.analyzeWebsite(id!),
    onSuccess: (result) => {
      setAnalysisResult(result);
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      toast.success('Website analyzed successfully');
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'Analysis failed');
    },
  });

  const auditMutation = useMutation({
    mutationFn: () => auditService.run({ lead_id: id! }),
    onSuccess: (result) => {
      setAuditResult(result);
      toast.success(`Audit complete — Score: ${result.score.overall_score}/100 (${result.score.category})`);
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'Audit failed');
    },
  });

  const screenshotMutation = useMutation({
    mutationFn: () => screenshotService.capture({ lead_id: id! }),
    onSuccess: (result) => {
      setScreenshotResult(result);
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      toast.success('Screenshots captured successfully');
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'Screenshot capture failed');
    },
  });

  const outreachMutation = useMutation({
    mutationFn: () => outreachService.generate({ lead_id: id! }),
    onSuccess: (result) => {
      setOutreachResult(result);
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      toast.success('AI Outreach generated successfully');
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'Outreach generation failed');
    },
  });

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${label} copied to clipboard`);
    } catch {
      toast.error('Failed to copy');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton variant="rounded" width={200} height={24} />
        <Card>
          <CardContent className="p-6 space-y-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} variant="text" width="100%" height={20} />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <EmptyState
        title="Lead not found"
        message="This lead does not exist or has been removed."
        action={<Button variant="outline" onClick={() => navigate('/projects')}>Back to Projects</Button>}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/projects')}>
          <ArrowLeft className="size-4 mr-1" />
          Back
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div>
              <CardTitle className="text-lg">{lead.name}</CardTitle>
              <CardDescription>
                <Badge tone={statusTone[lead.status] ?? 'muted'}>{lead.status}</Badge>
                {lead.industry && <span className="ml-2">{lead.industry}</span>}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                leftIcon={<Play className="size-3.5" />}
                loading={generateMutation.isPending}
                onClick={() => generateMutation.mutate()}
              >
                Generate Website
              </Button>
              <Button
                size="sm"
                variant="outline"
                leftIcon={<Search className="size-3.5" />}
                loading={analysisMutation.isPending}
                onClick={() => analysisMutation.mutate()}
              >
                {analysisMutation.isPending ? 'Analyzing...' : 'Analyze Website'}
              </Button>
              <Button
                size="sm"
                variant={screenshotResult ? 'brand-soft' : 'outline'}
                leftIcon={<Camera className="size-3.5" />}
                loading={screenshotMutation.isPending}
                onClick={() => screenshotMutation.mutate()}
              >
                {screenshotMutation.isPending ? 'Capturing...' : 'Capture Screenshot'}
              </Button>
              <Button
                size="sm"
                variant={auditResult ? 'brand-soft' : 'outline'}
                leftIcon={<Shield className="size-3.5" />}
                loading={auditMutation.isPending}
                onClick={() => auditMutation.mutate()}
              >
                {auditMutation.isPending ? 'Auditing...' : 'Run Audit'}
              </Button>
              <Button
                size="sm"
                variant={outreachResult ? 'brand-soft' : 'outline'}
                leftIcon={<Send className="size-3.5" />}
                loading={outreachMutation.isPending}
                onClick={() => outreachMutation.mutate()}
              >
                {outreachMutation.isPending ? 'Generating...' : 'Generate Outreach'}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader><CardTitle>Contact</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {lead.website && (
              <div className="flex items-center gap-2 text-[13px]">
                <Globe className="size-3.5 text-[var(--color-text-muted)]" />
                <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-[var(--color-brand)] hover:underline truncate">
                  {lead.website}
                </a>
              </div>
            )}
            {lead.phone && (
              <div className="flex items-center gap-2 text-[13px]">
                <Phone className="size-3.5 text-[var(--color-text-muted)]" />
                <span>{lead.phone}</span>
              </div>
            )}
            {lead.address && (
              <div className="flex items-center gap-2 text-[13px]">
                <MapPin className="size-3.5 text-[var(--color-text-muted)]" />
                <span>{lead.address}</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-[13px]">
              <Building className="size-3.5 text-[var(--color-text-muted)]" />
              <span>{lead.city}, {lead.country}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Rating & Reviews</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {lead.rating != null && (
              <div className="flex items-center gap-2">
                <Star className="size-4 text-amber-500 fill-amber-500" />
                <span className="text-[16px] font-bold">{lead.rating.toFixed(1)}</span>
                <span className="text-[12px] text-[var(--color-text-muted)]">/ 5</span>
              </div>
            )}
            {lead.reviews_count != null && (
              <p className="text-[13px] text-[var(--color-text-muted)]">
                {lead.reviews_count} review{lead.reviews_count !== 1 ? 's' : ''}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Timeline</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="text-[13px]">
              <span className="text-[var(--color-text-muted)]">Created: </span>
              <span>{formatRelative(lead.created_at)}</span>
            </div>
            <div className="text-[13px]">
              <span className="text-[var(--color-text-muted)]">Updated: </span>
              <span>{formatRelative(lead.updated_at)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Website Analysis Results */}
      {analysisResult && (
        <>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between w-full">
                <CardTitle>Website Analysis</CardTitle>
                <Badge tone={analysisResult.https_enabled ? 'success' : 'danger'}>
                  {analysisResult.https_enabled ? 'HTTPS' : 'No HTTPS'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-x-8 gap-y-3">
              <div className="space-y-2">
                {analysisResult.page_title && (
                  <div className="text-[13px]">
                    <span className="text-[var(--color-text-muted)]">Title: </span>
                    <span>{analysisResult.page_title}</span>
                  </div>
                )}
                {analysisResult.meta_description && (
                  <div className="text-[13px]">
                    <span className="text-[var(--color-text-muted)]">Meta: </span>
                    <span className="text-[var(--color-text-muted)]">{analysisResult.meta_description}</span>
                  </div>
                )}
                {analysisResult.website_language && (
                  <div className="text-[13px]">
                    <span className="text-[var(--color-text-muted)]">Language: </span>
                    <span>{analysisResult.website_language}</span>
                  </div>
                )}
                {analysisResult.http_status_code != null && (
                  <div className="text-[13px]">
                    <span className="text-[var(--color-text-muted)]">HTTP Status: </span>
                    <span>{analysisResult.http_status_code}</span>
                  </div>
                )}
              </div>
              <div className="space-y-2">
                {analysisResult.emails.length > 0 && (
                  <div className="text-[13px]">
                    <span className="text-[var(--color-text-muted)]">Emails: </span>
                    <span>{analysisResult.emails.join(', ')}</span>
                  </div>
                )}
                {analysisResult.phone_numbers.length > 0 && (
                  <div className="text-[13px]">
                    <span className="text-[var(--color-text-muted)]">Phones: </span>
                    <span>{analysisResult.phone_numbers.join(', ')}</span>
                  </div>
                )}
                <div className="flex items-center gap-3 text-[13px]">
                  <span className={analysisResult.contact_page_exists ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]'}>
                    {analysisResult.contact_page_exists ? 'Contact page' : 'No contact page'}
                  </span>
                  <span className={analysisResult.about_page_exists ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]'}>
                    {analysisResult.about_page_exists ? 'About page' : 'No about page'}
                  </span>
                </div>
                {(
                  analysisResult.social_facebook ||
                  analysisResult.social_instagram ||
                  analysisResult.social_linkedin ||
                  analysisResult.social_twitter ||
                  analysisResult.social_youtube
                ) && (
                  <div className="text-[13px]">
                    <span className="text-[var(--color-text-muted)]">Social: </span>
                    <span>
                      {[
                        analysisResult.social_facebook,
                        analysisResult.social_instagram,
                        analysisResult.social_linkedin,
                        analysisResult.social_twitter,
                        analysisResult.social_youtube,
                      ].filter(Boolean).join(', ')}
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Technical Details</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-[20px] font-bold">{analysisResult.h1_count}</div>
                  <div className="text-[11px] text-[var(--color-text-muted)]">H1 Tags</div>
                </div>
                <div className="text-center">
                  <div className="text-[20px] font-bold">{analysisResult.h2_count}</div>
                  <div className="text-[11px] text-[var(--color-text-muted)]">H2 Tags</div>
                </div>
                <div className="text-center">
                  <div className="text-[20px] font-bold">{analysisResult.total_paragraphs}</div>
                  <div className="text-[11px] text-[var(--color-text-muted)]">Paragraphs</div>
                </div>
                <div className="text-center">
                  <div className="text-[20px] font-bold">{analysisResult.total_images}</div>
                  <div className="text-[11px] text-[var(--color-text-muted)]">Images</div>
                </div>
                <div className="text-center">
                  <div className="text-[20px] font-bold">{analysisResult.total_forms}</div>
                  <div className="text-[11px] text-[var(--color-text-muted)]">Forms</div>
                </div>
              </div>
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-[13px]">
                {analysisResult.missing_title && <span className="text-[var(--color-warning)]">Missing title tag</span>}
                {analysisResult.missing_meta_description && <span className="text-[var(--color-warning)]">Missing meta description</span>}
                {analysisResult.missing_h1 && <span className="text-[var(--color-warning)]">Missing H1 tag</span>}
                {analysisResult.html_size_kb != null && (
                  <span><span className="text-[var(--color-text-muted)]">HTML size: </span>{analysisResult.html_size_kb.toFixed(1)} KB</span>
                )}
                {analysisResult.response_time_ms != null && (
                  <span><span className="text-[var(--color-text-muted)]">Response time: </span>{analysisResult.response_time_ms.toFixed(0)} ms</span>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Screenshot Results */}
      {screenshotResult && (screenshotResult.desktop_url || screenshotResult.mobile_url || screenshotResult.full_page_url) && (
        <Card>
          <CardHeader><CardTitle>Screenshots</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              {screenshotResult.desktop_url && (
                <div>
                  <p className="text-[11px] text-[var(--color-text-muted)] mb-1.5">Desktop</p>
                  <a href={screenshotResult.desktop_url} target="_blank" rel="noopener noreferrer">
                    <img
                      src={screenshotResult.desktop_url}
                      alt="Desktop screenshot"
                      className="w-full rounded-[8px] border border-[var(--color-border)] hover:opacity-90 transition-opacity"
                    />
                  </a>
                </div>
              )}
              {screenshotResult.mobile_url && (
                <div>
                  <p className="text-[11px] text-[var(--color-text-muted)] mb-1.5">Mobile</p>
                  <a href={screenshotResult.mobile_url} target="_blank" rel="noopener noreferrer">
                    <img
                      src={screenshotResult.mobile_url}
                      alt="Mobile screenshot"
                      className="w-full rounded-[8px] border border-[var(--color-border)] hover:opacity-90 transition-opacity"
                    />
                  </a>
                </div>
              )}
              {screenshotResult.full_page_url && (
                <div>
                  <p className="text-[11px] text-[var(--color-text-muted)] mb-1.5">Full Page</p>
                  <a href={screenshotResult.full_page_url} target="_blank" rel="noopener noreferrer">
                    <img
                      src={screenshotResult.full_page_url}
                      alt="Full page screenshot"
                      className="w-full rounded-[8px] border border-[var(--color-border)] hover:opacity-90 transition-opacity"
                    />
                  </a>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Audit Results */}
      {auditResult && (
        <>
          {/* Score Section */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between w-full">
                <CardTitle>AI Score</CardTitle>
                <Badge tone={scoreTone(auditResult.score.category)}>
                  {auditResult.score.category}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-6 gap-4">
                {[
                  { label: 'Overall', value: auditResult.score.overall_score },
                  { label: 'SEO', value: auditResult.score.seo_score },
                  { label: 'UX', value: auditResult.score.ux_score },
                  { label: 'Branding', value: auditResult.score.branding_score },
                  { label: 'Trust', value: auditResult.score.trust_score },
                  { label: 'Conversion', value: auditResult.score.conversion_score },
                ].map((s) => (
                  <div key={s.label} className="text-center">
                    <div className="text-[24px] font-bold text-[var(--color-brand)]">{s.value}</div>
                    <div className="text-[11px] text-[var(--color-text-muted)]">{s.label}</div>
                  </div>
                ))}
              </div>
              {auditResult.score.explanation && (
                <p className="text-[12.5px] text-[var(--color-text-muted)] mt-3">{auditResult.score.explanation}</p>
              )}
            </CardContent>
          </Card>

          {/* Business Summary */}
          {auditResult.audit && typeof auditResult.audit === 'object' && 'Business Summary' in auditResult.audit && (
            <Card>
              <CardHeader><CardTitle>Business Summary</CardTitle></CardHeader>
              <CardContent>
                <p className="text-[13px] leading-relaxed">{String(auditResult.audit['Business Summary'])}</p>
              </CardContent>
            </Card>
          )}

          {/* Top Weaknesses */}
          {auditResult.audit && typeof auditResult.audit === 'object' && 'Top Weaknesses' in auditResult.audit && Array.isArray(auditResult.audit['Top Weaknesses']) && (
            <Card>
              <CardHeader><CardTitle>Top Weaknesses</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {(auditResult.audit['Top Weaknesses'] as Array<{ title?: string; evidence?: string; impact?: string; recommendation?: string }>).map((w, i) => (
                  <div key={i} className="p-3 rounded-[10px] bg-[var(--color-surface-hover)] space-y-1.5">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="size-3.5 text-amber-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-[13px] font-medium">{w.title ?? `Weakness #${i + 1}`}</p>
                        {w.evidence && <p className="text-[12px] text-[var(--color-text-muted)] mt-0.5">{w.evidence}</p>}
                        {w.impact && <p className="text-[12px] text-[var(--color-text-muted)] mt-0.5"><span className="font-medium">Impact:</span> {w.impact}</p>}
                        {w.recommendation && (
                          <div className="flex items-start gap-1.5 mt-1.5">
                            <CheckCircle className="size-3 text-[var(--color-brand)] mt-0.5 flex-shrink-0" />
                            <p className="text-[12px] text-[var(--color-brand)]">{w.recommendation}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Overall Summary / Verdict */}
          {auditResult.audit && typeof auditResult.audit === 'object' && 'Overall Summary' in auditResult.audit && (
            <Card>
              <CardHeader><CardTitle>Overall Summary</CardTitle></CardHeader>
              <CardContent>
                <p className="text-[13px] leading-relaxed">{String(auditResult.audit['Overall Summary'])}</p>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Outreach Results */}
      {outreachResult && (
        <Card>
          <CardHeader><CardTitle>AI Outreach</CardTitle></CardHeader>
          <CardContent className="space-y-5">
            {outreachResult.email_subject && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[12px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Email Subject</p>
                  <button
                    onClick={() => copyToClipboard(outreachResult.email_subject!, 'Subject')}
                    className="text-[var(--color-text-muted)] hover:text-[var(--color-brand)] transition-colors"
                  >
                    <Copy className="size-3.5" />
                  </button>
                </div>
                <p className="text-[13px]">{outreachResult.email_subject}</p>
              </div>
            )}

            {outreachResult.cold_email && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[12px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Cold Email</p>
                  <button
                    onClick={() => copyToClipboard(outreachResult.cold_email!, 'Cold email')}
                    className="text-[var(--color-text-muted)] hover:text-[var(--color-brand)] transition-colors"
                  >
                    <Copy className="size-3.5" />
                  </button>
                </div>
                <p className="text-[13px] whitespace-pre-wrap leading-relaxed">{outreachResult.cold_email}</p>
              </div>
            )}

            {outreachResult.followup_email && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[12px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Follow-up Email</p>
                  <button
                    onClick={() => copyToClipboard(outreachResult.followup_email!, 'Follow-up email')}
                    className="text-[var(--color-text-muted)] hover:text-[var(--color-brand)] transition-colors"
                  >
                    <Copy className="size-3.5" />
                  </button>
                </div>
                <p className="text-[13px] whitespace-pre-wrap leading-relaxed">{outreachResult.followup_email}</p>
              </div>
            )}

            {outreachResult.linkedin_message && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[12px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">LinkedIn Message</p>
                  <button
                    onClick={() => copyToClipboard(outreachResult.linkedin_message!, 'LinkedIn message')}
                    className="text-[var(--color-text-muted)] hover:text-[var(--color-brand)] transition-colors"
                  >
                    <Copy className="size-3.5" />
                  </button>
                </div>
                <p className="text-[13px] whitespace-pre-wrap leading-relaxed">{outreachResult.linkedin_message}</p>
              </div>
            )}

            {outreachResult.short_cta && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[12px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Short CTA</p>
                  <button
                    onClick={() => copyToClipboard(outreachResult.short_cta!, 'CTA')}
                    className="text-[var(--color-text-muted)] hover:text-[var(--color-brand)] transition-colors"
                  >
                    <Copy className="size-3.5" />
                  </button>
                </div>
                <p className="text-[13px]">{outreachResult.short_cta}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

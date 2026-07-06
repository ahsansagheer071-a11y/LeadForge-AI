import { ExternalLink, Mail, BookOpen, MessageCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Separator } from '@/components/Separator';

const links = [
  { icon: BookOpen, label: 'Documentation', href: '#', desc: 'Read the full LeadForge AI docs' },
  { icon: MessageCircle, label: 'Community', href: '#', desc: 'Join our Discord community' },
  { icon: Mail, label: 'Contact Support', href: '#', desc: 'Get help from the team' },
];

export function HelpPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Help & Support</h1>
        <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Resources to help you get the most out of LeadForge AI</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {links.map((link) => (
          <a key={link.label} href={link.href} className="block">
            <Card className="hover:border-[var(--color-brand-border)] transition-colors cursor-pointer">
              <CardContent className="p-5">
                <div className="size-10 rounded-[10px] bg-[var(--color-brand-soft)] flex items-center justify-center mb-3">
                  <link.icon className="size-5 text-[var(--color-brand)]" />
                </div>
                <div className="flex items-center gap-1 mb-1">
                  <span className="text-[14px] font-semibold">{link.label}</span>
                  <ExternalLink className="size-3.5 text-[var(--color-text-muted)]" />
                </div>
                <p className="text-[12px] text-[var(--color-text-muted)]">{link.desc}</p>
              </CardContent>
            </Card>
          </a>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>FAQ</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { q: 'How does AI generation work?', a: 'Enter a business URL, and LeadForge AI scrapes, analyzes, and generates a complete website using advanced AI models.' },
            { q: 'Can I customize the output?', a: 'Yes. You can regenerate, tweak the prompt, and adjust settings before deploying.' },
            { q: 'Where can I deploy?', a: 'We support Vercel, Netlify, AWS, GCP, Azure, and self-hosted options.' },
          ].map((faq, i) => (
            <div key={i}>
              <p className="text-[13px] font-medium">{faq.q}</p>
              <p className="text-[12px] text-[var(--color-text-muted)] mt-0.5">{faq.a}</p>
              {i < 2 && <Separator className="mt-3" />}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

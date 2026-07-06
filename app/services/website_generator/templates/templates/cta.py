from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class CTATemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "cta"

    def validate(self, section: SectionInfo) -> bool:
        return bool(section.heading)

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface CTASectionProps {
  heading?: string;
  subheading?: string;
  description?: string;
  buttons?: Array<{ text: string; url: string }>;
  layout?: string;
}

export const CTASection: React.FC<CTASectionProps> = ({
  heading,
  subheading,
  description,
  buttons = [],
}) => {
  return (
    <section className="w-full py-20 md:py-28">
      <div className="container px-4 md:px-6">
        <div className="relative overflow-hidden rounded-2xl bg-primary px-8 py-16 md:px-16 md:py-24 text-center">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_hsl(var(--primary-foreground)/0.15),transparent_50%)]" />
          <div className="relative space-y-6 max-w-2xl mx-auto">
            {subheading && (
              <p className="text-sm font-medium uppercase tracking-wider text-primary-foreground/70">
                {subheading}
              </p>
            )}
            <h2 className="text-3xl font-bold tracking-tight text-primary-foreground sm:text-4xl md:text-5xl">
              {heading || "Ready to Get Started?"}
            </h2>
            {description && (
              <p className="text-primary-foreground/80 text-lg mx-auto max-w-lg">
                {description}
              </p>
            )}
            <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
              {buttons.length > 0 ? buttons.map((btn, i) => (
                <a
                  key={i}
                  href={btn.url || "#"}
                  className={`inline-flex h-11 items-center justify-center rounded-md px-8 text-sm font-medium transition-all ${
                    i === 0
                      ? "bg-background text-foreground shadow hover:bg-background/90"
                      : "border border-primary-foreground/20 text-primary-foreground hover:bg-primary-foreground/10"
                  }`}
                >
                  {btn.text}
                </a>
              )) : (
                <a
                  href="#"
                  className="inline-flex h-11 items-center justify-center rounded-md bg-background text-foreground px-8 text-sm font-medium shadow hover:bg-background/90 transition-all"
                >
                  Get Started
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""

from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class HeroTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "hero"

    def validate(self, section: SectionInfo) -> bool:
        return bool(section.heading)

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface HeroSectionProps {
  heading?: string;
  subheading?: string;
  description?: string;
  buttons?: Array<{ text: string; url: string }>;
  layout?: string;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  heading,
  subheading,
  description,
  buttons = [],
}) => {
  return (
    <section className="w-full py-24 md:py-32 lg:py-40">
      <div className="container px-4 md:px-6">
        <div className="flex flex-col items-center space-y-6 text-center">
          <div className="space-y-4 max-w-3xl">
            {subheading && (
              <p className="inline-flex items-center rounded-full border px-4 py-1.5 text-xs font-medium text-muted-foreground">
                {subheading}
              </p>
            )}
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
              {heading || "Lead Generation Reimagined"}
            </h1>
            {description && (
              <p className="mx-auto max-w-[700px] text-muted-foreground text-lg md:text-xl">
                {description}
              </p>
            )}
          </div>
          {buttons.length > 0 && (
            <div className="flex flex-wrap items-center justify-center gap-4">
              {buttons.map((btn, i) => (
                <a
                  key={i}
                  href={btn.url || "#"}
                  className={`inline-flex h-11 items-center justify-center rounded-md px-8 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                    i === 0
                      ? "bg-primary text-primary-foreground shadow hover:bg-primary/90"
                      : "border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                  }`}
                >
                  {btn.text}
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
"""

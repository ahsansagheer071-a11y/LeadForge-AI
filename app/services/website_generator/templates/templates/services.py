from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class ServicesTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "services"

    def validate(self, section: SectionInfo) -> bool:
        return bool(section.heading)

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface ServicesSectionProps {
  heading?: string;
  subheading?: string;
  description?: string;
  layout?: string;
}

export const ServicesSection: React.FC<ServicesSectionProps> = ({
  heading,
  subheading,
  description,
}) => {
  const items = [
    { title: "AI Lead Scoring", description: "Machine learning models rank leads by conversion probability in real-time.", icon: "01" },
    { title: "Smart Enrichment", description: "Automatically enrich lead data from 50+ public sources.", icon: "02" },
    { title: "Intent Detection", description: "Identify buying signals with natural language processing.", icon: "03" },
  ];
  return (
    <section className="w-full py-20 md:py-28 bg-muted/30">
      <div className="container px-4 md:px-6">
        <div className="mx-auto max-w-3xl text-center space-y-4 mb-16">
          {subheading && (
            <p className="text-sm font-medium uppercase tracking-wider text-primary">
              {subheading}
            </p>
          )}
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            {heading || "Our Services"}
          </h2>
          {description && (
            <p className="text-muted-foreground text-lg">{description}</p>
          )}
        </div>
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {items.map((item, i) => (
            <div
              key={i}
              className="group relative overflow-hidden rounded-xl border bg-background p-8 transition-all hover:shadow-lg hover:-translate-y-1"
            >
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-sm font-bold text-primary">
                {item.icon}
              </div>
              <h3 className="mb-3 text-xl font-semibold">{item.title}</h3>
              <p className="text-muted-foreground leading-relaxed">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
"""

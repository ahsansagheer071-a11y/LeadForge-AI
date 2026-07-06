from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class PortfolioTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "portfolio"

    def validate(self, section: SectionInfo) -> bool:
        return bool(section.heading)

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface PortfolioSectionProps {
  heading?: string;
  subheading?: string;
  description?: string;
  layout?: string;
}

export const PortfolioSection: React.FC<PortfolioSectionProps> = ({
  heading,
  subheading,
  description,
}) => {
  const items = [
    { title: "SaaS Platform", category: "Web App", image: null },
    { title: "E-commerce Suite", category: "Full Stack", image: null },
    { title: "Analytics Dashboard", category: "Data", image: null },
  ];
  return (
    <section className="w-full py-20 md:py-28">
      <div className="container px-4 md:px-6">
        <div className="mx-auto max-w-3xl text-center space-y-4 mb-16">
          {subheading && (
            <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
              {subheading}
            </p>
          )}
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            {heading || "Our Work"}
          </h2>
          {description && (
            <p className="text-muted-foreground text-lg">{description}</p>
          )}
        </div>
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {items.map((item, i) => (
            <div
              key={i}
              className="group relative overflow-hidden rounded-xl border bg-background transition-all hover:shadow-lg"
            >
              <div className="aspect-[4/3] bg-muted flex items-center justify-center">
                <span className="text-muted-foreground text-sm">{item.category}</span>
              </div>
              <div className="p-6">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                  {item.category}
                </p>
                <h3 className="text-xl font-semibold">{item.title}</h3>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
"""

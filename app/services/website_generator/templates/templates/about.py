from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class AboutTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "about"

    def validate(self, section: SectionInfo) -> bool:
        return bool(section.heading)

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface AboutSectionProps {
  heading?: string;
  subheading?: string;
  description?: string;
  layout?: string;
}

export const AboutSection: React.FC<AboutSectionProps> = ({
  heading,
  subheading,
  description,
}) => {
  return (
    <section className="w-full py-20 md:py-28">
      <div className="container px-4 md:px-6">
        <div className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
          <div className="space-y-6">
            {subheading && (
              <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
                {subheading}
              </p>
            )}
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
              {heading || "About Us"}
            </h2>
            <div className="h-1 w-16 rounded-full bg-primary" />
            {description && (
              <p className="text-muted-foreground text-lg leading-relaxed">
                {description}
              </p>
            )}
          </div>
          <div className="relative aspect-video rounded-xl bg-muted" />
        </div>
      </div>
    </section>
  );
};
"""

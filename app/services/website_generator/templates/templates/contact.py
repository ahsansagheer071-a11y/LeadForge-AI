from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class ContactTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "contact"

    def validate(self, section: SectionInfo) -> bool:
        return bool(section.heading)

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface ContactSectionProps {
  heading?: string;
  subheading?: string;
  description?: string;
  layout?: string;
}

export const ContactSection: React.FC<ContactSectionProps> = ({
  heading,
  subheading,
  description,
}) => {
  return (
    <section className="w-full py-20 md:py-28">
      <div className="container px-4 md:px-6">
        <div className="mx-auto max-w-3xl text-center space-y-4 mb-12">
          {subheading && (
            <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
              {subheading}
            </p>
          )}
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            {heading || "Get In Touch"}
          </h2>
          {description && (
            <p className="text-muted-foreground text-lg">{description}</p>
          )}
        </div>
        <div className="mx-auto max-w-lg">
          <form className="space-y-6">
            <div className="grid gap-6 sm:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="name" className="text-sm font-medium">Name</label>
                <input
                  id="name"
                  placeholder="John Doe"
                  className="flex h-11 w-full rounded-md border border-input bg-background px-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">Email</label>
                <input
                  id="email"
                  type="email"
                  placeholder="john@example.com"
                  className="flex h-11 w-full rounded-md border border-input bg-background px-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label htmlFor="message" className="text-sm font-medium">Message</label>
              <textarea
                id="message"
                placeholder="Tell us about your project..."
                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-4 py-3 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            <button
              type="submit"
              className="inline-flex h-11 w-full items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Send Message
            </button>
          </form>
        </div>
      </div>
    </section>
  );
};
"""

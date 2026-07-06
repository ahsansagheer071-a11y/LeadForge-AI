from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class FAQTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "faq"

    def validate(self, section: SectionInfo) -> bool:
        return bool(section.heading)

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface FAQSectionProps {
  heading?: string;
  subheading?: string;
  description?: string;
  layout?: string;
}

export const FAQSection: React.FC<FAQSectionProps> = ({
  heading,
  subheading,
  description,
}) => {
  const faqs = [
    { q: "How does AI lead scoring work?", a: "Our machine learning models analyze historical conversion data and lead attributes to assign a probability score to each lead." },
    { q: "Can I integrate with my CRM?", a: "Yes, we offer native integrations with Salesforce, HubSpot, and Zapier for hundreds of other tools." },
    { q: "Is my data secure?", a: "All data is encrypted at rest and in transit. We are SOC 2 compliant and follow industry best practices." },
    { q: "What kind of support do you offer?", a: "All plans include email support. Growth and Enterprise plans include priority support with dedicated account managers." },
  ];
  return (
    <section className="w-full py-20 md:py-28">
      <div className="container px-4 md:px-6 max-w-4xl mx-auto">
        <div className="mx-auto max-w-3xl text-center space-y-4 mb-16">
          {subheading && (
            <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
              {subheading}
            </p>
          )}
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            {heading || "Frequently Asked Questions"}
          </h2>
          {description && (
            <p className="text-muted-foreground text-lg">{description}</p>
          )}
        </div>
        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <details
              key={i}
              className="group rounded-xl border bg-background transition-all hover:shadow-sm [&[open]]:shadow-md"
            >
              <summary className="flex cursor-pointer items-center justify-between p-6 font-medium text-lg">
                {faq.q}
                <span className="ml-4 text-muted-foreground transition-transform group-open:rotate-45 text-2xl leading-none">
                  +
                </span>
              </summary>
              <div className="px-6 pb-6 pt-0 text-muted-foreground leading-relaxed">
                {faq.a}
              </div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
};
"""

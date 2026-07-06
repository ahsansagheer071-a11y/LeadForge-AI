from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class PricingTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "pricing"

    def validate(self, section: SectionInfo) -> bool:
        return bool(section.heading)

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface PricingSectionProps {
  heading?: string;
  subheading?: string;
  description?: string;
  layout?: string;
}

export const PricingSection: React.FC<PricingSectionProps> = ({
  heading,
  subheading,
  description,
}) => {
  const plans = [
    { name: "Starter", price: "$49", description: "Perfect for small teams.", features: ["1,000 leads/mo", "Basic scoring", "Email support"], popular: false },
    { name: "Growth", price: "$149", description: "For growing businesses.", features: ["10,000 leads/mo", "AI scoring", "Priority support", "API access"], popular: true },
    { name: "Enterprise", price: "Custom", description: "For large organizations.", features: ["Unlimited leads", "Custom models", "Dedicated support", "SLA"], popular: false },
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
            {heading || "Pricing"}
          </h2>
          {description && (
            <p className="text-muted-foreground text-lg">{description}</p>
          )}
        </div>
        <div className="grid gap-8 lg:grid-cols-3 max-w-5xl mx-auto">
          {plans.map((plan, i) => (
            <div
              key={i}
              className={`relative flex flex-col rounded-2xl border p-8 transition-all hover:shadow-lg ${
                plan.popular ? "border-primary shadow-md scale-105" : "bg-background"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-1 text-xs font-medium text-primary-foreground">
                  Most Popular
                </div>
              )}
              <div className="mb-6">
                <h3 className="text-xl font-semibold mb-1">{plan.name}</h3>
                <p className="text-muted-foreground text-sm">{plan.description}</p>
              </div>
              <div className="mb-6">
                <span className="text-4xl font-bold">{plan.price}</span>
                {plan.price !== "Custom" && <span className="text-muted-foreground ml-1">/mo</span>}
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((f, j) => (
                  <li key={j} className="flex items-center gap-2 text-sm">
                    <span className="h-4 w-4 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs">&check;</span>
                    {f}
                  </li>
                ))}
              </ul>
              <a
                href="#"
                className={`inline-flex h-11 items-center justify-center rounded-md px-8 text-sm font-medium transition-colors ${
                  plan.popular
                    ? "bg-primary text-primary-foreground shadow hover:bg-primary/90"
                    : "border border-input bg-background hover:bg-accent"
                }`}
              >
                {plan.popular ? "Get Started" : "Learn More"}
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
"""

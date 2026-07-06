from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class TestimonialsTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "testimonials"

    def validate(self, section: SectionInfo) -> bool:
        return bool(section.heading)

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface TestimonialsSectionProps {
  heading?: string;
  subheading?: string;
  description?: string;
  layout?: string;
}

export const TestimonialsSection: React.FC<TestimonialsSectionProps> = ({
  heading,
  subheading,
  description,
}) => {
  const testimonials = [
    { name: "Sarah Chen", role: "VP of Sales", company: "TechScale Inc.", content: "LeadForge AI transformed our lead qualification process. We saw a 3x increase in conversion rates within the first month.", rating: 5 },
    { name: "Marcus Rodriguez", role: "CEO", company: "GrowthWorks", content: "The AI-powered insights have been a game changer for our sales team. Highly recommended for any B2B organization.", rating: 5 },
    { name: "Emily Watson", role: "Marketing Director", company: "DataFlow Corp", content: "We've tried many lead generation tools, but none compare to the accuracy and depth of LeadForge AI.", rating: 5 },
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
            {heading || "What Our Clients Say"}
          </h2>
          {description && (
            <p className="text-muted-foreground text-lg">{description}</p>
          )}
        </div>
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {testimonials.map((t, i) => (
            <div
              key={i}
              className="relative rounded-xl border bg-background p-8 transition-all hover:shadow-lg"
            >
              <div className="flex gap-1 mb-4">
                {Array.from({ length: 5 }).map((_, j) => (
                  <span key={j} className={`h-4 w-4 ${j < t.rating ? "text-yellow-500" : "text-muted"}`}>
                    &#9733;
                  </span>
                ))}
              </div>
              <blockquote className="text-muted-foreground leading-relaxed mb-6">
                &ldquo;{t.content}&rdquo;
              </blockquote>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold text-primary">
                  {t.name.split(" ").map(n => n[0]).join("")}
                </div>
                <div>
                  <p className="text-sm font-semibold">{t.name}</p>
                  <p className="text-xs text-muted-foreground">{t.role}, {t.company}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
"""

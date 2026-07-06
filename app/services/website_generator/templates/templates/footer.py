from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class FooterTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "footer"

    def validate(self, section: SectionInfo) -> bool:
        return True

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';

interface FooterSectionProps {
  heading?: string;
  description?: string;
  columns?: number;
  showNewsletter?: boolean;
}

export const FooterSection: React.FC<FooterSectionProps> = ({
  description,
  columns = 3,
}) => {
  const cols = [
    { title: "Product", items: ["Features", "Pricing", "Integrations", "Changelog"] },
    { title: "Company", items: ["About", "Blog", "Careers", "Contact"] },
    { title: "Legal", items: ["Privacy", "Terms", "Security", "Cookies"] },
  ];
  return (
    <footer className="w-full border-t bg-background">
      <div className="container px-4 md:px-6 py-12 md:py-16">
        <div className="grid gap-8 lg:grid-cols-4">
          <div className="space-y-4">
            <div className="flex items-center gap-2 font-semibold text-lg">
              <span className="h-6 w-6 rounded-full bg-primary" />
              <span>LeadForge</span>
            </div>
            {description && (
              <p className="text-sm text-muted-foreground max-w-xs">{description}</p>
            )}
          </div>
          {cols.slice(0, columns).map((col, i) => (
            <div key={i}>
              <h4 className="font-semibold text-sm mb-4">{col.title}</h4>
              <ul className="space-y-3">
                {col.items.map((item, j) => (
                  <li key={j}>
                    <a href="#" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 border-t pt-8 text-center text-sm text-muted-foreground">
          <p>&copy; {new Date().getFullYear()} LeadForge AI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};
"""

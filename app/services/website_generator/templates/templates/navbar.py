from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_intelligence.schemas import SectionInfo


class NavbarTemplate(BaseTemplate):
    def supported_section_type(self) -> str:
        return "navbar"

    def validate(self, section: SectionInfo) -> bool:
        return True

    def render(self, section: SectionInfo) -> str:
        return """import React from 'react';
import Link from 'next/link';

interface NavbarSectionProps {
  heading?: string;
  links?: Array<{ label: string; url: string }>;
  isSticky?: boolean;
}

export const NavbarSection: React.FC<NavbarSectionProps> = ({
  heading,
  links = [],
  isSticky = true,
}) => {
  return (
    <header
      className={`w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 ${
        isSticky ? "sticky top-0 z-50" : ""
      }`}
    >
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-semibold text-lg">
          <span className="h-6 w-6 rounded-full bg-primary" />
          <span>{heading || "LeadForge"}</span>
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
          {links.map((link, i) => (
            <Link
              key={i}
              href={link.url}
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
};
"""

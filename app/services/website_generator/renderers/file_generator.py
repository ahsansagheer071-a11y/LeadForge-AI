import logging
from typing import List, Optional

from app.services.website_generator.blueprint_schemas import (
    BlueprintAsset,
    BlueprintPage,
    WebsiteBlueprint,
)
from app.services.website_generator.schemas import GeneratedFile
from app.services.website_generator.templates.engine import TemplateEngine
from app.services.website_generator.templates.registry import TemplateRegistry
from app.services.website_generator.templates.templates import get_all_template_classes
from app.services.website_intelligence.schemas import SectionInfo

logger = logging.getLogger(__name__)

_SECTION_TYPE_PROPS: dict = {
    "navbar": ("heading",),
    "hero": ("heading", "subheading", "description", "buttons"),
    "about": ("heading", "subheading", "description"),
    "services": ("heading", "subheading", "description"),
    "portfolio": ("heading", "subheading", "description"),
    "pricing": ("heading", "subheading", "description"),
    "faq": ("heading", "subheading", "description"),
    "testimonials": ("heading", "subheading", "description"),
    "contact": ("heading", "subheading", "description", "buttons"),
    "cta": ("heading", "subheading", "description", "buttons"),
    "footer": ("heading", "description",),
}

_SECTION_TYPE_LABELS = {
    "navbar": "Navbar",
    "hero": "Hero",
    "about": "About",
    "services": "Services",
    "portfolio": "Portfolio",
    "pricing": "Pricing",
    "faq": "FAQ",
    "testimonials": "Testimonials",
    "contact": "Contact",
    "cta": "CTA",
    "footer": "Footer",
}


def _build_section_props(section: SectionInfo) -> List[str]:
    props: List[str] = []
    allowed = _SECTION_TYPE_PROPS.get(section.section_type, ("heading", "description"))
    if "heading" in allowed and section.heading:
        props.append('heading="%s"' % section.heading.replace("'", "\\'"))
    if "subheading" in allowed and section.subheading:
        props.append('subheading="%s"' % section.subheading.replace("'", "\\'"))
    if "description" in allowed and section.description:
        props.append('description="%s"' % section.description.replace("'", "\\'"))
    if "buttons" in allowed and section.buttons:
        import json as _json
        btns = _json.dumps([{"text": b.text, "url": b.url} for b in section.buttons])
        props.append("buttons={%s}" % btns)
    return props


class FileGenerator:
    def __init__(self, engine: TemplateEngine | None = None) -> None:
        if engine is not None:
            self._engine = engine
        else:
            registry = TemplateRegistry()
            registry.register_many(get_all_template_classes())
            self._engine = TemplateEngine(registry)

    def generate_layout(self, blueprint: WebsiteBlueprint) -> GeneratedFile:
        business_name = blueprint.business_name or "LeadForge"
        seo_title = (blueprint.seo.get("title", "") or business_name)
        seo_desc = (blueprint.seo.get("description", "") or "Premium AI-powered lead intelligence platform")

        has_navbar = self._has_section(blueprint, "navbar")
        has_footer = self._has_section(blueprint, "footer")

        imports = [
            'import type { Metadata } from "next";',
            'import { Inter } from "next/font/google";',
            'import "./globals.css";',
        ]
        if has_navbar:
            imports.append('import { NavbarSection } from "@/components/sections/NavbarSection";')
        if has_footer:
            imports.append('import { FooterSection } from "@/components/sections/FooterSection";')

        nav_links = blueprint.navigation.get("links", [])
        is_sticky = blueprint.navigation.get("is_sticky", True)
        footer_cols = blueprint.footer.get("columns", 3)

        header = (
            f'<NavbarSection heading="{business_name}" links={{JSON.parse(\'{self._format_json(nav_links)}\')}} isSticky={{{str(is_sticky).lower()}}} />'
            if has_navbar else ""
        )
        footer = (
            f'<FooterSection description="{seo_desc}" columns={{{footer_cols}}} />'
            if has_footer else ""
        )

        lines = []
        for imp in imports:
            lines.append(imp)
        lines.append("")
        lines.append(f"""const inter = Inter({{\n  subsets: ["latin"],\n}});

export const metadata: Metadata = {{
  title: "{seo_title}",
  description: "{seo_desc}",
}};

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return (
    <html lang="en">
      <body className={{inter.className}}>
        {header}
        <main className="flex min-h-screen flex-col">{{children}}</main>
        {footer}
      </body>
    </html>
  );
}}""")

        content = "\n".join(lines)
        return GeneratedFile(
            path="app/layout.tsx",
            content=content,
            type="layout",
            size=len(content.encode("utf-8")),
        )

    def generate_page(
        self,
        blueprint: WebsiteBlueprint,
        page: BlueprintPage,
    ) -> GeneratedFile:
        business_name = blueprint.business_name or "LeadForge"
        page_title = page.title or page.page_name.replace("_", " ").title()
        route_parts = [p for p in page.route.strip("/").split("/") if p]

        sections = page.sections or blueprint.sections

        imports: List[str] = []
        section_renders: List[str] = []
        seen_types: set = set()

        for section in sections:
            st = section.section_type
            if st in seen_types or st not in _SECTION_TYPE_LABELS:
                continue
            seen_types.add(st)
            label = _SECTION_TYPE_LABELS[st]
            imports.append(
                f'import {{ {label}Section }} from "@/components/sections/{label}Section";'
            )
            props = _build_section_props(section)
            props_str = " ".join(props)
            section_renders.append(f"      <{label}Section {props_str} />")

        if not section_renders:
            sections_for_page = [
                s for s in blueprint.sections
                if s.section_type in _SECTION_TYPE_LABELS
            ]
            seen_types = set()
            for section in sections_for_page:
                st = section.section_type
                if st in seen_types:
                    continue
                seen_types.add(st)
                label = _SECTION_TYPE_LABELS[st]
                imports.append(
                    f'import {{ {label}Section }} from "@/components/sections/{label}Section";'
                )
                props = _build_section_props(section)
                props_str = " ".join(props)
                section_renders.append(f"      <{label}Section {props_str} />")

        imports_str = "\n".join(imports) if imports else ""
        sections_str = "\n".join(section_renders)

        content = f'''{imports_str}

export default function {page.page_name.replace("_", " ").title().replace(" ", "")}Page() {{
  return (
    <>
{sections_str}
    </>
  );
}}
'''

        if route_parts:
            path = f"app/{'/'.join(route_parts)}/page.tsx"
        else:
            path = "app/page.tsx"

        return GeneratedFile(
            path=path,
            content=content,
            type="page",
            size=len(content.encode("utf-8")),
        )

    def generate_section_component(
        self,
        section: SectionInfo,
        business_name: str = "",
    ) -> GeneratedFile | None:
        st = section.section_type
        label = _SECTION_TYPE_LABELS.get(st)
        if not label:
            logger.warning(
                "FileGenerator: No label for section type '%s'", st
            )
            return None

        content, is_valid = self._engine.render_section_with_validation(section)
        if not is_valid:
            logger.warning(
                "FileGenerator: Section '%s' rendered with fallback (validation failed)",
                st,
            )

        return GeneratedFile(
            path=f"components/sections/{label}Section.tsx",
            content=content,
            type="react_component",
            size=len(content.encode("utf-8")),
        )

    def generate_globals_css(
        self, blueprint: WebsiteBlueprint
    ) -> GeneratedFile:
        content = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
"""
        return GeneratedFile(
            path="app/globals.css",
            content=content,
            type="stylesheet",
            size=len(content.encode("utf-8")),
        )

    def generate_utils(self) -> GeneratedFile:
        content = """import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
"""
        return GeneratedFile(
            path="lib/utils.ts",
            content=content,
            type="script",
            size=len(content.encode("utf-8")),
        )

    def generate_asset_files(
        self, blueprint: WebsiteBlueprint
    ) -> List[GeneratedFile]:
        files: List[GeneratedFile] = []
        for asset in blueprint.assets:
            content = ""
            path = f"public/{asset.reference.lstrip('/')}"
            files.append(
                GeneratedFile(
                    path=path,
                    content=content,
                    type="asset",
                    size=0,
                )
            )
        return files

    def generate_tailwind_config(self) -> GeneratedFile:
        content = """import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};
export default config;
"""
        return GeneratedFile(
            path="tailwind.config.ts",
            content=content,
            type="configuration",
            size=len(content.encode("utf-8")),
        )

    def generate_package_json(self) -> GeneratedFile:
        content = """{
  "name": "leadforge-website",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^15.0.4",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.5.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.6.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
"""
        return GeneratedFile(
            path="package.json",
            content=content,
            type="configuration",
            size=len(content.encode("utf-8")),
        )

    def generate_tsconfig(self) -> GeneratedFile:
        content = """{
  "compilerOptions": {
    "target": "es2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""
        return GeneratedFile(
            path="tsconfig.json",
            content=content,
            type="configuration",
            size=len(content.encode("utf-8")),
        )

    def generate_postcss_config(self) -> GeneratedFile:
        content = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""
        return GeneratedFile(
            path="postcss.config.js",
            content=content,
            type="configuration",
            size=len(content.encode("utf-8")),
        )

    def generate_next_config(self) -> GeneratedFile:
        content = """/** @type {import('next').NextConfig} */
const nextConfig = {};
module.exports = nextConfig;
"""
        return GeneratedFile(
            path="next.config.js",
            content=content,
            type="configuration",
            size=len(content.encode("utf-8")),
        )

    @staticmethod
    def _has_section(blueprint: WebsiteBlueprint, section_type: str) -> bool:
        for s in blueprint.sections:
            if s.section_type == section_type:
                return True
        return False

    @staticmethod
    def _format_json(obj) -> str:
        import json as _json
        return _json.dumps(obj, ensure_ascii=False)

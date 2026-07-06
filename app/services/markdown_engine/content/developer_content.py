DEVELOPER_MD_CONTENT: str = """# Project Architecture

Use

Next.js App Router
TypeScript
TailwindCSS
shadcn/ui
Framer Motion
React Server Components where appropriate
Client Components only when required

## Folder Structure

Use scalable architecture.

Example hierarchy

app/
components/
features/
hooks/
lib/
styles/
public/

Do not flatten project structure.

## Component Rules

Each component must have a single responsibility.
Reusable.
Typed.
Composable.
No duplicate components.
Prefer composition over inheritance.

## State Management

Prefer local state.
Use Context only when necessary.
Avoid unnecessary global state.
Avoid prop drilling.

## Styling Rules

Tailwind only.
No inline CSS.
No CSS Modules.
No styled-components.
Spacing must follow 4px / 8px scale.
Rounded corners consistent.
Shadows consistent.

## Responsive Rules

Desktop first.
Tablet optimized.
Mobile optimized.
No broken layouts.
Fluid typography.
Fluid spacing.

## Forms

React Hook Form.
Zod validation.
Accessible labels.
Helpful validation messages.

## Images

Use Next Image.
Lazy loading.
Responsive sizes.
Priority only for hero.

## Icons

Lucide Icons only.
Consistent stroke width.
Consistent sizing.

## Animations

Framer Motion only.

Use

Fade
Slide
Scale
Stagger
Scroll reveal

Keep duration between 0.25s–0.6s.
Avoid excessive motion.

## Performance

Dynamic imports.
Code splitting.
Tree shaking.
Image optimization.
Minimal bundle size.
Avoid unnecessary re-renders.

## Accessibility

Semantic HTML.
Keyboard navigation.
ARIA attributes.
Visible focus states.
WCAG AA compliance.

## SEO

Metadata API.
Structured Data.
OpenGraph.
Twitter Cards.
Canonical URL.
Semantic headings.

## Error Handling

Graceful fallbacks.
No crashing UI.
Proper loading states.
Proper empty states.
Proper error states.

## Code Quality

Strict TypeScript.
No any.
Meaningful names.
Small functions.
No duplicated logic.
Readable architecture.

## File Generation Rules

Generate complete files.
Never generate partial snippets.
Never skip imports.
Never invent dependencies.
Never use deprecated APIs.
"""

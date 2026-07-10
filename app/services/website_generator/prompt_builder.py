from app.services.website_generator.schemas import GenerationContext, PromptContext


class PromptBuilder:
    def build(self, context: GenerationContext) -> PromptContext:
        combined = (
            context.rules_context
            + "\n\n---\n\n# Generation Constraints (from Output Requirements)\n\n"
            + context.output_context
        )
        return PromptContext(
            system_context=context.system_context,
            developer_context=context.developer_context,
            branding_context=context.branding_context,
            content_context=context.content_context,
            layout_context=context.layout_context,
            components_context=context.components_context,
            animation_context=context.animation_context,
            seo_context=context.seo_context,
            performance_context=context.performance_context,
            accessibility_context=context.accessibility_context,
            assets_context=context.assets_context,
            rules_context=context.rules_context,
            output_context=context.output_context,
            generation_constraints=combined,
        )

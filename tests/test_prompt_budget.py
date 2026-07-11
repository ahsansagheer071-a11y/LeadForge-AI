import pytest
from app.services.website_generator.schemas import PromptContext
from app.services.website_generator.prompt_budget import PromptBudgetController, BudgetAction, BudgetReport


@pytest.fixture
def controller():
    return PromptBudgetController()


def make_prompt(**overrides) -> PromptContext:
    defaults = {
        "content_context": "",
        "layout_context": "",
        "components_context": "",
        "rules_context": "",
        "system_context": "",
        "generation_constraints": "",
    }
    return PromptContext(**{**defaults, **overrides})


class TestPromptBudgetController:
    def test_apply_on_empty_prompt(self, controller):
        prompt = make_prompt()
        result, report = controller.apply(prompt)
        assert isinstance(result, PromptContext)
        assert report.original_total_chars == 0
        assert report.final_total_chars == 0
        assert report.chars_saved == 0

    def test_preserves_meaningful_content(self, controller):
        text = "We sell premium artisan coffee beans. Free shipping on orders over $50."
        prompt = make_prompt(content_context=text)
        result, report = controller.apply(prompt)
        assert text in result.content_context
        assert report.chars_saved == 0

    def test_removes_duplicate_nav_labels(self, controller):
        text = (
            "- **Home**\n"
            "- **About**\n"
            "- **Home**\n"
            "- **Contact**\n"
            "- **Home**\n"
        )
        prompt = make_prompt(content_context=text)
        result, report = controller.apply(prompt)
        assert result.content_context.count("- **Home**") == 1
        assert result.content_context.count("- **About**") == 1
        assert result.content_context.count("- **Contact**") == 1
        assert report.chars_saved > 0

    def test_removes_shopify_boilerplate(self, controller):
        text = "Some content Powered by Shopify more content Shopify store"
        prompt = make_prompt(content_context=text)
        result, report = controller.apply(prompt)
        assert "Powered by Shopify" not in result.content_context
        assert report.chars_saved > 0

    def test_removes_cookie_notices(self, controller):
        text = "This site uses cookies. Accept all cookies? We use cookies to improve."
        prompt = make_prompt(content_context=text)
        result, report = controller.apply(prompt)
        assert "cookie" not in result.content_context.lower() or "accept" not in result.content_context.lower()

    def test_removes_tracking_content(self, controller):
        text = "Some content gtag('config', 'UA-12345') and fbq('track', 'PageView')"
        prompt = make_prompt(content_context=text)
        result, report = controller.apply(prompt)
        assert "gtag" not in result.content_context
        assert "fbq" not in result.content_context

    def test_removes_technical_template(self, controller):
        text = "Some content {{ product.title }} and {% paginate by 5 %}"
        prompt = make_prompt(content_context=text)
        result, report = controller.apply(prompt)
        assert "{{" not in result.content_context

    def test_does_not_modify_tracking_in_non_content_fields(self, controller):
        text = "gtag('config', 'UA-12345')"
        prompt = make_prompt(
            content_context="Real content",
            layout_context=text,
        )
        result, report = controller.apply(prompt)
        assert "gtag" in result.layout_context
        assert result.content_context == "Real content"

    def test_report_contains_actions(self, controller):
        text = "Home About Home Products Powered by Shopify"
        prompt = make_prompt(content_context=text)
        _, report = controller.apply(prompt)
        assert isinstance(report, BudgetReport)
        assert len(report.actions) > 0
        for action in report.actions:
            assert isinstance(action, BudgetAction)
            assert action.chars_removed > 0
            assert action.field == "content_context"

    def test_report_counts_are_accurate(self, controller):
        text = "Home About Home Contact Powered by Shopify"
        prompt = make_prompt(content_context=text)
        _, report = controller.apply(prompt)
        assert report.chars_saved == report.original_total_chars - report.final_total_chars

    def test_handles_empty_fields_gracefully(self, controller):
        prompt = PromptContext(
            content_context="",
            layout_context="",
            generation_constraints="test",
        )
        result, report = controller.apply(prompt)
        assert result.content_context == ""
        assert report.original_total_chars == 4

    def test_apply_multiple_fields(self, controller):
        cc = "- **Home**\n- **About**\n- **Home**\nPowered by Shopify coffee"
        lc = "Built with Shopify template"
        prompt = make_prompt(content_context=cc, layout_context=lc)
        result, report = controller.apply(prompt)
        assert result.content_context.count("- **Home**") == 1
        assert "Powered by Shopify" not in result.content_context
        assert "Built with Shopify" not in result.layout_context
        assert report.chars_saved > 0

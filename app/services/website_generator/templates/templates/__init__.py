from app.services.website_generator.templates.templates.navbar import NavbarTemplate
from app.services.website_generator.templates.templates.hero import HeroTemplate
from app.services.website_generator.templates.templates.about import AboutTemplate
from app.services.website_generator.templates.templates.services import ServicesTemplate
from app.services.website_generator.templates.templates.portfolio import PortfolioTemplate
from app.services.website_generator.templates.templates.pricing import PricingTemplate
from app.services.website_generator.templates.templates.faq import FAQTemplate
from app.services.website_generator.templates.templates.testimonials import TestimonialsTemplate
from app.services.website_generator.templates.templates.contact import ContactTemplate
from app.services.website_generator.templates.templates.cta import CTATemplate
from app.services.website_generator.templates.templates.footer import FooterTemplate

_ALL_TEMPLATES = {
    "navbar": NavbarTemplate,
    "hero": HeroTemplate,
    "about": AboutTemplate,
    "services": ServicesTemplate,
    "portfolio": PortfolioTemplate,
    "pricing": PricingTemplate,
    "faq": FAQTemplate,
    "testimonials": TestimonialsTemplate,
    "contact": ContactTemplate,
    "cta": CTATemplate,
    "footer": FooterTemplate,
}


def get_all_template_classes():
    return dict(_ALL_TEMPLATES)

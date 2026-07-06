import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NavigationItem(BaseModel):
    label: str
    url: str
    children: List["NavigationItem"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class HeroSection(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    cta_buttons: List[Dict[str, Any]] = Field(default_factory=list)
    background_image: Optional[str] = None


class AboutSection(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    images: List[str] = Field(default_factory=list)


class ServiceItem(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image: Optional[str] = None


class ContactInfo(BaseModel):
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    address: Optional[str] = None
    contact_form_present: bool = False
    contact_form_fields: List[str] = Field(default_factory=list)


class SocialLink(BaseModel):
    platform: str
    url: str
    icon: Optional[str] = None


class TestimonialItem(BaseModel):
    author: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    content: str
    avatar: Optional[str] = None
    rating: Optional[int] = None


class FAQItem(BaseModel):
    question: str
    answer: str


class TeamMember(BaseModel):
    name: str
    role: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[str] = None
    social_links: List[SocialLink] = Field(default_factory=list)


class BlogLink(BaseModel):
    title: str
    url: str
    excerpt: Optional[str] = None
    image: Optional[str] = None
    date: Optional[str] = None


class FooterContent(BaseModel):
    copyright: Optional[str] = None
    navigation: List[NavigationItem] = Field(default_factory=list)
    social_links: List[SocialLink] = Field(default_factory=list)
    newsletter_signup: bool = False
    legal_links: List[NavigationItem] = Field(default_factory=list)


class ColorPalette(BaseModel):
    primary: Optional[str] = None
    secondary: Optional[str] = None
    accent: Optional[str] = None
    background: Optional[str] = None
    text: Optional[str] = None


class FontInfo(BaseModel):
    family: str
    weight: Optional[str] = None
    usage: Optional[str] = None


class Statistics(BaseModel):
    sections_count: int = 0
    images_count: int = 0
    forms_count: int = 0
    buttons_count: int = 0
    total_words: int = 0
    load_time_ms: Optional[float] = None


class WebsiteIntelligence(BaseModel):
    business_name: str = ""
    category: str = ""
    logo: str = ""
    favicon: str = ""
    colors: ColorPalette = Field(default_factory=ColorPalette)
    fonts: List[FontInfo] = Field(default_factory=list)
    navigation: List[NavigationItem] = Field(default_factory=list)
    hero: HeroSection = Field(default_factory=HeroSection)
    services: List[ServiceItem] = Field(default_factory=list)
    about: AboutSection = Field(default_factory=AboutSection)
    contact: ContactInfo = Field(default_factory=ContactInfo)
    footer: FooterContent = Field(default_factory=FooterContent)
    social_links: List[SocialLink] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    testimonials: List[TestimonialItem] = Field(default_factory=list)
    faq: List[FAQItem] = Field(default_factory=list)
    team: List[TeamMember] = Field(default_factory=list)
    blog_links: List[BlogLink] = Field(default_factory=list)
    statistics: Statistics = Field(default_factory=Statistics)
    raw_html_size_kb: Optional[float] = None
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class WebsiteIntelligenceResponse(BaseModel):
    lead_id: uuid.UUID
    website_url: str
    intelligence: WebsiteIntelligence

    model_config = ConfigDict(from_attributes=True)


class WebsiteIntelligenceRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to extract intelligence from.")
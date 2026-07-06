import sys, types, asyncio

# Bootstrap WebsiteProfile
wi_init = types.ModuleType('app.services.website_intelligence')
wi_init.__path__ = []
sys.modules['app.services.website_intelligence'] = wi_init

wi_schemas_mod = types.ModuleType('app.services.website_intelligence.schemas')
wi_schemas_mod.__file__ = 'app/services/website_intelligence/schemas.py'
sys.modules['app.services.website_intelligence.schemas'] = wi_schemas_mod
with open(wi_schemas_mod.__file__) as f:
    code = compile(f.read(), wi_schemas_mod.__file__, 'exec')
exec(code, wi_schemas_mod.__dict__)

WebsiteProfile = wi_schemas_mod.WebsiteProfile

from app.services.markdown_engine.builder import MarkdownBuilder
from app.services.website_generator.context_builder import ContextBuilder
from app.services.website_generator.prompt_builder import PromptBuilder
from app.services.website_generator.providers.grok_provider import GrokProvider
from app.services.website_generator.providers.provider_factory import ProviderFactory, register_provider
from app.services.website_generator.providers.schemas import AIResponse, AIUsage
from app.services.website_generator.providers.base import AIProvider
from app.services.website_generator.schemas import PromptContext
from datetime import datetime, timezone


# ===== Build PromptContext =====
profile = WebsiteProfile(
    business=wi_schemas_mod.BusinessInfo(name="Acme Corp", industry="Enterprise Software"),
    brand=wi_schemas_mod.BrandIdentity(
        brand_colors=wi_schemas_mod.ColorPalette(
            primary="#1A73E8", contrast_ratios={"text_on_background": 7.2},
            wcag_compliance={"text_on_background": "AAA"}, accessibility_score=82.0,
        ),
        typography_info=wi_schemas_mod.TypographyInfo(primary_font="Inter", heading_font="Inter"),
        logo_info=wi_schemas_mod.LogoInfo(logo_url="https://example.com/logo.png"),
        design_language=wi_schemas_mod.DesignLanguageResult(
            design_language="Modern SaaS", confidence_score=0.85,
        ),
    ),
    seo=wi_schemas_mod.SEOInfo(
        page_title="Acme Corp", meta_description="Enterprise software.", https_enabled=True,
    ),
    images=[wi_schemas_mod.ImageAsset(url="https://example.com/img.jpg", alt="Test")],
    extraction_timestamp=datetime.now(timezone.utc),
)

builder = MarkdownBuilder(profile)
pkg = builder.build_package()
ctx = ContextBuilder().build(profile, pkg)
prompt = PromptBuilder().build(ctx)


async def test_all():
    print('=' * 60)
    print('TEST 1: ProviderFactory basic resolution')
    print('=' * 60)
    provider = ProviderFactory.get_provider("grok")
    assert isinstance(provider, GrokProvider)
    assert isinstance(provider, AIProvider)
    print(f'  Resolved: {type(provider).__name__}')
    print('  >>> PASS')
    print()

    print('=' * 60)
    print('TEST 2: Default provider resolution')
    print('=' * 60)
    provider2 = ProviderFactory.get_provider()
    assert isinstance(provider2, GrokProvider)
    print(f'  Default resolved to: {type(provider2).__name__}')
    print('  >>> PASS')
    print()

    print('=' * 60)
    print('TEST 3: Unknown provider raises ValueError')
    print('=' * 60)
    try:
        ProviderFactory.get_provider("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f'  ValueError: {e}')
    print('  >>> PASS')
    print()

    print('=' * 60)
    print('TEST 4: Register new provider')
    print('=' * 60)
    class FakeProvider(AIProvider):
        async def generate(self, pc): return AIResponse(success=True, provider="fake", model="fake")
        async def health_check(self): return True
        def provider_name(self): return "fake"
        def supported_models(self): return ["fake"]
    register_provider("fake", FakeProvider)
    fake = ProviderFactory.get_provider("fake")
    assert isinstance(fake, FakeProvider)
    print(f'  Registered and resolved: {type(fake).__name__}')
    print('  >>> PASS')
    print()

    print('=' * 60)
    print('TEST 5: GrokProvider interface methods')
    print('=' * 60)
    gp = GrokProvider()
    assert gp.provider_name() == "grok"
    models = gp.supported_models()
    assert len(models) >= 1
    assert "grok-3-mini" in models
    print(f'  provider_name: {gp.provider_name()}')
    print(f'  supported_models: {models}')
    print('  >>> PASS')
    print()

    print('=' * 60)
    print('TEST 6: GrokProvider — missing API key')
    print('=' * 60)
    gp_no_key = GrokProvider(api_key=None)
    resp = await gp_no_key.generate(prompt)
    assert resp.success is False
    assert any("not configured" in e for e in resp.errors)
    print(f'  success: {resp.success}')
    print(f'  errors: {resp.errors}')
    print('  >>> PASS')
    print()

    print('=' * 60)
    print('TEST 7: GrokProvider — invalid API key (auth error)')
    print('=' * 60)
    gp_bad_key = GrokProvider(api_key="sk-invalid-key-for-testing")
    resp2 = await gp_bad_key.generate(prompt)
    # Expect either auth failure or connection error depending on network
    assert resp2.success is False
    print(f'  success: {resp2.success}')
    print(f'  errors: {resp2.errors}')
    print('  >>> PASS')
    print()

    print('=' * 60)
    print('TEST 8: GrokProvider — live real API call')
    print('=' * 60)
    gp_live = GrokProvider()
    # Check if API key is actually set
    if gp_live._api_key:
        resp3 = await gp_live.generate(prompt)
        print(f'  success:         {resp3.success}')
        print(f'  provider:        {resp3.provider}')
        print(f'  model:           {resp3.model}')
        print(f'  latency:         {resp3.latency:.2f}s')
        if resp3.usage:
            u = resp3.usage
            print(f'  usage:           prompt={u.prompt_tokens}  completion={u.completion_tokens}  total={u.total_tokens}')
        if resp3.success and resp3.raw_response:
            preview = resp3.raw_response[:300]
            print(f'  raw_response (first 300 chars):')
            print(f'    {preview}...')
        elif not resp3.success:
            print(f'  errors:          {resp3.errors}')
            print(f'  warnings:        {resp3.warnings}')
        print('  >>> LIVE TEST DONE (see above for results)')
    else:
        print('  GROK_API_KEY not set — skipping live test')
        print('  To run live test: set GROK_API_KEY in .env')
    print()

    print('=' * 60)
    print('TEST 9: AIResponse + AIUsage schema structure')
    print('=' * 60)
    u = AIUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, estimated_cost=0.0001)
    assert u.prompt_tokens == 10
    assert u.total_tokens == 30
    r = AIResponse(success=True, provider="grok", model="grok-3-mini", raw_response="hello", usage=u, latency=1.5)
    assert r.success is True
    assert r.usage.total_tokens == 30
    print(f'  AIUsage: {u.model_dump()}')
    print(f'  AIResponse: success={r.success}, provider={r.provider}, latency={r.latency}')
    print('  >>> PASS')
    print()

    print('All provider tests completed.')

asyncio.run(test_all())

"""Check profile data from database reconstruction."""
import json, sys, io, urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = "https://leadforge-ai-production-eff1.up.railway.app"

login_body = urllib.parse.urlencode({"username": "test@test.com", "password": "Test123!"}).encode()
login_req = urllib.request.Request(f"{BASE}/api/v1/auth/login", data=login_body,
    headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
resp = urllib.request.urlopen(login_req, timeout=10)
token = json.loads(resp.read())["access_token"]
auth = {"Authorization": f"Bearer {token}"}

# Check the website intelligence profile via the build endpoint
# Actually, let me check what the generation endpoint returns as diagnostics
sites = [("kissthehippo", "9105ef6f-e9fc-4152-ad0e-22c2dbf240db"), ("stumptown", "5d86fb3d-c77a-4f90-aba9-c3d5eaebda82")]

for name, lid in sites:
    # Check lead detail
    r = urllib.request.Request(f"{BASE}/api/v1/leads/{lid}", headers=auth)
    resp = urllib.request.urlopen(r, timeout=30)
    d = json.loads(resp.read())
    lead = d.get("data", d)
    print(f"\n=== {name} ===")
    print(f"  website: {lead.get('website')}")
    
    # Check the intelligence profile endpoint  
    r2 = urllib.request.Request(f"{BASE}/api/v1/generation/leads/{lid}/profile", headers=auth)
    try:
        resp2 = urllib.request.urlopen(r2, timeout=30)
        d2 = json.loads(resp2.read())
        profile = d2.get("data", {}).get("profile", d2.get("profile", {}))
        biz = profile.get("business", {})
        products = profile.get("products", [])
        services = profile.get("services", [])
        testimonials = profile.get("testimonials", [])
        faqs = profile.get("faqs", [])
        team = profile.get("team", [])
        contact = profile.get("contact", {})
        hero = profile.get("hero_info", {}) or profile.get("hero", {})
        images = profile.get("images", [])
        
        print(f"  Business name: {biz.get('name', 'EMPTY')}")
        print(f"  Products: {len(products)}")
        for p in products[:3]:
            print(f"    - {p.get('title', 'N/A')}")
        print(f"  Services: {len(services)}")
        for s in services[:3]:
            print(f"    - {s.get('name', 'N/A')}")
        print(f"  Testimonials: {len(testimonials)}")
        for t in testimonials[:2]:
            print(f"    - {t.get('author', 'N/A')}: {(t.get('content', '') or t.get('review_text', ''))[:60]}")
        print(f"  FAQs: {len(faqs)}")
        print(f"  Team: {len(team)}")
        print(f"  Contact emails: {contact.get('emails', [])}")
        print(f"  Images: {len(images)}")
        hero_img = hero.get('hero_image') or hero.get('background_image_url')
        print(f"  Hero image: {hero_img}")
        print(f"  Hero title: {hero.get('hero_title') or hero.get('title')}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        print(f"  Profile endpoint: HTTP {e.code}: {raw[:200]}")

"""Comprehensive production test: runs both websites through the full generation
pipeline and returns detailed metrics on content preservation."""
import json, sys, io, time, urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "https://leadforge-ai-production-eff1.up.railway.app"
FRONTEND = "https://leadforge-ai.vercel.app"

def req(method, path, headers=None, data=None, form=None, timeout=300):
    hdrs = {}
    if headers: hdrs.update(headers)
    body = None
    if form:
        body = urllib.parse.urlencode(form).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")
    url = f"{BASE}{path}"
    for _ in range(3):
        r = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        try:
            resp = urllib.request.urlopen(r, timeout=timeout)
            raw = resp.read()
            try: return resp.status, json.loads(raw)
            except: return resp.status, raw.decode()
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 307, 308) and e.headers.get("Location"):
                url = e.headers["Location"]
                if url.startswith("/"): url = f"{BASE}{url}"
                body = None
                continue
            raw = e.read()
            try: return e.code, json.loads(raw)
            except: return e.code, raw.decode()
        except Exception as e:
            return 0, str(e)
    return 0, "Too many redirects"

# --- Auth ---
print("=" * 60)
print("LOGIN")
print("=" * 60)
s, d = req("POST", "/api/v1/auth/login", form={"username": "test@test.com", "password": "Test123!"})
if s != 200:
    print(f"FATAL: Login failed: {s} {d}")
    sys.exit(1)
token = d["access_token"]
auth = {"Authorization": f"Bearer {token}"}
print(f"  Login OK (HTTP {s})")

# --- Find existing leads ---
print("\n" + "=" * 60)
print("LEADS")
print("=" * 60)
s, d = req("GET", "/api/v1/leads", headers=auth)
leads = d.get("data", {}).get("items", []) if isinstance(d, dict) else []
print(f"  Found {len(leads)} leads")

target_sites = {
    "kissthehippo.com": None,
    "stumptowncoffee.com": None,
}
for lead in leads:
    url = lead.get("website", "")
    lid = lead.get("id")
    for site in target_sites:
        if site in (url or ""):
            target_sites[site] = lid
            print(f"  {site} -> lead {lid}")

# --- Helper: generate and poll ---
def generate_and_poll(lead_id, site_name):
    print(f"\n{'=' * 60}")
    print(f"GENERATE: {site_name} (lead={lead_id})")
    print(f"{'=' * 60}")

    s, d = req("POST", "/api/v1/generation/jobs", headers=auth, data={"lead_id": lead_id})
    if s not in (200, 201, 202):
        print(f"  Failed to create job: {s} {d}")
        return None
    job_id = d.get("data", {}).get("job_id")
    if not job_id:
        print(f"  No job_id in response: {d}")
        return None
    print(f"  Job created: {job_id}")

    for attempt in range(60):
        time.sleep(5)
        s, d = req("GET", f"/api/v1/generation/jobs/{job_id}", headers=auth)
        if s != 200:
            print(f"  Poll failed: {s}")
            continue
        data = d.get("data", {})
        status = data.get("status", "unknown")
        progress = data.get("progress", "")
        provider = data.get("provider_used", "unknown")
        gen_time = data.get("generation_time", 0)
        print(f"  [{attempt+1}] status={status} | progress={progress} | provider={provider} | time={gen_time:.1f}s")

        if status == "succeeded":
            html = data.get("html", "")
            website_id = data.get("website_id")
            preview_path = data.get("preview_path")
            return {
                "site": site_name,
                "status": "succeeded",
                "html": html,
                "html_len": len(html) if html else 0,
                "website_id": website_id,
                "preview_path": preview_path,
                "provider_used": provider,
                "generation_time": gen_time,
                "job_id": job_id,
                "polls": attempt + 1,
            }
        elif status == "failed":
            error = data.get("error", "unknown")
            print(f"  FAILED: {error}")
            return {"site": site_name, "status": "failed", "error": error, "provider_used": provider}

    print(f"  TIMEOUT after 60 polls")
    return {"site": site_name, "status": "timeout"}

results = {}
for site, lead_id in target_sites.items():
    if lead_id:
        results[site] = generate_and_poll(lead_id, site)
    else:
        print(f"\n  Skipping {site} — no lead found")

# --- Analyze HTML content ---
print("\n" + "=" * 60)
print("CONTENT ANALYSIS")
print("=" * 60)

import re
def analyze_html(html, site_name):
    if not html:
        return {"error": "empty html"}
    text_only = re.sub(r'<[^>]+>', ' ', html)
    text_only = re.sub(r'\s+', ' ', text_only).strip()
    words = text_only.split()
    img_refs = re.findall(r'<img[^>]+src\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
    sections = len(re.findall(r'<section', html, re.IGNORECASE))
    h_tags = len(re.findall(r'<h[1-6]', html, re.IGNORECASE))
    has_hero = bool(re.search(r'<header|<section[^>]*hero|class=["\'].*hero|background-image', html, re.IGNORECASE))
    has_about = bool(re.search(r'about|our\s+story|who\s+we\s+are', html, re.IGNORECASE))
    has_contact = bool(re.search(r'mailto:|@|phone|tel:|contact', html, re.IGNORECASE))
    has_footer = bool(re.search(r'<footer', html, re.IGNORECASE))
    return {
        "html_chars": len(html),
        "visible_words": len(words),
        "image_count": len(img_refs),
        "section_count": sections,
        "h_tag_count": h_tags,
        "has_hero": has_hero,
        "has_about": has_about,
        "has_contact": has_contact,
        "has_footer": has_footer,
        "first_100_words": " ".join(words[:100]),
    }

for site, result in results.items():
    if result and result.get("status") == "succeeded":
        analysis = analyze_html(result.get("html", ""), site)
        result["analysis"] = analysis
        print(f"\n  {site}:")
        print(f"    HTML chars: {analysis['html_chars']}")
        print(f"    Visible words: {analysis['visible_words']}")
        print(f"    Images: {analysis['image_count']}")
        print(f"    Sections: {analysis['section_count']}")
        print(f"    H-tags: {analysis['h_tag_count']}")
        print(f"    Hero: {analysis['has_hero']} | About: {analysis['has_about']} | Contact: {analysis['has_contact']} | Footer: {analysis['has_footer']}")
        print(f"    Provider: {result.get('provider_used', 'unknown')}")
        print(f"    Generation time: {result.get('generation_time', 0):.1f}s")

# --- Preview URLs ---
print("\n" + "=" * 60)
print("PREVIEW URLS")
print("=" * 60)
for site, result in results.items():
    if result and result.get("website_id"):
        wid = result["website_id"]
        print(f"  {site}: {FRONTEND}/preview/{wid}")

# --- ZIP download ---
print("\n" + "=" * 60)
print("ZIP DOWNLOAD")
print("=" * 60)
for site, result in results.items():
    if result and result.get("website_id"):
        wid = result["website_id"]
        url = f"{BASE}/api/v1/generation/websites/{wid}/download"
        hdrs = {"Authorization": f"Bearer {token}"}
        try:
            r = urllib.request.Request(url, headers=hdrs)
            resp = urllib.request.urlopen(r, timeout=120)
            zip_data = resp.read()
            ct = resp.headers.get("Content-Type", "")
            print(f"  {site}: {len(zip_data)} bytes | type={ct}")
            result["zip_size"] = len(zip_data)
        except urllib.error.HTTPError as e:
            print(f"  {site}: HTTP {e.code}")
            result["zip_size"] = 0
        except Exception as e:
            print(f"  {site}: Error: {e}")
            result["zip_size"] = 0

# --- Final Summary ---
print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)
for site, result in results.items():
    if not result:
        print(f"  {site}: SKIPPED (no lead)")
        continue
    print(f"\n  {site}:")
    print(f"    Status: {result.get('status')}")
    print(f"    Provider: {result.get('provider_used', 'unknown')}")
    print(f"    Generation time: {result.get('generation_time', 0):.1f}s")
    if result.get("analysis"):
        a = result["analysis"]
        print(f"    HTML: {a['html_chars']} chars, {a['visible_words']} words")
        print(f"    Images: {a['image_count']}, Sections: {a['section_count']}")
        print(f"    Sections present: hero={a['has_hero']} about={a['has_about']} contact={a['has_contact']} footer={a['has_footer']}")
    if result.get("zip_size"):
        print(f"    ZIP: {result['zip_size']} bytes")
    if result.get("error"):
        print(f"    Error: {result['error']}")

# Save full results to file
with open("production_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nFull results saved to production_results.json")

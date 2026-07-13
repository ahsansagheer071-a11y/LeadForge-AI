"""Production test for fidelity fixes: products, hero H1, images, no placeholders."""
import json, sys, io, urllib.request, urllib.parse, time, re, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "https://leadforge-ai-production-eff1.up.railway.app"

def req(method, path, headers=None, data=None, form=None, timeout=60):
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
    for attempt in range(3):
        r = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        try:
            resp = urllib.request.urlopen(r, timeout=timeout)
            raw = resp.read()
            try: return resp.status, json.loads(raw)
            except: return resp.status, raw.decode()
        except urllib.error.HTTPError as e:
            raw = e.read()
            try: return e.code, json.loads(raw)
            except: return e.code, raw.decode()
        except Exception:
            if attempt < 2: time.sleep(2); continue
            return 0, "Connection failed"
    return 0, "Too many retries"

s, d = req("POST", "/api/v1/auth/login", form={"username": "test@test.com", "password": "Test123!"})
token = d["access_token"]
auth = {"Authorization": f"Bearer {token}"}

sites = [
    ("kissthehippo", "9105ef6f-e9fc-4152-ad0e-22c2dbf240db"),
    ("stumptown", "5d86fb3d-c77a-4f90-aba9-c3d5eaebda82"),
]

results = {}
for name, lid in sites:
    print(f"\n{'='*60}")
    print(f"Generating for {name}...")
    s, d = req("POST", "/api/v1/generation/jobs", headers=auth, data={"lead_id": lid})
    job_id = d.get("data", {}).get("job_id")
    if not job_id:
        print(f"  ERROR: {d}"); continue
    print(f"  Job: {job_id}")

    for attempt in range(90):
        time.sleep(5)
        s2, d2 = req("GET", f"/api/v1/generation/jobs/{job_id}", headers=auth)
        if s2 != 200 or not isinstance(d2, dict): continue
        data = d2.get("data", {})
        status = data.get("status", "unknown")
        provider = data.get("provider_used", "")
        gen_time = data.get("generation_time", 0)
        if attempt % 5 == 0 or status in ("succeeded", "failed"):
            print(f"  [{attempt+1}] status={status} provider={provider} time={gen_time:.1f}s")
        if status == "succeeded":
            html = data.get("html", "")
            if not html: print("  ERROR: no HTML"); break

            # Analysis
            title_m = re.search(r'<title>(.*?)</title>', html)
            title = title_m.group(1) if title_m else "N/A"

            h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
            h1_text = re.sub(r'<[^>]+>', '', h1_m.group(1)).strip() if h1_m else "NO H1"

            imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
            placeholders = [i for i in imgs if "placeholder" in i.lower() or "example.com" in i]
            real = [i for i in imgs if i not in placeholders]
            img_counts = collections.Counter(real)
            dupes = {k: v for k, v in img_counts.items() if v > 1}

            cards = len(re.findall(r'class="card"', html, re.IGNORECASE))
            has_header = bool(re.search(r'<header', html, re.IGNORECASE))
            has_footer = bool(re.search(r'<footer', html, re.IGNORECASE))
            h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
            h3s = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)

            # Check for product links
            product_links = re.findall(r'href="[^"]*(?:/products/|/collections/)[^"]*"', html, re.IGNORECASE)

            print(f"\n  RESULTS:")
            print(f"    Title: {title}")
            print(f"    H1: {h1_text}")
            print(f"    provider_used: {provider}")
            print(f"    HTML: {len(html)} chars")
            print(f"    Images: {len(real)} real, {len(placeholders)} placeholder, {len(dupes)} duplicated")
            for url, count in list(dupes.items())[:3]:
                print(f"      DUPE {count}x: {url[:100]}")
            for img in real[:3]:
                print(f"      IMG: {img[:100]}")
            print(f"    Cards: {cards}")
            print(f"    Hero <header>: {has_header} | Footer: {has_footer}")
            print(f"    H2s: {[h.strip()[:50] for h in h2s]}")
            print(f"    H3s: {[h.strip()[:50] for h in h3s]}")
            print(f"    Product links in HTML: {len(product_links)}")
            for pl in product_links[:5]:
                print(f"      {pl}")

            with open(f"tmp_{name}_latest.html", "w", encoding="utf-8") as f:
                f.write(html)

            results[name] = {
                "title": title, "h1": h1_text, "provider": provider,
                "html_len": len(html), "real_imgs": len(real),
                "placeholders": len(placeholders), "dupes": len(dupes),
                "cards": cards, "h3s": len(h3s), "has_header": has_header,
                "has_footer": has_footer, "product_links": len(product_links),
                "warnings": data.get("build_metadata", {}).get("warnings", []),
            }
            break
        elif status == "failed":
            print(f"  FAILED: {data.get('error', '')[:200]}")
            break
    else:
        print(f"  TIMEOUT")

# Summary
print(f"\n{'='*60}")
print("SUMMARY:")
for name, r in results.items():
    print(f"\n  {name}:")
    print(f"    H1: {r['h1']}")
    print(f"    Cards: {r['cards']}")
    print(f"    Real images: {r['real_imgs']}")
    print(f"    Placeholder images: {r['placeholders']}")
    print(f"    Duplicate images: {r['dupes']}")
    print(f"    Provider: {r['provider']}")
    print(f"    Warnings: {r['warnings']}")

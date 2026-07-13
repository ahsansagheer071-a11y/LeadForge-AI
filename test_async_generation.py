"""End-to-end async generation workflow test against deployed Railway backend."""

import urllib.request, urllib.parse, urllib.error
import json, time, random, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "https://leadforge-ai-production-eff1.up.railway.app"
PASS = 0
FAIL = 0

def log(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}: {detail[:400]}")

def req_json(method, path, headers=None, data=None, form=None, timeout=180):
    """JSON request/response."""
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
    except Exception as e:
        return 0, str(e)

def req_binary(method, path, headers=None, timeout=180):
    """Binary response (e.g. ZIP download)."""
    hdrs = {}
    if headers: hdrs.update(headers)
    url = f"{BASE}{path}"
    r = urllib.request.Request(url, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        raw = resp.read()
        return resp.status, raw, resp.headers
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, raw, e.headers
    except Exception as e:
        return 0, str(e), {}

# -----------------------------------------------------------------------
# Common test data
# -----------------------------------------------------------------------
WEB_CHAIN = [
    ("example.com", "Simple site"),
    ("kissthehippo.com", "Complex site"),
]

# -----------------------------------------------------------------------
# Setup: login as existing test user
# -----------------------------------------------------------------------
print("=" * 60)
print("ASYNC GENERATION WORKFLOW TEST")
print("=" * 60)

print("\n--- SETUP ---")
c, d = req_json("GET", "/health")
log("Health check", c == 200 and isinstance(d, dict) and d.get("status") == "online", str(d)[:100])

# Login
c, d = req_json("POST", "/api/v1/auth/login", form={"username": "test@test.com", "password": "Test123!"})
token = d.get("access_token", "") if c == 200 and isinstance(d, dict) else ""
log("Login", bool(token), str(d)[:100] if not token else "")
if not token:
    print("Cannot continue: login failed. Exiting.")
    sys.exit(1)

H = {"Authorization": f"Bearer {token}"}

# -----------------------------------------------------------------------
# Run 2 website generation tests
# -----------------------------------------------------------------------
results = []

for host, label in WEB_CHAIN:
    print(f"\n--- TEST: {label} ({host}) ---")

    # Create a fresh lead
    c, d = req_json("POST", "/api/v1/leads", headers=H, data={
        "url": f"https://{host}",
        "company_name": f"Test {label}",
        "industry": "Technology",
    }, timeout=30)
    lead_id = d.get("data", {}).get("id") if c == 201 else None
    log(f"Create lead for {host}", bool(lead_id), f"HTTP {c}: {str(d)[:150]}")

    if not lead_id:
        continue

    # Build profile first (crawl)
    c, d = req_json("POST", "/api/v1/generation/build", headers=H, data={"lead_id": lead_id}, timeout=120)
    log(f"Build profile for {host}", c == 200, f"HTTP {c}: {str(d)[:200]}")

    # Submit async generation job
    c, d = req_json("POST", "/api/v1/generation/jobs", headers=H, data={"lead_id": lead_id}, timeout=30)
    job_id = d.get("data", {}).get("job_id") if c in (200, 202) else None
    log(f"Submit job for {host}", bool(job_id), f"HTTP {c}: {str(d)[:200]}")

    if not job_id:
        continue

    # Poll until complete
    provider = ""
    website_id = ""
    final_status = ""
    total_wait = 0
    poll_interval = 5
    max_wait = 300

    print(f"  Polling job {job_id[:12]}...", end="", flush=True)
    while total_wait < max_wait:
        time.sleep(poll_interval)
        total_wait += poll_interval
        c, d = req_json("GET", f"/api/v1/generation/jobs/{job_id}", headers=H, timeout=30)
        if c != 200:
            break
        data = d.get("data", {})
        status = data.get("status", "")
        progress = data.get("progress", "")
        website_id = data.get("website_id") or website_id
        provider = data.get("provider_used") or provider
        print(".", end="", flush=True)

        if status == "succeeded":
            final_status = "succeeded"
            print(f" DONE ({total_wait}s)")
            break
        elif status == "failed":
            final_status = "failed"
            error = data.get("error", "Unknown error")
            print(f"\n  FAILED after {total_wait}s: {error}")
            break

    if not final_status:
        print(f"\n  TIMEOUT after {max_wait}s")

    log(f"Generation for {host}: {final_status or 'timeout'}", final_status == "succeeded",
        f"provider={provider} website_id={website_id} duration={total_wait}s")

    if website_id:
        # Test Preview API
        c, d = req_json("GET", f"/api/v1/generation/websites/{website_id}", headers=H, timeout=30)
        log(f"Preview API for {host} (website_id)", c == 200 and d.get("data", {}).get("html"),
            f"HTTP {c}: has_html={bool(d.get('data', {}).get('html', '')[:50])}")

        if c == 200 and d.get("data", {}).get("html"):
            html = d["data"]["html"]
            log(f"Generated HTML for {host} non-empty", len(html) > 100, f"len={len(html)}")
            log(f"HTML structure valid", "<!DOCTYPE html" in html.upper() or "<html" in html.lower(),
                f"starts with: {html[:80].strip()}")

        # Test ZIP download (binary endpoint)
        c, raw, headers = req_binary("GET", f"/api/v1/generation/websites/{website_id}/download", headers=H, timeout=60)
        log(f"ZIP download for {host} HTTP {c}", c == 200, f"Content-Type={headers.get('Content-Type')}")
        if c == 200 and isinstance(raw, bytes):
            log(f"ZIP size for {host}", len(raw) > 0, f"size={len(raw)} bytes")
            try:
                import zipfile
                zf = zipfile.ZipFile(io.BytesIO(raw))
                names = zf.namelist()
                log(f"ZIP valid for {host}", len(names) > 0, f"files={names}")
                has_index = any("index.html" in n for n in names)
                log(f"ZIP has index.html for {host}", has_index, f"files={names}")

                # Verify index.html content is valid HTML
                for name in names:
                    if "index.html" in name:
                        content = zf.read(name).decode("utf-8", errors="replace")
                        log(f"index.html content valid for {host}",
                            len(content) > 100 and ("<!DOCTYPE html" in content.upper() or "<html" in content.lower()),
                            f"len={len(content)} start={content[:80].strip()}")
                        break
            except Exception as e:
                log(f"ZIP extraction for {host}", False, str(e))

    results.append({
        "host": host,
        "label": label,
        "lead_id": lead_id,
        "job_id": job_id,
        "website_id": website_id,
        "status": final_status,
        "provider": provider,
        "duration": total_wait,
    })

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
print(f"\n{'='*60}")
print(f"RESULTS: {PASS} passed, {FAIL} failed")
for r in results:
    print(f"  {r['label']:25s} | status={r['status'] or 'N/A':10s} | provider={r['provider'] or 'N/A':15s} | "
          f"website_id={str(r['website_id'])[:12] if r['website_id'] else 'N/A':12s} | {r.get('duration', 0)}s")
print(f"{'='*60}")

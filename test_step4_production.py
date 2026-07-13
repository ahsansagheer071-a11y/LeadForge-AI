"""STEP 4 — Final Production Acceptance Test.

Tests the complete generation pipeline against deployed Railway backend:
  - Real website generation (async jobs)
  - Fidelity validation
  - Preview (HTML with source images)
  - ZIP download and structure validation
"""

import urllib.request, urllib.parse, urllib.error
import json, time, sys, io, os, re, base64, zipfile
from zipfile import ZipFile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "https://leadforge-ai-production-eff1.up.railway.app"
PASS = 0
FAIL = 0
RESULTS = []


def log(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}: {detail[:500]}")


def req_json(method, path, headers=None, data=None, form=None, timeout=180):
    hdrs = {}
    if headers:
        hdrs.update(headers)
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
        try:
            return resp.status, json.loads(raw)
        except:
            return resp.status, raw.decode()
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except:
            return e.code, raw.decode()
    except Exception as e:
        return 0, str(e)


def req_binary(method, path, headers=None, timeout=180):
    hdrs = {}
    if headers:
        hdrs.update(headers)
    url = f"{BASE}{path}"
    r = urllib.request.Request(url, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        raw = resp.read()
        return resp.status, raw, dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, raw, dict(e.headers)
    except Exception as e:
        return 0, str(e).encode(), {}


LOREM_PATTERN = re.compile(r'lorem\s+ipsum', re.IGNORECASE)
SERVICE_PATTERN = re.compile(r'service\s+[123](?:\s|$|[,\.\-])', re.IGNORECASE)
LEADFORDGE_PATTERN = re.compile(r'leadforge', re.IGNORECASE)
DUMMY_CONTACT_PATTERN = re.compile(r'(example\.com|555-0100|123\s+main\s+st)', re.IGNORECASE)
FAKE_TESTIMONIAL_PATTERN = re.compile(
    r'(best\s+(?:company|service|product)\s+ever|'
    r'john\s+doe|jane\s+doe|'
    r'fake\s+(?:review|testimonial))',
    re.IGNORECASE,
)


def validate_fidelity(html, business_name, host):
    """Run fidelity checks on generated HTML. Returns (pass, issues)."""
    issues = []

    if not html or len(html) < 100:
        issues.append("HTML is empty or too short")
        return False, issues

    if "<!doctype html" not in html.lower() and "<html" not in html.lower():
        issues.append("Not valid HTML")

    if LOREM_PATTERN.search(html):
        issues.append("Lorem Ipsum present")

    if SERVICE_PATTERN.search(html):
        issues.append("Generic services (Service 1/2/3) present")

    if LEADFORDGE_PATTERN.search(html):
        issues.append("LeadForge branding present")

    if DUMMY_CONTACT_PATTERN.search(html):
        issues.append("Dummy contact information present")

    if FAKE_TESTIMONIAL_PATTERN.search(html):
        issues.append("Fake testimonials present")

    if business_name and business_name.lower() not in html.lower():
        issues.append(f"Business name '{business_name}' not found in HTML")

    return len(issues) == 0, issues


def validate_zip_structure(raw_zip, website_html_for_preview):
    """Validate ZIP file structure and content. Returns (pass, issues, details)."""
    issues = []
    details = {}

    if not raw_zip or len(raw_zip) == 0:
        return False, ["ZIP is empty"], details

    try:
        zf = ZipFile(io.BytesIO(raw_zip))
    except Exception as e:
        return False, [f"ZIP cannot be opened: {e}"], details

    names = zf.namelist()
    details["files"] = names
    details["file_count"] = len(names)

    if not names:
        issues.append("ZIP has no files")
        return False, issues, details

    has_index = any("index.html" in n.lower() for n in names)
    if not has_index:
        issues.append("No index.html in ZIP")

    if has_index:
        for name in names:
            if "index.html" in name.lower():
                content = zf.read(name).decode("utf-8", errors="replace")
                details["index_html_size"] = len(content)

                if len(content) < 100:
                    issues.append("index.html is too small")

                if "<!doctype html" not in content.lower() and "<html" not in content.lower():
                    issues.append("index.html is not valid HTML")

                # Check image references in the ZIP index.html
                img_refs = re.findall(r'<img[^>]+src\s*=\s*"([^"]+)"', content, re.IGNORECASE)
                details["image_refs_in_zip_html"] = img_refs
                broken = []
                for ref in img_refs:
                    if ref.startswith("http://") or ref.startswith("https://"):
                        broken.append(f"Remote URL in ZIP: {ref}")
                    else:
                        ref_clean = ref.lstrip("./")
                        found = False
                        for n in names:
                            if n == ref_clean or n.endswith("/" + ref_clean) or ref_clean.endswith(n):
                                found = True
                                break
                        if not found:
                            broken.append(f"Missing asset: {ref}")
                if broken:
                    issues.extend(broken)
                details["broken_image_refs"] = broken

                # Check images in ZIP
                image_files = [n for n in names if any(
                    n.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]
                )]
                details["image_files_in_zip"] = image_files
                details["image_count"] = len(image_files)

                # Check for assets/images directory
                has_assets_dir = any("assets/images/" in n or "assets\\images\\" in n for n in names)
                details["has_assets_images_dir"] = has_assets_dir
                break

    return len(issues) == 0, issues, details


def validate_preview_html(html):
    """Check preview HTML contains real source content and images."""
    issues = []
    details = {}

    if not html:
        return False, ["Preview HTML is empty"], details

    details["html_size"] = len(html)
    details["has_doctype"] = "<!doctype html" in html.lower() or "<!DOCTYPE html" in html

    img_refs = re.findall(r'<img[^>]+src\s*=\s*"([^"]+)"', html, re.IGNORECASE)
    details["image_count"] = len(img_refs)
    details["image_urls"] = img_refs[:10]

    data_uri_count = sum(1 for ref in img_refs if ref.startswith("data:"))
    remote_count = sum(1 for ref in img_refs if ref.startswith("http://") or ref.startswith("https://"))
    local_count = len(img_refs) - data_uri_count - remote_count
    details["data_uri_images"] = data_uri_count
    details["remote_images"] = remote_count
    details["local_images"] = local_count

    if len(img_refs) == 0:
        issues.append("No images in preview HTML")

    sections = re.findall(r'<(?:section|div|h[1-6]|p|article|main|nav|header|footer)', html, re.IGNORECASE)
    details["visible_elements"] = len(sections)
    if len(sections) < 3:
        issues.append(f"Very few visible elements ({len(sections)})")

    return len(issues) == 0, issues, details


# ============================================================
# MAIN TEST
# ============================================================
print("=" * 70)
print("STEP 4 — FINAL PRODUCTION ACCEPTANCE")
print("=" * 70)

# --- Health check ---
print("\n--- HEALTH CHECK ---")
c, d = req_json("GET", "/health")
log("Backend online", c == 200 and isinstance(d, dict) and d.get("status") == "online")

# --- Auth ---
print("\n--- AUTHENTICATION ---")
c, d = req_json("POST", "/api/v1/auth/login", form={"username": "test@test.com", "password": "Test123!"})
token = d.get("access_token", "") if c == 200 and isinstance(d, dict) else ""
log("Login", bool(token), f"HTTP {c}" if not token else "")
if not token:
    print("FATAL: login failed")
    sys.exit(1)
H = {"Authorization": f"Bearer {token}"}

# --- Website chain ---
WEBSITES = [
    {"host": "kissthehippo.com", "name": "Kiss the Hippo Coffee", "url": "https://kissthehippo.com"},
    {"host": "stumptowncoffee.com", "name": "Stumptown Coffee Roasters", "url": "https://www.stumptowncoffee.com"},
]

for site in WEBSITES:
    host = site["host"]
    expected_name = site["name"]
    print(f"\n{'='*70}")
    print(f"SITE: {host}")
    print(f"{'='*70}")

    site_result = {
        "host": host,
        "job_id": "",
        "website_id": "",
        "provider": "",
        "fidelity": {},
        "preview": {},
        "zip": {},
    }

    # Create lead
    c, d = req_json("POST", "/api/v1/leads", headers=H, data={
        "url": site["url"],
        "company_name": f"Production Test {host}",
        "industry": "Food & Beverage",
    }, timeout=30)
    lead_id = d.get("data", {}).get("id") if c == 201 else None
    log(f"Create lead ({host})", bool(lead_id), f"HTTP {c}: {str(d)[:200]}")
    if not lead_id:
        site_result["fidelity"] = {"error": "lead creation failed"}
        RESULTS.append(site_result)
        continue

    # Build profile
    c, d = req_json("POST", "/api/v1/generation/build", headers=H, data={"lead_id": lead_id}, timeout=120)
    log(f"Build profile ({host})", c == 200, f"HTTP {c}: {str(d)[:200]}")

    # Submit async job
    c, d = req_json("POST", "/api/v1/generation/jobs", headers=H, data={"lead_id": lead_id}, timeout=30)
    job_id = d.get("data", {}).get("job_id") if c in (200, 202) else None
    log(f"Submit job ({host})", bool(job_id), f"HTTP {c}: {str(d)[:200]}")
    if not job_id:
        site_result["fidelity"] = {"error": "job submission failed"}
        RESULTS.append(site_result)
        continue
    site_result["job_id"] = job_id

    # Poll
    total_wait = 0
    poll_interval = 5
    max_wait = 420
    final_status = ""
    provider_used = ""
    website_id = ""
    gen_html = ""
    gen_time = 0

    print(f"  Polling job {job_id[:16]}...", end="", flush=True)
    while total_wait < max_wait:
        time.sleep(poll_interval)
        total_wait += poll_interval
        c, d = req_json("GET", f"/api/v1/generation/jobs/{job_id}", headers=H, timeout=30)
        if c != 200:
            print(f"\n  Poll error: HTTP {c}")
            break
        data = d.get("data", {})
        status = data.get("status", "")
        website_id = data.get("website_id") or website_id
        provider_used = data.get("provider_used") or provider_used
        gen_time = data.get("generation_time", 0) or gen_time
        print(".", end="", flush=True)

        if status == "succeeded":
            final_status = "succeeded"
            gen_html = data.get("html", "")
            print(f" DONE ({total_wait}s)")
            break
        elif status == "failed":
            final_status = "failed"
            error = data.get("error", "Unknown")
            print(f"\n  FAILED: {error[:300]}")
            break

    if not final_status:
        print(f"\n  TIMEOUT after {max_wait}s")

    site_result["website_id"] = website_id
    site_result["provider"] = provider_used

    log(f"Generation succeeded ({host})", final_status == "succeeded",
        f"provider={provider_used} website_id={website_id[:12] if website_id else 'N/A'} duration={total_wait}s")

    if final_status != "succeeded" or not website_id:
        RESULTS.append(site_result)
        continue

    # --- Preview ---
    print(f"\n  --- PREVIEW ({host}) ---")
    c, d = req_json("GET", f"/api/v1/generation/websites/{website_id}", headers=H, timeout=30)
    log(f"Preview API 200 ({host})", c == 200, f"HTTP {c}")

    preview_html = ""
    if c == 200 and d.get("data"):
        preview_html = d["data"].get("html", "")
        ok, pv_issues, pv_details = validate_preview_html(preview_html)
        log(f"Preview has visible content ({host})", ok and pv_details.get("visible_elements", 0) >= 3,
            f"issues={pv_issues} elements={pv_details.get('visible_elements', 0)}")
        log(f"Preview has images ({host})", pv_details.get("image_count", 0) > 0,
            f"count={pv_details.get('image_count', 0)} remote={pv_details.get('remote_images', 0)} data_uri={pv_details.get('data_uri_images', 0)}")
        site_result["preview"] = {
            "html_size": pv_details.get("html_size", 0),
            "image_count": pv_details.get("image_count", 0),
            "visible_elements": pv_details.get("visible_elements", 0),
            "remote_images": pv_details.get("remote_images", 0),
            "data_uri_images": pv_details.get("data_uri_images", 0),
        }
    else:
        site_result["preview"] = {"error": f"HTTP {c}"}

    # --- Fidelity ---
    print(f"\n  --- FIDELITY ({host}) ---")
    fid_ok, fid_issues = validate_fidelity(preview_html or gen_html, expected_name, host)
    log(f"Fidelity check ({host})", fid_ok, f"issues={fid_issues}")
    site_result["fidelity"] = {
        "pass": fid_ok,
        "issues": fid_issues,
        "missing_content": [i for i in fid_issues if "not found" in i.lower() or "missing" in i.lower()],
        "invented_content": [i for i in fid_issues if "lorem" in i.lower() or "generic" in i.lower() or "fake" in i.lower() or "dummy" in i.lower() or "leadforge" in i.lower()],
        "broken_images": [i for i in fid_issues if "missing asset" in i.lower() or "remote url" in i.lower()],
    }

    # --- ZIP ---
    print(f"\n  --- ZIP ({host}) ---")
    c, raw, headers = req_binary("GET", f"/api/v1/generation/websites/{website_id}/download", headers=H, timeout=120)
    log(f"ZIP download HTTP 200 ({host})", c == 200, f"HTTP {c}: {raw[:200].decode('utf-8', errors='replace') if isinstance(raw, bytes) and c != 200 else ''}")
    if c == 200 and isinstance(raw, bytes):
        log(f"ZIP non-empty ({host})", len(raw) > 0, f"size={len(raw)}")

        zip_ok, zip_issues, zip_details = validate_zip_structure(raw, preview_html)
        log(f"ZIP structure valid ({host})", zip_ok, f"issues={zip_issues}")

        # Build the expected safe filename
        safe_name = re.sub(r'[^a-z0-9]', '-', (site.get("name", "leadforge-website")).lower()).strip('-') or "leadforge-website"
        expected_filename = f"{safe_name}-{website_id}.zip"

        site_result["zip"] = {
            "size_bytes": len(raw),
            "filename": expected_filename,
            "file_count": zip_details.get("file_count", 0),
            "files": zip_details.get("files", []),
            "image_files_in_zip": zip_details.get("image_files_in_zip", []),
            "has_assets_images_dir": zip_details.get("has_assets_images_dir", False),
            "image_refs_in_zip_html": zip_details.get("image_refs_in_zip_html", []),
            "broken_image_refs": zip_details.get("broken_image_refs", []),
            "index_html_size": zip_details.get("index_html_size", 0),
        }
    else:
        site_result["zip"] = {"error": f"HTTP {c}"}

    RESULTS.append(site_result)


# ============================================================
# BACKEND TESTS
# ============================================================
print(f"\n{'='*70}")
print("BACKEND TESTS")
print(f"{'='*70}")
import subprocess
test_result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
    capture_output=True, text=True, timeout=180,
    cwd=os.path.dirname(os.path.abspath(__file__)) or "."
)
test_output = test_result.stdout + test_result.stderr
test_pass = test_result.returncode == 0
log("Backend tests pass", test_pass, test_output[-500:] if not test_pass else "")

# Parse test counts
import re as _re
m = _re.search(r'(\d+) passed', test_output)
test_count = int(m.group(1)) if m else 0
m_fail = _re.search(r'(\d+) failed', test_output)
test_fail_count = int(m_fail.group(1)) if m_fail else 0


# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'='*70}")
print("FINAL REPORT")
print(f"{'='*70}")

print(f"\nBackend tests: {test_count} passed, {test_fail_count} failed")
print()

for r in RESULTS:
    host = r["host"]
    print(f"--- {host} ---")
    print(f"  job_id:     {r['job_id']}")
    print(f"  website_id: {r['website_id']}")
    print(f"  provider:   {r['provider']}")
    print(f"  fidelity:   {'PASS' if r['fidelity'].get('pass') else 'FAIL'}")
    if r["fidelity"].get("issues"):
        for i in r["fidelity"]["issues"]:
            print(f"    - {i}")
    print(f"  preview:    images={r['preview'].get('image_count', 'N/A')} "
          f"elements={r['preview'].get('visible_elements', 'N/A')} "
          f"size={r['preview'].get('html_size', 'N/A')} bytes")
    print(f"  zip:        size={r['zip'].get('size_bytes', 'N/A')} bytes "
          f"files={r['zip'].get('file_count', 'N/A')} "
          f"images={len(r['zip'].get('image_files_in_zip', []))}")
    if r["zip"].get("broken_image_refs"):
        print(f"    BROKEN REFS: {r['zip']['broken_image_refs']}")
    print()

# Aggregate
all_pass = PASS > 0 and FAIL == 0
all_fidelity_pass = all(r.get("fidelity", {}).get("pass", False) for r in RESULTS)
all_zip_ok = all(r.get("zip", {}).get("size_bytes", 0) > 0 and not r.get("zip", {}).get("broken_image_refs") for r in RESULTS)
all_preview_ok = all(r.get("preview", {}).get("image_count", 0) > 0 for r in RESULTS)

print(f"Overall: {PASS} passed, {FAIL} failed")
print(f"Fidelity all pass: {all_fidelity_pass}")
print(f"ZIP all valid:     {all_zip_ok}")
print(f"Preview all have images: {all_preview_ok}")
print(f"Backend tests:     {test_pass}")

print(f"\n{'='*70}")
if all_pass and all_fidelity_pass and all_zip_ok and all_preview_ok and test_pass:
    print("RESULT: ALL CHECKS PASSED")
else:
    print("RESULT: SOME CHECKS FAILED — see details above")
print(f"{'='*70}")

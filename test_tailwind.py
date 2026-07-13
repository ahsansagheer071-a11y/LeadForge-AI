"""Quick test of tailwindcss.com build (was failing with UnboundLocalError)."""
import urllib.request, urllib.parse, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "https://leadforge-ai-production-eff1.up.railway.app"

def req(method, path, headers=None, data=None, form=None, timeout=180):
    hdrs = {} if headers is None else dict(headers)
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

# Login
c, d = req("POST", "/api/v1/auth/login", form={"username": "test@test.com", "password": "Test123!"})
token = d.get("access_token", "") if c == 200 and isinstance(d, dict) else ""
print(f"Login: HTTP {c}, token={token[:20] if token else 'NONE'}...")
if not token:
    print("FAILED TO LOGIN")
    sys.exit(1)

H = {"Authorization": f"Bearer {token}"}

# Create lead for tailwindcss.com
c, d = req("POST", "/api/v1/leads", headers=H, data={
    "url": "https://tailwindcss.com",
    "company_name": "Tailwind Test",
    "industry": "Technology",
}, timeout=30)
lead_id = d.get("data", {}).get("id") if c == 201 else None
print(f"Create lead: HTTP {c}, lead_id={lead_id}")

if not lead_id:
    print("FAILED TO CREATE LEAD")
    sys.exit(1)

# Build profile (was failing with UnboundLocalError)
print("\nTesting build_profile for tailwindcss.com...")
c, d = req("POST", "/api/v1/generation/build", headers=H, data={"lead_id": lead_id}, timeout=120)
print(f"Build profile: HTTP {c}", end="")
if c == 200:
    print(" ✅ SUCCESS - section_type bug is fixed!")
else:
    print(f" ❌ FAILED: {str(d)[:300]}")
    # Continue to test the job anyway

# Submit generation job
print("\nTesting async generation for tailwindcss.com...")
c, d = req("POST", "/api/v1/generation/jobs", headers=H, data={"lead_id": lead_id}, timeout=30)
job_id = d.get("data", {}).get("job_id") if c in (200, 202) else None
print(f"Submit job: HTTP {c}, job_id={job_id}")

if job_id:
    for i in range(60):
        time.sleep(5)
        c, d = req("GET", f"/api/v1/generation/jobs/{job_id}", headers=H, timeout=30)
        if c != 200:
            print(f"  Poll error HTTP {c}")
            break
        status = d.get("data", {}).get("status", "")
        progress = d.get("data", {}).get("progress", "")
        print(f"  [{i*5}s] status={status} progress={progress}")
        if status == "succeeded":
            website_id = d.get("data", {}).get("website_id", "")
            print(f"\n✅ Generation succeeded! website_id={website_id}")
            break
        elif status == "failed":
            error = d.get("data", {}).get("error", "Unknown")
            print(f"\n❌ Generation failed: {error}")
            break
else:
    print("FAILED TO SUBMIT JOB (may already have active job)")

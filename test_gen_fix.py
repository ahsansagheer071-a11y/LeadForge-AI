"""Quick test to verify the provider content fix works in production."""
import urllib.request, urllib.parse, urllib.error, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "https://leadforge-ai-production-eff1.up.railway.app"


def req(method, path, headers=None, data=None, form=None, timeout=180):
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
    for _ in range(3):
        r = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        try:
            resp = urllib.request.urlopen(r, timeout=timeout)
            raw = resp.read()
            try:
                return resp.status, json.loads(raw)
            except:
                return resp.status, raw.decode()
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 307, 308) and e.headers.get("Location"):
                url = e.headers["Location"]
                if url.startswith("/"):
                    url = f"{BASE}{url}"
                body = None
                continue
            raw = e.read()
            try:
                return e.code, json.loads(raw)
            except:
                return e.code, raw.decode()
        except Exception as e:
            return 0, str(e)
    return 0, "Too many redirects"


def main():
    status, data = req("POST", "/api/v1/auth/login", form={"username": "test@test.com", "password": "Test123!"})
    if status != 200:
        print(f"Login failed: {status}")
        return
    token = data["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    print("[1] Login OK")

    status, leads = req("GET", "/api/v1/leads/", headers=auth)
    if isinstance(leads, dict) and "data" in leads:
        leads = leads["data"]
    if not isinstance(leads, list):
        leads = []

    kissthehippo_id = None
    for lead in leads:
        ws = (lead.get("website") or "").lower()
        bid = (lead.get("business_name") or "").lower()
        if "kissthehippo" in ws or "kiss the hippo" in bid:
            kissthehippo_id = lead["id"]
            break

    if kissthehippo_id:
        print(f"[2] Found kissthehippo lead: {kissthehippo_id}")
    else:
        print("[2] Creating kissthehippo lead...")
        status, data = req("POST", "/api/v1/leads", headers=auth, data={"url": "https://kissthehippo.com", "company_name": "Kiss the Hippo Coffee", "industry": "Coffee Retail"})
        print(f"    Create response: {status} {str(data)[:500]}")
        if status in (200, 201):
            # Response is StandardResponse with data wrapper
            if isinstance(data, dict):
                inner = data.get("data")
                if isinstance(inner, dict):
                    kissthehippo_id = inner.get("id")
                elif isinstance(inner, str):
                    kissthehippo_id = inner
                if not kissthehippo_id:
                    kissthehippo_id = data.get("id")
        if not kissthehippo_id:
            # Check leads list for existing
            print("    Searching leads list...")
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict) and "items" in data["data"]:
                for lead in data["data"]["items"]:
                    ws = (lead.get("website") or "").lower()
                    if "kissthehippo" in ws:
                        kissthehippo_id = lead.get("id")
                        break
            if not kissthehippo_id:
                print(f"  Could not create or find lead")
                return
    print(f"    Lead ID: {kissthehippo_id}")

    print("[3] Triggering generation...")
    status, data = req("POST", "/api/v1/generation/jobs", headers=auth, data={"lead_id": kissthehippo_id})
    print(f"    Status: {status}")
    if status not in (200, 201, 202):
        print(f"    Error: {str(data)[:500]}")
        return

    job_id = data.get("job_id") or data.get("id")
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        job_id = job_id or data["data"].get("job_id")
    print(f"    Job ID: {job_id}")

    print("[4] Polling for completion...")
    job = None
    for i in range(80):
        time.sleep(5)
        status, job = req("GET", f"/api/v1/generation/jobs/{job_id}", headers=auth)
        if isinstance(job, dict) and "data" in job:
            job = job["data"]
        st = job.get("status", "unknown")
        prog = job.get("progress", "")
        print(f"    [{(i+1)*5:3d}s] {st} | {prog}")
        if st in ("succeeded", "failed"):
            break

    if not job:
        print("No job result!")
        return

    final_status = job.get("status")
    print(f"\n{'='*60}")
    print(f"RESULT: {final_status}")
    print(f"{'='*60}")

    if final_status == "succeeded":
        html = job.get("html", "")
        html_len = len(html)
        has_doctype = "<!doctype html>" in html.lower() or "<!DOCTYPE html>" in html
        has_closing = "</html>" in html.lower()
        has_content = html_len > 1000
        has_business = "kiss the hippo" in html.lower()
        provider = job.get("provider_used", "unknown")

        print(f"  Provider:            {provider}")
        print(f"  HTML length:         {html_len:,} chars")
        print(f"  Has DOCTYPE:         {has_doctype}")
        print(f"  Has </html>:         {has_closing}")
        print(f"  Has content (>1KB):  {has_content}")
        print(f"  Has business name:   {has_business}")
        print(f"  Preview path:        {job.get('preview_path', 'N/A')}")
        print(f"  Gen time:            {job.get('generation_time', 'N/A')}s")
        print(f"\n  First 1500 chars:\n  {html[:1500]}")

        if has_doctype and has_closing and has_content and has_business:
            print(f"\n*** PASS: AI generated a real, faithful website redesign! ***")
        elif html_len < 1000:
            print(f"\n*** FAIL: HTML too short ({html_len} bytes) ***")
        else:
            print(f"\n*** PARTIAL: HTML exists but quality issues detected ***")

    elif final_status == "failed":
        print(f"  Error: {job.get('error', 'unknown')}")


if __name__ == "__main__":
    main()

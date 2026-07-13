"""Test 2nd website: stumptowncoffee.com"""
import urllib.request, urllib.parse, json, sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = "https://leadforge-ai-production-eff1.up.railway.app"

def req(method, path, headers=None, data=None, form=None, timeout=180):
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
        except Exception as e: return 0, str(e)
    return 0, "Too many redirects"

def main():
    s, d = req("POST", "/api/v1/auth/login", form={"username": "test@test.com", "password": "Test123!"})
    token = d["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    print("[1] Login OK")

    # Find or create stumptowncoffee lead
    s, leads = req("GET", "/api/v1/leads/", headers=auth)
    lead_list = leads.get("data", {}).get("items", []) if isinstance(leads, dict) else leads
    stump_id = None
    for lead in lead_list:
        ws = (lead.get("website") or "").lower()
        if "stumptown" in ws:
            stump_id = lead["id"]
            break

    if stump_id:
        print(f"[2] Found stumptown lead: {stump_id}")
    else:
        print("[2] Creating stumptowncoffee lead...")
        s, d = req("POST", "/api/v1/leads", headers=auth, data={"url": "https://www.stumptowncoffee.com", "company_name": "Stumptown Coffee Roasters", "industry": "Coffee Roasters"})
        print(f"    Status: {s}")
        if s in (200, 201):
            inner = d.get("data", d) if isinstance(d, dict) else d
            stump_id = inner.get("id") if isinstance(inner, dict) else None
        if not stump_id:
            print(f"    Failed: {str(d)[:300]}")
            return
    print(f"    Lead ID: {stump_id}")

    # Trigger generation
    print("[3] Triggering generation...")
    s, d = req("POST", "/api/v1/generation/jobs", headers=auth, data={"lead_id": stump_id})
    if s not in (200, 201, 202):
        print(f"    Error: {str(d)[:500]}")
        return
    job_id = d.get("job_id") or d.get("id")
    if isinstance(d, dict) and "data" in d and isinstance(d["data"], dict):
        job_id = job_id or d["data"].get("job_id")
    print(f"    Job ID: {job_id}")

    # Poll
    print("[4] Polling...")
    job = None
    for i in range(80):
        time.sleep(5)
        s, job = req("GET", f"/api/v1/generation/jobs/{job_id}", headers=auth)
        if isinstance(job, dict) and "data" in job:
            job = job["data"]
        st = job.get("status", "unknown")
        print(f"    [{(i+1)*5:3d}s] {st} | {job.get('progress', '')}")
        if st in ("succeeded", "failed"):
            break

    if not job:
        print("No result!")
        return

    final = job.get("status")
    print(f"\n{'='*60}")
    print(f"RESULT: {final}")
    print(f"{'='*60}")

    if final == "succeeded":
        html = job.get("html", "")
        has_doctype = "<!doctype html>" in html.lower() or "<!DOCTYPE html>" in html
        has_closing = "</html>" in html.lower()
        has_content = len(html) > 1000
        has_business = "stumptown" in html.lower()
        print(f"  HTML length:     {len(html):,} chars")
        print(f"  DOCTYPE:         {has_doctype}")
        print(f"  </html>:         {has_closing}")
        print(f"  Content >1KB:    {has_content}")
        print(f"  Business name:   {has_business}")
        print(f"  Preview:         {job.get('preview_path', 'N/A')}")
        print(f"\n  Body content:")

        m = re.search(r"<body>(.*?)</body>", html, re.DOTALL)
        if m:
            body = m.group(1).strip()
            print(body[:3000])
        else:
            print(html[:3000])

        if has_doctype and has_closing and has_content and has_business:
            print(f"\n*** PASS ***")
        else:
            print(f"\n*** ISSUES DETECTED ***")
    elif final == "failed":
        print(f"  Error: {job.get('error', 'unknown')}")

if __name__ == "__main__":
    main()

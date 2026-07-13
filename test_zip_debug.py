"""Debug ZIP download issue - check what the download endpoint returns."""
import urllib.request, json, ssl, io, zipfile

BASE = "https://leadforge-ai-production-eff1.up.railway.app"

# Login
body = urllib.parse.urlencode({"username": "test@test.com", "password": "Test123!"}).encode()
r = urllib.request.Request(f"{BASE}/api/v1/auth/login", data=body, method="POST")
r.add_header("Content-Type", "application/x-www-form-urlencoded")
resp = urllib.request.urlopen(r, timeout=30)
token = json.loads(resp.read())["access_token"]

H = {"Authorization": f"Bearer {token}"}

website_id = "fb707999-db9f-4ca0-b0e5-693ef3cf2d9d"
url = f"{BASE}/api/v1/generation/websites/{website_id}/download"
req = urllib.request.Request(url, headers=H, method="GET")
try:
    resp = urllib.request.urlopen(req, timeout=60)
    raw = resp.read()
    print(f"Status: {resp.status}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    print(f"Content-Disposition: {resp.headers.get('Content-Disposition')}")
    print(f"Size: {len(raw)} bytes")
    if len(raw) > 0:
        zf = zipfile.ZipFile(io.BytesIO(raw))
        print(f"Files: {zf.namelist()}")
    else:
        print("EMPTY ZIP!")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    if hasattr(e, "code"):
        print(f"HTTP Code: {e.code}")
        raw = e.read()
        print(f"Body: {raw[:500]}")

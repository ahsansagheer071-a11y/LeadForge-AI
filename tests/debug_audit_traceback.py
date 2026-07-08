"""Get the full audit traceback from Railway."""
import requests
import random
import string
import json

base = "https://leadforge-ai-production-eff1.up.railway.app"
s = requests.Session()

email = f"debug{random.randint(10000,99999)}@test.com"
r = s.post(base + "/api/v1/auth/register",
           data={"email": email, "password": "Test123!", "full_name": "Debug User"})
if r.status_code == 201:
    r = s.post(base + "/api/v1/auth/login",
               data={"username": email, "password": "Test123!"})
else:
    r = s.post(base + "/api/v1/auth/login",
               data={"username": "test@test.com", "password": "Test123!"})
token = (r.json().get("access_token") or
         (r.json().get("data") or {}).get("access_token", ""))
H = {"Authorization": f"Bearer {token}"}

r = s.post(base + "/api/v1/leads", headers=H,
           json={"name": "Debug Biz", "website": "https://example.com",
                 "industry": "Tech", "city": "NYC", "country": "US",
                 "phone": "1234567890"})
print(f"Create Lead: {r.status_code} {r.text[:300]}")
lead_data = r.json()
lead_id = (lead_data.get("data") or {}).get("id") or lead_data.get("id", "")
print(f"Lead ID: {lead_id}")

if lead_id:
    r = s.post(base + f"/api/v1/leads/{lead_id}/analyze",
               headers=H, json={"url": "https://example.com"})
    print(f"Analyze: {r.status_code}")

    r = s.post(base + "/api/v1/audits/run",
               headers=H, json={"lead_id": lead_id, "provider": "groq"})
    print(f"Audit: {r.status_code}")
    print("FULL RESPONSE:")
    print(r.text[:3000])

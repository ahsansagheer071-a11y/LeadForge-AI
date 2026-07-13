import os
import sys
import time
import uuid
import httpx

API_BASE = "https://leadforge-ai-production-eff1.up.railway.app/api/v1"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Password123!"
COMPLEX_URL = "https://kissthehippo.com"

def run_test():
    with httpx.Client(base_url=API_BASE, timeout=60.0) as client:
        # 1. Register User
        ts = int(time.time())
        email = f"test_{ts}@example.com"
        password = "Password123!"
        print(f"1. Registering {email}...")
        resp = client.post("/auth/register", json={"email": email, "password": password, "full_name": "Test User"})
        if resp.status_code != 201:
            print("Register failed:", resp.text)
            return
            
        print("   Logging in...")
        resp = client.post("/auth/login", data={"username": email, "password": password})
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create Lead for complex site
        print(f"2. Creating lead for {COMPLEX_URL}...")
        lead_payload = {
            "company_name": "Kiss The Hippo",
            "url": COMPLEX_URL,
            "industry": "Ecommerce"
        }
        resp = client.post("/leads", json=lead_payload, headers=headers)
        if resp.status_code not in (200, 201):
            print("Lead creation failed:", resp.text)
            return
        lead_id = resp.json()["data"]["id"]
        print(f"   Lead ID: {lead_id}")
        
        # 3. Start Job
        print("3. Starting async generation job...")
        resp = client.post("/generation/jobs", json={"lead_id": lead_id}, headers=headers)
        if resp.status_code != 202:
            print("Job creation failed:", resp.text)
            return
        
        job_data = resp.json()["data"]
        job_id = job_data["job_id"]
        print(f"   Job ID: {job_id}")
        
        # 4. Poll Job
        print("4. Polling job...")
        start_time = time.time()
        website_id = None
        while True:
            resp = client.get(f"/generation/jobs/{job_id}", headers=headers)
            if resp.status_code != 200:
                print(f"Poll failed: {resp.status_code} {resp.text}")
                time.sleep(3)
                continue
            
            poll_data = resp.json()["data"]
            status = poll_data["status"]
            progress = poll_data["progress"]
            print(f"   Status: {status} | Progress: {progress}")
            
            if status == "succeeded":
                website_id = poll_data["website_id"]
                gen_time = poll_data.get("generation_time", 0)
                print(f"   Success! Website ID: {website_id} in {gen_time}s")
                break
            elif status == "failed":
                print(f"   Job Failed! Error: {poll_data.get('error')}")
                return
            
            time.sleep(3)
            
        total_time = time.time() - start_time
        print(f"Total generation duration: {total_time:.1f}s")
        
        # 5. Preview HTML
        print(f"5. Fetching Preview for {website_id}...")
        resp = client.get(f"/generation/websites/{website_id}", headers=headers)
        print(f"   Preview fetch status: {resp.status_code}")
        
        # 6. Download ZIP
        print(f"6. Downloading ZIP for {website_id}...")
        resp = client.get(f"/generation/websites/{website_id}/download", headers=headers)
        if resp.status_code == 200:
            size = len(resp.content)
            filename = resp.headers.get("Content-Disposition", "unknown").split("filename=")[-1].strip('"')
            print(f"   ZIP downloaded successfully! Filename: {filename}, Size: {size} bytes")
        else:
            print(f"   ZIP download failed: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    run_test()

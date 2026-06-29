import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_and_me():
    # Attempt to login
    response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "Password1!"})
    print("Login status:", response.status_code)
    print("Login body:", response.json())
    
    # Let's say we register the user first if login fails
    if response.status_code != 200:
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com", 
            "password": "Password1!", 
            "full_name": "Test User",
            "is_superuser": False
        })
        response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "Password1!"})
        print("Login status after register:", response.status_code)
        print("Login body:", response.json())

    # Get the token
    json_resp = response.json()
    if "data" in json_resp and "access_token" in json_resp["data"]:
        token = json_resp["data"]["access_token"]
        print("Token extracted from data.access_token:", token[:10] + "...")
        
        # Test Swagger behavior: if Swagger looks for root access_token, it gets None
        swagger_token = json_resp.get("access_token")
        print("Token extracted from root (Swagger simulation):", swagger_token)
        
        # Call /me with the actual token
        me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        print("Me status with correct token:", me_resp.status_code)
        print("Me body with correct token:", me_resp.json())
        
        # Call /me with undefined
        me_resp_undef = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer undefined"})
        print("Me status with 'undefined':", me_resp_undef.status_code)
        print("Me body with 'undefined':", me_resp_undef.json())

test_login_and_me()

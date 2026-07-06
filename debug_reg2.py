"""Debug registration flow with network monitoring"""
import subprocess, time, sys, os
from playwright.sync_api import sync_playwright

os.environ["JWT_SECRET"] = "ta1nIFT27VE0fZAh9gsbdKr5PQDwN6cRuLeSO483CjYqWmlUMHkyzvGxiBpXoJ"
ROOT = r"D:\Leadforge AI"

procs = []
p = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                     cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
procs.append(p)
p2 = subprocess.Popen(["npm.cmd", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"],
                      cwd=os.path.join(ROOT, "frontend"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
procs.append(p2)

for i in range(30):
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:8000/health", timeout=2)
        urllib.request.urlopen("http://localhost:3000", timeout=2)
        print(f"Ready after {i+1}s")
        break
    except:
        time.sleep(1)
else:
    print("Not ready"); sys.exit(1)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page()

    # Network monitoring
    requests = []
    page.on("request", lambda r: requests.append(("REQ", r.method, r.url)))
    page.on("response", lambda r: requests.append(("RES", r.status, r.url)))

    # Console monitoring
    console_msgs = []
    page.on("console", lambda msg: console_msgs.append((msg.type, msg.text)))

    page.goto("http://localhost:3000/register", wait_until="networkidle")
    print(f"Page loaded")

    # Fill
    page.locator("#name").fill("Test User")
    page.locator("#email").fill("testuser@example.com")
    page.locator("#password").fill("TestPass123!")
    page.locator("#confirm").fill("TestPass123!")
    
    print("Submitting...")
    page.locator("button[type='submit']").filter(has_text="Create account").click()
    page.wait_for_timeout(10000)

    print(f"\nURL after 5s: {page.url}")

    # Show relevant network requests
    print(f"\nNetwork requests:")
    for t, m, u in requests:
        if "localhost" in u or "auth" in u:
            print(f"  {t} {m} {u.split('?')[0]}")
    
    if console_msgs:
        print(f"\nConsole messages:")
        for t, msg in console_msgs[-10:]:
            print(f"  [{t}] {msg[:200]}")
    
    # Check page HTML for redirect/navigation state
    state = page.evaluate("""() => {
        const el = document.querySelector('[data-sonner-toast]');
        const toastText = el ? el.textContent.trim() : null;
        const inputs = document.querySelectorAll('input');
        const vals = Array.from(inputs).map(i => ({id: i.id, val: i.value}));
        const errors = document.querySelectorAll('.text-red-500, .text-red-600, [role=alert]');
        const errorTexts = Array.from(errors).map(e => e.textContent.trim());
        return { url: window.location.href, toastText, inputVals: vals, errorTexts };
    }""")
    print(f"\nPage state: {json.dumps(state, indent=2)}")

    page.screenshot(path="debug_register2.png")
    print("Screenshot saved")

    browser.close()

import json
for p in procs:
    p.terminate()
    p.wait(timeout=5)

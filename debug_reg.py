"""Debug registration flow"""
import subprocess, time, sys, os
from playwright.sync_api import sync_playwright

os.environ["JWT_SECRET"] = "ta1nIFT27VE0fZAh9gsbdKr5PQDwN6cRuLeSO483CjYqWmlUMHkyzvGxiBpXoJ"
ROOT = r"D:\Leadforge AI"

# Start backend only
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

    page.goto("http://localhost:3000/register", wait_until="networkidle")
    print(f"Page loaded: {page.title()}")

    # Check form elements
    html = page.evaluate("""() => {
        const inputs = document.querySelectorAll('input');
        return Array.from(inputs).map(i => ({id: i.id, name: i.name, type: i.type, placeholder: i.placeholder}));
    }""")
    print(f"Inputs: {html}")

    # Check button
    btn = page.evaluate("""() => {
        const b = document.querySelector('button[type=submit]');
        if (!b) return 'NOT FOUND';
        return {text: b.textContent.trim(), disabled: b.disabled};
    }""")
    print(f"Button: {btn}")

    # Fill and submit
    page.locator("#name").fill("Test User")
    page.locator("#email").fill("testuser@example.com")
    page.locator("#password").fill("TestPass123!")
    page.locator("#confirm").fill("TestPass123!")
    page.wait_for_timeout(500)
    
    print("Fields filled, checking values...")
    vals = page.evaluate("""() => {
        const i = document.querySelectorAll('input');
        return Array.from(i).map(x => ({id: x.id, val: x.value}));
    }""")
    print(f"Values: {vals}")

    print("Clicking submit...")
    page.locator("button[type='submit']").filter(has_text="Create account").click()
    page.wait_for_timeout(3000)
    
    print(f"URL after click: {page.url}")
    
    # Check for error messages
    text = page.evaluate("""() => document.body.innerText""")
    print(f"Page text:\n{text[:1000]}")

    # Check console for errors
    logs = page.evaluate("""() => {
        // Check if there's any error state
        return document.querySelector('.text-red')?.textContent || 'no visible error';
    }""")
    print(f"Visible errors: {logs}")
    
    # Also check react-hook-form errors
    form_errors = page.evaluate("""() => {
        const er = document.querySelectorAll('[role=alert], .form-error, .text-red-500');
        return Array.from(er).map(e => e.textContent.trim());
    }""")
    print(f"Form errors: {form_errors}")
    
    # Take screenshot
    page.screenshot(path="debug_register.png")
    print("Screenshot saved to debug_register.png")

    browser.close()

for p in procs:
    p.terminate()
    p.wait(timeout=5)

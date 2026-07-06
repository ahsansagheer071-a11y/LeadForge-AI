"""
End-to-end auth tests: starts backend + frontend (discarding output),
runs all 6 Playwright scenarios, reports results.
"""
import subprocess, time, sys, os, json, base64
from playwright.sync_api import sync_playwright

os.environ["JWT_SECRET"] = "ta1nIFT27VE0fZAh9gsbdKr5PQDwN6cRuLeSO483CjYqWmlUMHkyzvGxiBpXoJ"
ROOT = r"D:\Leadforge AI"
FRONT = "http://localhost:3000"
EMAIL = "testuser@example.com"
PASS = "TestPass123!"
NAME = "Test User"

def start(cmd, cwd):
    return subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Clean test user from DB before starting
subprocess.run([sys.executable, os.path.join(ROOT, "clean_db.py")], cwd=ROOT, capture_output=True, text=True)
print("DB cleaned")

procs = []
procs.append(start([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], ROOT))
procs.append(start(["npm.cmd", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"],
                    os.path.join(ROOT, "frontend")))

for i in range(60):
    import urllib.request
    ok = True
    try:
        urllib.request.urlopen("http://localhost:8000/health", timeout=2)
    except:
        ok = False
    try:
        urllib.request.urlopen("http://localhost:3000", timeout=2)
    except:
        ok = False
    if ok:
        print(f"Both up after {i+1}s")
        break
    time.sleep(1)
else:
    print("FAIL: servers not ready"); sys.exit(1)

results = []

def run_scenario(n, desc, fn):
    print(f"\n{'='*60}")
    print(f"SCENARIO {n}: {desc}")
    try:
        fn()
        print(f"  -> [PASS]")
        results.append((n, desc, "PASS", ""))
    except AssertionError as e:
        print(f"  -> [FAIL] {e}")
        results.append((n, desc, "FAIL", str(e)))
    except Exception as e:
        print(f"  -> [FAIL] exception: {e}")
        import traceback; traceback.print_exc()
        results.append((n, desc, "FAIL", str(e)))

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])

    # ---- 1: Register ----
    def t1():
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.goto(f"{FRONT}/register", wait_until="networkidle")
        pg.fill("#name", NAME)
        pg.fill("#email", EMAIL)
        pg.fill("#password", PASS)
        pg.fill("#confirm", PASS)
        pg.locator("button[type='submit']").filter(has_text="Create account").click()
        # Wait for navigation to /login to complete
        pg.wait_for_url("**/login", timeout=10000)
        pg.wait_for_timeout(3000)  # let React render + Sonner animate in
        # Check entire DOM for any text mentioning "Account created"
        body_text = pg.evaluate("() => document.body.innerText")
        print(f"  /login page text (first 600ch): {body_text[:600]}")
        has_toast_text = "Account created" in body_text or "successfully" in body_text
        # Also check for sonner elements
        sonner_els = pg.evaluate("""() => {
            const r = [];
            document.querySelectorAll('*').forEach(el => {
                for (const a of el.getAttributeNames()) {
                    if (a.toLowerCase().includes('sonner') || a.toLowerCase().includes('toast')) {
                        r.push(a + '=' + el.getAttribute(a));
                    }
                }
            });
            return r;
        }""")
        print(f"  Sonner attrs found: {sonner_els}")
        assert has_toast_text or len(sonner_els) > 0, "No toast text found on /login page"
        ctx.close()
    run_scenario(1, "Register -> /login + toast", t1)

    # ---- 2: Login ----
    def t2():
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.goto(f"{FRONT}/login", wait_until="networkidle")
        pg.fill("#email", EMAIL)
        pg.fill("#password", PASS)
        pg.locator("button[type='submit']").filter(has_text="Sign in").click()
        pg.wait_for_timeout(5000)

        acc = pg.evaluate("localStorage.getItem('lf_access_token')")
        ref = pg.evaluate("localStorage.getItem('lf_refresh_token')")
        assert acc and len(acc) > 0, "Access token missing"
        assert ref and len(ref) > 0, "Refresh token missing"
        print(f"  access_token={len(acc)}ch refresh_token={len(ref)}ch")

        # Decode token
        p = acc.split(".")[1]
        pad = 4 - len(p) % 4
        if pad != 4: p += "=" * pad
        claims = json.loads(base64.urlsafe_b64decode(p))
        print(f"  Token sub={claims.get('sub','?')[:12]}... exp={claims.get('exp')}")

        st = json.loads(pg.evaluate("localStorage.getItem('lf_auth_v1')") or "{}")
        state = st.get("state", {})
        assert state.get("isAuthenticated") is True, "Not authenticated"
        assert state.get("user",{}).get("email") == EMAIL
        print(f"  isAuthenticated=True, user.email={EMAIL}")

        url = pg.url
        assert "/login" not in url, f"Still on /login: {url}"
        print(f"  Landed on {url}")
        ctx.close()
    run_scenario(2, "Login -> tokens, /me, dashboard", t2)

    # ---- 3: Wrong password ----
    def t3():
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.goto(f"{FRONT}/login", wait_until="networkidle")
        pg.fill("#email", EMAIL)
        pg.fill("#password", "WrongPassword456!")
        pg.locator("button[type='submit']").filter(has_text="Sign in").click()
        pg.wait_for_timeout(5000)

        err = pg.evaluate("""() => {
            const els = document.querySelectorAll('p, span, div');
            for (const el of els) {
                const t = el.textContent.trim();
                if (t.includes('Incorrect') || t.includes('incorrect')) return t;
            }
            return null;
        }""")
        assert err is not None, "No error message found"
        assert "Incorrect email or password" in err, f"Wrong error: {err}"
        print(f"  Error shown: '{err}'")
        ctx.close()
    run_scenario(3, "Wrong password -> error shown", t3)

    # ---- 4: Refresh ----
    def t4():
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.goto(f"{FRONT}/login", wait_until="networkidle")
        pg.fill("#email", EMAIL)
        pg.fill("#password", PASS)
        pg.locator("button[type='submit']").filter(has_text="Sign in").click()
        pg.wait_for_timeout(5000)
        pre = pg.url
        print(f"  Pre-refresh: {pre}")
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(5000)
        post = pg.url
        print(f"  Post-refresh: {post}")
        assert "/login" not in post, f"Redirected to login: {post}"
        st = json.loads(pg.evaluate("localStorage.getItem('lf_auth_v1')") or "{}")
        ia = st.get("state", {}).get("isAuthenticated", False)
        assert ia is True, "Not authenticated after refresh"
        print(f"  isAuthenticated=True")
        ctx.close()
    run_scenario(4, "Refresh -> stays, no redirect", t4)

    # ---- 5: Clear tokens -> redirect ----
    def t5():
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.goto(f"{FRONT}/login", wait_until="networkidle")
        pg.fill("#email", EMAIL)
        pg.fill("#password", PASS)
        pg.locator("button[type='submit']").filter(has_text="Sign in").click()
        pg.wait_for_timeout(3000)
        pg.evaluate("""() => {
            localStorage.removeItem('lf_access_token');
            localStorage.removeItem('lf_refresh_token');
            localStorage.removeItem('lf_auth_v1');
        }""")
        print(f"  localStorage cleared")
        pg.goto(f"{FRONT}/dashboard", wait_until="networkidle")
        pg.wait_for_timeout(3000)
        url = pg.url
        assert "/login" in url, f"Expected /login, got {url}"
        print(f"  /dashboard -> {url}")
        ctx.close()
    run_scenario(5, "Clear tokens -> /login redirect", t5)

    # ---- 6: Logout ----
    def t6():
        ctx = browser.new_context()
        pg = ctx.new_page()
        pg.goto(f"{FRONT}/login", wait_until="networkidle")
        pg.fill("#email", EMAIL)
        pg.fill("#password", PASS)
        pg.locator("button[type='submit']").filter(has_text="Sign in").click()
        pg.wait_for_timeout(5000)

        # Click avatar button
        av = pg.locator("button").filter(has=pg.locator("div.rounded-full"))
        assert av.count() > 0, "Avatar button not found"
        av.click()
        pg.wait_for_timeout(500)

        # Click Sign out
        so = pg.get_by_role("button", name="Sign out")
        assert so.count() > 0, "Sign out button not found"
        so.click()
        pg.wait_for_timeout(5000)

        acc = pg.evaluate("localStorage.getItem('lf_access_token')")
        ref = pg.evaluate("localStorage.getItem('lf_refresh_token')")
        assert acc is None, "access_token not cleared"
        assert ref is None, "refresh_token not cleared"
        print(f"  Tokens cleared")

        st = json.loads(pg.evaluate("localStorage.getItem('lf_auth_v1')") or "{}")
        ia = st.get("state", {}).get("isAuthenticated", False)
        assert ia is False, "Still authenticated"
        print(f"  isAuthenticated=False")

        pg.goto(f"{FRONT}/dashboard", wait_until="networkidle")
        pg.wait_for_timeout(3000)
        url = pg.url
        assert "/login" in url, f"Expected /login, got {url}"
        print(f"  /dashboard -> {url}")
        ctx.close()
    run_scenario(6, "Logout -> /logout, cleared, blocked", t6)

    browser.close()

# Summary
print(f"\n{'='*60}")
passed = sum(1 for _,_,s,_ in results if s == "PASS")
failed = sum(1 for _,_,s,_ in results if s == "FAIL")
for n, desc, status, detail in results:
    detail_str = f" ({detail})" if detail else ""
    print(f"  [{status}] Scenario {n}: {desc}{detail_str}")
print(f"\n  TOTAL: {passed} PASS / {failed} FAIL / {len(results)} total")
if failed:
    print("  => Phase 6.2 NOT complete - failures above need investigation")
else:
    print("  => Phase 6.2 COMPLETE - Auth API wiring verified end-to-end")

for p in procs:
    p.terminate(); p.wait(timeout=5)
sys.exit(failed)
